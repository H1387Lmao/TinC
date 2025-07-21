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
		
	def parse_factor(self):
		if self.pos.peek().t in [TokenTypes.INT, TokenTypes.STRING]:
			return self.pos.consume().v
		elif self.pos.peek().t == TokenTypes.IDENTIFIER:
			if self.pos.peek(2).t == TokenTypes.ARROW:
				return self.parse_getattr()
			return self.pos.consume().v
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
		else:
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
	def parse_stmts(self, end=TokenTypes.EOF):
		stmts=[]
		while self.pos.peek().t!=end:
			stmts.append(self.parse_stmt())
			if self.pos.peek().t==end: break
		return stmts
	def parse_prog(self):
		return AST(type="Program", stmts=self.parse_stmts())