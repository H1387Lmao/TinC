import inspect
import errors

class ReturnException(Exception):
	def __init__(self, value=None):
		self.value = value

class Function:
	def __init__(self, name, args):
		self.name = name
		self.args = args

class CustomFunction:
	def __init__(self, params, stmts):
		self.params = params  # List of strings (parameter names)
		self.stmts = stmts  # AST(Scope) node

	def _call(self, interpreter, *arguments_values):
		function_scope = {}
		interpreter.scopes.append(function_scope)

		# Bind arguments to parameters by position
		for i, param_name in enumerate(self.params):
			if i < len(arguments_values):
				function_scope[param_name] = arguments_values[i]
			else:
				function_scope[param_name] = None  # Assign None if no argument provided

		return_value = None
		try:
			interpreter.execute_stmts(self.stmts.stmts)
		except ReturnException as e:
			return_value = e.value
		finally:
			interpreter.scopes.pop()  # Always pop the scope
		
		return return_value
	def __repr__(self):
		return "<Function>"

class Table:
	def __init__(self, elements=None):
		# Use a dict for elements, and handle the mutable default argument
		self.elements = elements if elements is not None else {}

	def __setitem__(self, item, value):
		self.elements[item] = value
	def __getitem__(self, item):
		return self.elements.get(item)

	def __getattr__(self, value):
		return self.elements.get(value, None)
	def __hasattr__(self, value):
		return value in self.elements
	
	def __repr__(self):
		a = "["
		items = []
		# Separate integer and string keys for clean representation
		numeric_keys = sorted([k for k in self.elements.keys() if isinstance(k, int)])
		other_keys = sorted([k for k in self.elements.keys() if not isinstance(k, int)])

		for k in numeric_keys:
			items.append(repr(self.elements[k]))
		for k in other_keys:
			items.append(f"{repr(k)}: {repr(self.elements[k])}")
		
		a += ", ".join(items)
		a += "]"
		return a

# --- Mathematical and Logical Operations ---
class MathEval:
	_numeric = ((int, int),)
	_string_numeric = ((str, str), (str, int), (int, str))
	_float = ((float, float), (int, float), (float, int))

	pairs = {
		"add": _numeric + _string_numeric + _float,
		"sub": _numeric + _float,
		"mul": _numeric + _string_numeric + _float,
		"div": _numeric + _float,
		"eq":  _numeric + _string_numeric + _float,
		"ne":  _numeric + _string_numeric + _float,
		"me":  _numeric + _float,  # More or equal (>=)
		"le":  _numeric + _float ,  # Less or equal (<=)
		"ls":  _numeric + _float,  # Less than (<)
		"mr":  _numeric + _float,  # More than (>)
	}

	@staticmethod
	def eval(interpreter, stmt_ast, op, a, b):
		# Handle custom class methods if they exist
		if isinstance(a, Table) and hasattr(a, "$"+op) and isinstance(getattr(a, "$"+op), CustomFunction):
			if hasattr(a, "$class"):
				return getattr(a, "$"+op)._call(interpreter, a,b)
			return getattr(a, "$"+op)._call(interpreter,b)	

		for pair_type_a, pair_type_b in MathEval.pairs[op]:
			if isinstance(a, pair_type_a) and isinstance(b, pair_type_b):
				if op == "div":
					if b == 0:
						errors.InterpreterError(stmt_ast, "Runtime Error: Division by zero.")
					return a / b
				elif op == "mul":
					return a * b
				elif op == "add":
					return a + b
				elif op == "sub":
					return a - b
				elif op == "eq":
					return a == b
				elif op == "ne":
					return a != b
				elif op == "me":
					return a >= b
				elif op == "le":
					return a <= b
				elif op == "ls":
					return a < b
				elif op == "mr":
					return a > b
		
		errors.InterpreterError(stmt_ast, f"Operation Error: Unable to apply operation '{op}' to types {type(a).__name__} and {type(b).__name__}.")
