import errors
import math
from parser import *
from stdlibrary import *

class CustomClass:
	pass

class CustomFunction:
	def __init__(self, name, params, stmts):
		self.name = name
		self.params = params
		self.stmts = stmts
	def _call(self, interpreter, *arguments):
		args = {}
		for i in self.params:
			if len(arguments) <= i:
				args[i] = None
			else:
				args[i] = arguments[i]
		interpreter.scopes.append({})
		function_scope = interpreter.get_scope()
		function_scope['return_value'] = None
		for arg_name, arg_value in args:
			function_scope[arg_name] = arg_value
		interpreter.execute_stmts(self.stmts.stmts)
		return interpreter.scopes.pop()['return_value']

		

class MathEval:
	_numeric = ((int, int),)
	_string_numeric = ((str, str), (int, int))
	_string_int = ((str, int),(int, str))

	pairs = {
		"add": _string_numeric,
		"sub": _numeric,
		"mul": _numeric + _string_int,
		"div": _numeric,
		"eq":  _numeric,
		"ne":  _numeric,
		"me":  _numeric,
		"le":  _numeric,
		"ls":  _numeric,
		"mr":  _numeric,
	}
	@staticmethod
	def eval(stmt, op, a, b):
		for pair in MathEval.pairs[op]:
			if isinstance(a, CustomClass):
				getattr(a, op)(b)
			elif isinstance(a, pair[0]) and isinstance(b, pair[1]):
				if op == "div":
					return a/b if a != 0 and b != 0 else 0
				elif op == "mul":
					return a*b
				elif op == "add":
					return a+b
				elif op == "sub":
					return a-b
				elif op == "eq":
					return a==b
				elif op == "me":
					return a>=b
				elif op == "le":
					return a<=b
				elif op == "ls":
					return a<b
				elif op == "mr":
					return a>b
				elif op == "ne":
					return a!=b
		else:
			errors.InterpreterError(stmt, f"Operation Error: Unable to apply operation {op} to type {str(type(a))} and {str(type(b))}")
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
	def execute_scope(self, scope):
		self.scopes.append({})
		self.execute_stmts(scope.stmts)
		self.scopes.pop()
	def get_scope(self):
		return self.scopes[-1]
	def get_variable(self, v):
		scope = self.get_scope()
		if v not in scope:
			if v not in self.globalVariables:
				return None, None
			else:
				return self.globalVariables, self.globalVariables[v]
		else:
			return scope, scope[v]
	def execute_stmt(self, stmt):
		if stmt.type == "Assign":
			scope, var = self.get_variable(stmt.target)
			if scope is not None:
				errors.InterpreterError(stmt, "Definition Error: Variable already used, if intended remove let.")
			else:
				self.get_scope()[stmt.target] = self.execute_value(stmt.value)
		elif stmt.type == "Reassign":
			scope, res = self.get_variable(stmt.target)
			if res is None:
				errors.InterpreterError(stmt, "Redefinition Error: Variable reassigned before assignment.")
			scope[stmt.target] = self.execute_value(stmt.value)
		elif stmt.type == "If":
			if self.execute_value(stmt.condition):
				self.execute_scope(stmt.stmts)
		elif stmt.type == "While":
			while self.execute_value(stmt.condition):
				self.execute_scope(stmt.stmts)
		elif stmt.type == "FunctionCall":
			return self.execute_value(stmt)
		elif stmt.type == "SetAttribute":
			if stmt.target.type != "GetAttribute":
				errors.InterpreterError(0, "Runtime Error: Expected attribute for SetAttribute")

			# Walk to the second-to-last parent
			ptr = stmt.target
			stack = []

			while hasattr(ptr, "type") and ptr.type == "GetAttribute":
				stack.append(ptr)
				ptr = ptr.parent

			# Execute from left to right to build the actual parent chain
			obj = self.execute_value(ptr)  # Base object (e.g., Variable("a"))

			for link in reversed(stack[:-1]):
				key = self.execute_value(link.target)
				obj = obj[key]

			# Now set the final attribute
			final_key = self.execute_value(stack[-1].target)
			obj[final_key] = self.execute_value(stmt.value)
		elif stmt.type == "For":
			var_name = stmt.condition.left
			self.scopes.append({})
			right = self.execute_value(stmt.condition.right)
			for v in right:
				if v in right:
					v = right[v]
				self.get_scope()[var_name] = v
				self.execute_stmts(stmt.stmts.stmts)
			self.scopes.pop()
		elif stmt.type == "FunctionDeclare":
			scope = self.get_scope()
			scope[stmt.name] = CustomFunction(name=stmt.name, params=stmt.arguments, stmts=stmt.stmts)

	def execute_value(self, stmt):
		if isinstance(stmt,AST):
			if stmt.type == "Unary":
				if stmt.operation == "!":
					return ~(self.execute_value(stmt.value))
				if stmt.operation == "-":
					return -(self.execute_value(stmt.value))
				if stmt.operation == "+":
					return math.abs(self.execute_value(stmt.value))
			elif stmt.type == "Binop":
				left = self.execute_value(stmt.left)
				right = self.execute_value(stmt.right)
				op = stmt.op.v

				method = None
				if   op == "+" :method = "add"
				elif op == "-" :method = "sub"
				elif op == "/" :method = "div"
				elif op == "*" :method = "mul"
				elif op == "==":method = "eq"
				elif op == "!=":method = "ne"
				elif op == "<" :method = "mr"
				elif op == ">" :method = "ls"
				elif op == ">=":method = "me"
				elif op == "<=":method = "le"

				if method:
					return self.math.eval(stmt, method, left, right)
			elif stmt.type == "FunctionCall":
				if stmt.name in stdlibrary:
					return stdlibrary[stmt.name](*map(self.execute_value, stmt.args))._call()
				scope, res = self.get_variable(stmt.name)
				if res is None: errors.InterpreterError(0, f"Variable Error: Function {stmt.name} is not defined")
				if not isinstance(res, CustomFunction): errors.InterpreterError(0, f"Variable Error: Variable {stmt.name} is not a function")
				return res._call(self,*stmt.args)
			elif stmt.type == "String":
				formatted = ""
				backslash=False
				for char in stmt.value:
					if char == "\\":
						if backslash:
							formatted+="\\"
							backslash = False
						else:
							backslash = True
					elif backslash:
						if char not in "nt":
							errors.InterpreterError(stmt, f"Invalid escape sequence: '\\{char}'")
						else:
							if char == "n":
								formatted += "\n"
							elif char == "t":
								formatted += "\t"
						backslash = False
					else:
						formatted += char
				return formatted
			elif stmt.type == "List":
				keys = list(map(self.execute_value, stmt.value))
				res = {}
				for key in keys:
					res[len(res)] = key
				return res
			elif stmt.type == "GetAttribute":
				parent = self.execute_value(stmt.parent)
				child = self.execute_value(stmt.target)

				return parent[child]
			else:
				errors.InterpreterError(stmt, f"Not Implemented: {stmt.type}")
		else:
			if isinstance(stmt, str):
				scope, res = self.get_variable(stmt)
				if res is None: errors.InterpreterError(0, f"Variable Error: Variable {stmt} is not defined")
				return res
			return stmt
