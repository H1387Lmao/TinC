import errors
import math
from parser import *
from eval import *
import sys
import types

def get_main_module_local_variables(module):
	local_variables = {}

	dict = inspect.getmembers(module)
	for name, value in dict:
		if name.startswith('__'):
			continue
		if isinstance(value, types.ModuleType):
			continue
		if hasattr(value, '__module__') and value.__module__ != module.__name__:
			continue
		local_variables[name] = value

	return local_variables

# --- The Interpreter Core ---
class Interpreter:
	def __init__(self):
		self.globalVariables = {}
		self.scopes = [self.globalVariables]
		self.math = MathEval
	
	def execute_prog(self, ast):
		self.execute_stmts(ast.stmts)
	
	def execute_stmts(self, stmts):
		for stmt in stmts:
			self.execute_stmt(stmt)
	
	def execute_scope(self, scope_node):
		self.scopes.append({})
		self.execute_stmts(scope_node.stmts)
		self.scopes.pop()
	
	def get_scope(self):
		return self.scopes[-1]
	
	def get_variable(self, var_name):
		# Search from the current scope outward to the global scope
		for scope in reversed(self.scopes):
			if var_name in scope:
				return scope, scope[var_name]
		return None, None
	
	# --- Main Execution Functions ---
	def execute_stmt(self, stmt):
		if stmt.type == "Assign":
			# 'let' assignment; check that variable doesn't exist
			scope_found, _ = self.get_variable(stmt.target)
			if scope_found is not None:
				errors.InterpreterError(stmt, f"Definition Error: Variable '{stmt.target}' already defined. Use re-assignment (e.g., '{stmt.target} = ...') instead of 'let'.")
			else:
				self.get_scope()[stmt.target] = self.execute_value(stmt.value)
		
		elif stmt.type == "Reassign":
			# Re-assignment; target must be a simple variable name
			scope_found, _ = self.get_variable(stmt.target)
			if scope_found is None:
				errors.InterpreterError(stmt, f"Redefinition Error: Variable '{stmt.target}' reassigned before 'let' assignment.")
			scope_found[stmt.target] = self.execute_value(stmt.value)
		
		elif stmt.type == "SetAttribute":
			if stmt.target.type != "GetAttribute":
				errors.InterpreterError(stmt, "Runtime Error: Expected attribute for SetAttribute operation.")
			self.set_attribute_value(stmt.target, stmt.value)
		elif stmt.type == "Use":
			module = __import__(stmt.target)
			variables = get_main_module_local_variables(module)

			for n, variable in variables.items():
				self.globalVariables[n] = variable
		elif stmt.type == "If":
			if self.execute_value(stmt.condition):
				self.execute_scope(stmt.stmts)
		
		elif stmt.type == "While":
			while self.execute_value(stmt.condition):
				self.execute_scope(stmt.stmts)
		
		elif stmt.type == "For":
			var_name = stmt.condition.left
			iterable_value = self.execute_value(stmt.condition.right)

			if not isinstance(iterable_value, (range, Table)):
				errors.InterpreterError(stmt, f"Runtime Error: 'for' loop iterable must be a range or a list/table, not {type(iterable_value).__name__}.")

			self.scopes.append({})  # New scope for the loop
			loop_scope = self.get_scope()
			
			if isinstance(iterable_value, range):
				for val in iterable_value:
					loop_scope[var_name] = val
					self.execute_stmts(stmt.stmts.stmts)
			elif isinstance(iterable_value, Table):
				for val in iterable_value.elements.values():
					loop_scope[var_name] = val
					self.execute_stmts(stmt.stmts.stmts)
			
			self.scopes.pop()
		
		elif stmt.type == "FunctionDeclare":
			func_name = stmt.name
			if isinstance(func_name, AST) and func_name.type == "FunctionCall":
				func_name = stmt.name.name
			func_obj = CustomFunction(params=stmt.arguments, stmts=stmt.stmts)
			
			if isinstance(func_name, AST) and func_name.type == "GetAttribute":
				parent_obj, method_name = self.resolve_attribute_chain(func_name)
				if isinstance(parent_obj, Table):
					parent_obj.elements[method_name] = func_obj
				else:
					errors.InterpreterError(stmt, f"Runtime Error: Cannot declare method on object of type '{type(parent_obj).__name__}'.")
			else:
				self.get_scope()[func_name] = func_obj
		
		elif stmt.type == "Return":
			raise ReturnException(self.execute_value(stmt.value))
		
		elif stmt.type == "Expression":
			self.execute_value(stmt.value)  # Evaluate, but ignore the return value

	def execute_value(self, ast_node):
		if not isinstance(ast_node, AST):
			if isinstance(ast_node, str):
					scope, res = self.get_variable(ast_node)
					if res is None: errors.InterpreterError(ast_node, f"Variable Error: Variable '{ast_node}' is not defined.")
					return res
			return ast_node
		
		if ast_node.type == "Unary":
			op_val = self.execute_value(ast_node.value)
			if ast_node.operation == "!":
				return ~op_val
			elif ast_node.operation == "-":
				return -op_val
			elif ast_node.operation == "+":
				return abs(op_val)
		
		elif ast_node.type == "Binop":
			left = self.execute_value(ast_node.left)
			right = self.execute_value(ast_node.right)
			op = ast_node.op.v
			
			method = None
			if op == "+": method = "add"
			elif op == "-": method = "sub"
			elif op == "*": method = "mul"
			elif op == "/": method = "div"
			elif op == "==": method = "eq"
			elif op == "!=": method = "ne"
			elif op == "<": method = "ls"
			elif op == ">": method = "mr"
			elif op == ">=": method = "me"
			elif op == "<=": method = "le"
			
			if method:
				return self.math.eval(self, ast_node, method, left, right)
		
		elif ast_node.type == "FunctionCall":
			callable_target = None
			if isinstance(ast_node.name, AST):
				# If it's an attribute access (like x->hello()), resolve it
				callable_target = self.get_attribute_value(ast_node.name)
			else:
				# Otherwise, it's a simple variable name (like printf, myFunction)
				# This will now correctly find StdPrint class in globalVariables
				_, callable_target = self.get_variable(ast_node.name)

			if callable_target is None:
				errors.InterpreterError(ast_node, f"Variable Error: Function/Callable '{ast_node.name}' is not defined.")

			args_values = [self.execute_value(arg_ast) for arg_ast in ast_node.arguments]
			
			# --- MODIFICATION 2: Handle different types of callables ---
			if isinstance(callable_target, CustomFunction):
				# User-defined functions created with fn keyword
				return callable_target._call(self, *args_values)
			elif hasattr(callable_target, "_call"):
				return callable_target(*args_values)._call()
			elif callable(callable_target):
				# For any other Python native callable object (e.g., if you loaded math.sqrt directly)
				return callable_target(*args_values)
			
			# If none of the above, it's an error
			errors.InterpreterError(ast_node, f"Type Error: '{type(callable_target).__name__}' is not a callable function.")
		
		elif ast_node.type == "String":
			formatted = ""
			backslash = False
			for char in ast_node.value:
				if char == "\\":
					if backslash: formatted += "\\"; backslash = False
					else: backslash = True
				elif backslash:
					if char == "n": formatted += "\n"
					elif char == "t": formatted += "\t"
					else: errors.InterpreterError(ast_node, f"Invalid escape sequence: '\\{char}'.")
					backslash = False
				else:
					formatted += char
			return formatted
		
		elif ast_node.type == "List":
			elements_dict = {i: self.execute_value(item) for i, item in enumerate(ast_node.value)}
			return Table(elements_dict)
		
		elif ast_node.type == "GetAttribute":
			return self.get_attribute_value(ast_node)
		
		elif ast_node.type == "Range":
			start = self.execute_value(ast_node.start)
			end = self.execute_value(ast_node.end)
			if not isinstance(start, int) or not isinstance(end, int):
				errors.InterpreterError(ast_node, f"Type Error: Range operands must be integers, got {type(start).__name__} and {type(end).__name__}.")
			return range(start, end + 1)
		
		errors.InterpreterError(ast_node, f"Not Implemented (execute_value): {ast_node.type}")

	# --- Helper Functions for Attribute Access ---
	def resolve_attribute_chain(self, get_attribute_ast):
		if get_attribute_ast.type != "GetAttribute":
			errors.InterpreterError(get_attribute_ast, "Internal Error: Expected GetAttribute AST.")
		
		base_object = self.execute_value(get_attribute_ast.parent)
		final_target_key = get_attribute_ast.target
		
		return base_object, final_target_key
		
	def get_attribute_value(self, get_attribute_ast):
		parent_obj, final_target_key = self.resolve_attribute_chain(get_attribute_ast)
		
		if isinstance(parent_obj, Table):
				# For Table objects, check if the key (integer or string) exists in its elements
				if final_target_key in parent_obj.elements:
						return parent_obj.elements[final_target_key]
				# Fallback to checking for actual Python attributes on the Table object itself (less common for user data)
				elif hasattr(parent_obj, final_target_key):
						return getattr(parent_obj, final_target_key)
				
				# If key not found in elements and not a direct Python attribute
				errors.InterpreterError(get_attribute_ast, f"AttributeError: 'Table' object has no attribute or index '{final_target_key}'.")
		
		# For other Python objects, use Python's built-in getattr
		elif hasattr(parent_obj, final_target_key):
				return getattr(parent_obj, final_target_key)
		
		# If no other case matched, it's an error
		errors.InterpreterError(get_attribute_ast, f"AttributeError: '{type(parent_obj).__name__}' object has no attribute or index '{final_target_key}'.")

	def set_attribute_value(self, get_attribute_ast, value_ast):
		parent_obj, final_target_key = self.resolve_attribute_chain(get_attribute_ast)
		resolved_value = self.execute_value(value_ast)
		
		if isinstance(parent_obj, Table):
				# For Table objects, set the element using the resolved key (integer or string)
				parent_obj.elements[final_target_key] = resolved_value
		# For other Python objects, use Python's built-in setattr
		elif hasattr(parent_obj, final_target_key):
				setattr(parent_obj, final_target_key, resolved_value)
		else:
				# If not a Table and not a direct Python attribute, it's an error
				errors.InterpreterError(get_attribute_ast, f"AttributeError: Cannot set attribute or index '{final_target_key}' on object of type '{type(parent_obj).__name__}'.")
