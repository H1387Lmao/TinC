import sys
import re

class BaseError:
	def __init__(self, tk, index, ln, col, source, msg):
		self.source = source
		self.ln = ln
		self.col = col
		self.source
		self.tk = tk

		self.format_msg(msg)

		sys.exit(-1)

	def getline(self):
		return self.source.split("\n")[self.ln]
	def replace_keyword(self, match):
		keyword = match.group(1)
		if keyword == "src":
			return self.getline()
		elif keyword == "col":
			return self.col
		elif keyword == "line":
			return self.ln
		elif keyword == "tk.v":
			return str(self.tk.v)
		elif keyword == "tk.n":
			return str(self.tk_n)
		elif keyword == "tk":
			return str(self.tk)
		return "%"+keyword+"%"
	def format_msg(self, msg):
		fmsg = re.sub(r'%([^%]+)%', self.replace_keyword, msg)
		print(fmsg)

class SyntaxError(BaseError):
	def __init__(self, tk, msg):
		super().__init__(
			tk,
			*tk.position.getall(),
			msg
		)

class LexerError(BaseError):
	def __init__(self, ctk, position, msg):
		super().__init__(
			ctk,
			*position.getall(),
			msg
		)