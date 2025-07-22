from token import *
from position import *
import errors

class AST:
	def __init__(self, **kwargs):
		self.kwargs = kwargs
		for k, v in kwargs.items():
			setattr(self, k, v)

	def repr(self, indent="  ", level=0):
		start = f"AST({self.type}){{"
		mid_lines = []
		for k, v in self.kwargs.items():
			if k =="type": continue
			line_prefix = f"{indent * (level + 1)}{k} = "
			if isinstance(v, AST):
				mid_lines.append(f"{line_prefix}{v.repr(indent, level + 1)},")
			elif isinstance(v, (list, tuple)):
				lines = [f"{line_prefix}["]
				for item in v:
					if isinstance(item, (AST, Token)):
						lines.append(f"{indent * (level + 2)}{item.repr(indent, level + 2)},")
					else:
						lines.append(f"{indent * (level + 2)}{repr(item)},")
				lines.append(f"{indent * (level + 1)}],")
				mid_lines.extend(lines)
			else:
				mid_lines.append(f"{line_prefix}{repr(v)},")
		end = f"{indent * level}}}"
		return "\n".join([start] + mid_lines + [end])

	def __repr__(self):
		return self.repr()


class Parser:
	def __init__(self, tokens):
		self.pos = ParserPosition(tokens)
	def binop(self, func, ops):
		left = func()
		while self.pos.peek().v in ops:
			op = self.pos.consume()
			right = func()
			left = AST(type="Binop",left=left, right=right, op=op)
		return left
	def parse_getattr(self):
		parent = self.pos.consume().v
		self.pos.consume()
		child = self.parse_factor()
		return AST(type="GetAttribute", parent=parent, target=child)

	def parse_getattr_chain(self):
		node = self.parse_factor()
		while self.pos.peek().v == "->":
			self.pos.consume()  # consume '->'
			attr = self.pos.expect(TokenTypes.IDENTIFIER)
			node = AST(type="GetAttribute", parent=node, target=attr.v)
		return node
	
	def parse_scope(self):
		self.pos.expect("{")
		stmts = self.parse_stmts(f"}}") # Fix for Lite XL Python SyntaxHighlighting
		return AST(type="Scope", stmts=stmts)

	def parse_condition(self):
		self.pos.expect("(")

		res=self.binop(self.parse_expr, ["==",">=","<=", "<", ">", "!="])

		self.pos.expect(")")

		return res
	def parse_for_condition(self):
		self.pos.expect("(")

		res=self.binop(self.parse_expr, ['?in'])

		self.pos.expect(")")

		return res

	def parse_list(self, end):
		ls = []

		while self.pos.peek().v != end:
			ls.append(self.parse_expr())
			if self.pos.peek().v == end:
				break
			self.pos.expect(",")
		self.pos.expect(end)

		return ls

	def parse_fc(self, need_expect=True):
		name = self.pos.consume().v
		self.pos.expect('(')
		args = self.parse_list(")")
		_ = self.pos.expect(';') if need_expect else None
		return AST(type="FunctionCall", name=name,args=args)

	def parse_factor(self):
		if self.pos.peek() is None:
			errors.SyntaxError(self.pos.peek(-1), f"Syntax Error: Recieved EOF before factor")
		if self.pos.peek().t == TokenTypes.INT:
			if self.pos.peek(2).v == "..":
				if self.pos.peek(3).t == TokenTypes.INT:
					res = range(self.pos.consume().v, self.pos.peek(2).v+1)
					self.pos.consume()
					self.pos.consume()
					return res
				else:
					errors.SyntaxError(self.pos.peek(-1), f"Syntax Error: Expected 'integer' after '..")
			return self.pos.consume().v
		elif self.pos.peek().t == TokenTypes.STRING:
			return AST(type="String", value=self.pos.consume().v)
		elif self.pos.peek().t == TokenTypes.IDENTIFIER:
			if self.pos.peek(2).t == TokenTypes.ARROW:
				return self.parse_getattr()
			elif self.pos.peek(2).v == "(":
				return self.parse_fc(need_expect=False)
			return self.pos.consume().v
		elif self.pos.peek().v == "[":
			self.pos.expect('[')
			return AST(type="List", value=self.parse_list("]"))
		elif self.pos.peek().v == '(':
			self.pos.consume()
			res = self.parse_expr()
			self.pos.expect(")")
			return res
		elif self.pos.peek().v in "-!+":
			op=self.pos.consume()
			return AST(type="Unary", operation=op.v,value=self.parse_factor())
		else:
			errors.SyntaxError(self.pos.peek(), f"Syntax Error: Expected value, got '{self.pos.peek().v}'")
			
	def parse_term(self):
		return self.binop(self.parse_factor, ['*','/'])
	def parse_expr(self):
		return self.binop(self.parse_term, ['+','-'])
	def parse_stmt(self):
		if self.pos.peek().v == "?let":
			self.pos.consume()
			name = self.pos.consume().v
			if self.pos.peek().v == ";":
				self.pos.expect(';')
				return AST(type="Assign", target=name, value=None)
			self.pos.consume()
			value = self.parse_expr()
			self.pos.expect(';')
			return AST(type="Assign", target=name, value=value)
		elif self.pos.peek().v == "?if":
			self.pos.consume()
			condition = self.parse_condition()
			scope = self.parse_scope()

			return AST(type="If", condition=condition, stmts=scope)
		elif self.pos.peek().v == "?while":
			self.pos.consume()
			condition = self.parse_condition()
			scope = self.parse_scope()

			return AST(type="While", condition=condition, stmts=scope)
		elif self.pos.peek().v == "?for":
			self.pos.consume()
			condition = self.parse_for_condition()
			scope = self.parse_scope()

			return AST(type="For", condition=condition, stmts=scope)
		elif self.pos.peek().v == "?fn":
			self.pos.consume()
			name = self.pos.consume().v
			self.pos.expect("(")
			arguments = self.parse_list(")")

			scope = self.parse_scope()

			return AST(type="FunctionDeclare", name=name, arguments=arguments, stmts=scope)
		elif self.pos.peek().v == "?return":
			self.pos.consume()
			res= AST(type="Return", value=self.parse_expr())
			self.pos.expect(";")
			return res
		elif self.pos.peek().t == TokenTypes.IDENTIFIER:
			if self.pos.peek(2).v == "(":
				return self.parse_fc()
			if not self.pos.peek(2).v == "=":
				target = self.parse_getattr_chain()
				if self.pos.peek().v == "=":
					self.pos.consume()  # consume '='
					value = self.parse_expr()
					self.pos.expect(';')
					return AST(type="SetAttribute", target=target, value=value)

				errors.SyntaxError(self.pos.peek(), f"Syntax Error: Expected statement, got 'identifier'")
		planb = self.pos.peek()
		target = self.parse_factor()
		if isinstance(target, AST):
			self.pos.consume()
			value = self.parse_expr()
			self.pos.expect(';')
		else:
			if isinstance(target, int):
				errors.SyntaxError(self.pos.peek(), f"Syntax Error: Expected identifier, got 'integer'")
			if planb.t != TokenTypes.IDENTIFIER:
				errors.SyntaxError(self.pos.peek(), f"Syntax Error: Expected identifier, got 'string'")
			self.pos.expect("=")
			value = self.parse_expr()
			self.pos.expect(';')
		return AST(type="Reassign", target=target, value=value)
	def parse_stmts(self, end="EOF"):
		stmts=[]
		while self.pos.peek().v!=end:
			stmts.append(self.parse_stmt())
			if self.pos.peek().t==end: break
		self.pos.expect(end)
		return stmts
	def parse_prog(self):
		return AST(type="Program", stmts=self.parse_stmts())
