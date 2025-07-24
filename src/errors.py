import sys
import re

class BaseError:
	def __init__(self, tk, index, line, col, source, msg):
		self.tk = tk
		self.index = index
		self.line = line
		self.col = col
		self.source = source

		self.print_error(msg)
		sys.exit(-1)

	def getline(self):
		lines = self.source.split('\n')
		if self.line >= len(lines):
			return ""
		return lines[self.line]

	def replace_keyword(self, match):
		key = match.group(1)
		return {
			"src": self.getline(),
			"col": str(self.col),
			"line": str(self.line),
			"tk.v": str(getattr(self.tk, 'v', self.tk)),
			"tk.n": str(getattr(self.tk, 'n', '?')),
			"tk": str(self.tk),
		}.get(key, "%" + key + "%")

	def print_error(self, msg):
		formatted = re.sub(r'%([^%]+)%', self.replace_keyword, msg)
		
		print(formatted)
		if self.source:
			print(f"    --> Line {self.line}, Column {self.col}")
		if self.__class__.__name__ != "InterpreterError":
			src_line = self.getline()
			print(f"     {src_line}")
			print(f"     {' ' * (self.col-1)}^")

class SyntaxError(BaseError):
	def __init__(self, tk, msg):
		super().__init__(tk, *tk.position.getall(), msg)

class LexerError(BaseError):
	def __init__(self, ctk, position, msg):
		super().__init__(ctk, *position.getall(), msg)

class InterpreterError(BaseError):
	def __init__(self, ast, msg):
		if hasattr(ast, 'position'):
			super().__init__(ast, *ast.position.getall(), msg)
		else:
			super().__init__(ast, 0,0,0, '', msg)
