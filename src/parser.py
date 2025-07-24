from tokens import *
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
		while self.pos.peek() and self.pos.peek().v in ops:
			op = self.pos.consume()
			right = func()
			left = AST(type="Binop",left=left, right=right, op=op)
		return left
	
	def parse_scope(self):
		self.pos.expect("{")
		stmts = self.parse_stmts(f"}}")
		self.pos.expect(f"}}")
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
			if self.pos.peek().v == ",":
				self.pos.expect(",")
			else:
				errors.SyntaxError(self.pos.peek(), f"Syntax Error: Expected ',' or '{end}', got '{self.pos.peek().v}'")
		self.pos.expect(end)
		return ls

	def parse_identifier_or_attribute_chain(self):
		node = self.parse_atom() # Start with an atom (should be an identifier here)

		# Check for attribute access (e.g., 'x->hello')
		while self.pos.peek() and self.pos.peek().v == "->":
			self.pos.consume() # Consume '->'
			if not self.pos.peek() or self.pos.peek().t != TokenTypes.IDENTIFIER:
				errors.SyntaxError(self.pos.peek(), "Syntax Error: Expected identifier after '->' in attribute chain.")
			attr_token = self.pos.consume()
			node = AST(type="GetAttribute", parent=node, target=attr_token.v) # Store attribute as its string value

		return node

	def parse_atom(self):
		if self.pos.peek() is None:
			errors.SyntaxError(self.pos.peek(-1), f"Syntax Error: Received EOF before factor")
		
		if self.pos.peek().t == TokenTypes.INT:
			start_val = self.pos.consume().v
			if self.pos.peek() and self.pos.peek().v == "..":
				self.pos.consume()
				if self.pos.peek().t == TokenTypes.INT:
					end_val = self.pos.consume().v
					return AST(type="Range", start=start_val, end=end_val)
				else:
					errors.SyntaxError(self.pos.peek(-1), f"Syntax Error: Expected integer after '..'")
			return start_val
		
		elif self.pos.peek().t == TokenTypes.STRING:
			return AST(type="String", value=self.pos.consume().v)
		
		elif self.pos.peek().v == '(':
			self.pos.consume()
			res = self.parse_expr()
			self.pos.expect(")")
			return res
		
		elif self.pos.peek().v == "[":
			self.pos.expect('[')
			return AST(type="List", value=self.parse_list("]"))

		elif self.pos.peek().v in "-!+":
			op = self.pos.consume()
			return AST(type="Unary", operation=op.v, value=self.parse_atom())
		
		elif self.pos.peek().t == TokenTypes.IDENTIFIER:
			return self.pos.consume().v
		
		else:
			errors.SyntaxError(self.pos.peek(), f"Syntax Error: Expected value, got '{self.pos.peek().v}'")
	
	def parse_callable_or_attribute_access_target(self):
		node = self.parse_atom() 

		while True:
			if self.pos.peek() and self.pos.peek().v == "->":
				self.pos.consume()
				if not self.pos.peek() or self.pos.peek().t != TokenTypes.IDENTIFIER:
					errors.SyntaxError(self.pos.peek(), f"Syntax Error: Expected identifier after '->'")
				attr = self.pos.consume().v
				node = AST(type="GetAttribute", parent=node, target=attr)
			elif self.pos.peek() and self.pos.peek().v == "(":
				self.pos.consume()
				arguments = self.parse_list(")")
				node = AST(type="FunctionCall", name=node, arguments=arguments)
			else:
				break
		return node

	def parse_factor(self):
		return self.parse_callable_or_attribute_access_target()
			
	def parse_term(self):
		return self.binop(self.parse_factor, ['*','/'])

	def parse_expr(self):
		return self.binop(self.parse_term, ['+','-'])

	def parse_stmt(self):
		# Handle 'let' statements
		if self.pos.peek().v == "?let":
			self.pos.consume()
			target = self.parse_callable_or_attribute_access_target()
			
			if self.pos.peek().v == "=":
				self.pos.consume()
				value = self.parse_expr()
				self.pos.expect(';')
				return AST(type="Assign", target=target, value=value)
			elif self.pos.peek().v == ";":
				self.pos.expect(';')
				return AST(type="Assign", target=target, value=None)
			else:
				errors.SyntaxError(self.pos.peek(), f"Syntax Error: Expected '=' or ';' after 'let' declaration")
		elif self.pos.peek().v == "?use":
			self.pos.consume()
			target = self.pos.consume()
			if target.t != TokenTypes.IDENTIFIER:
				errors.SyntaxError(self.pos.peek(), f"Syntax Error: Expected 'identifier' after 'use'")
			self.pos.expect(";")
			return AST(type="Use", target=target.v)
		# Handle 'if' statements
		elif self.pos.peek().v == "?if":
			self.pos.consume()
			condition = self.parse_condition()
			scope = self.parse_scope()
			return AST(type="If", condition=condition, stmts=scope)
		
		# Handle 'while' statements
		elif self.pos.peek().v == "?while":
			self.pos.consume()
			condition = self.parse_condition()
			scope = self.parse_scope()
			return AST(type="While", condition=condition, stmts=scope)
		
		# Handle 'for' statements
		elif self.pos.peek().v == "?for":
			self.pos.consume()
			condition = self.parse_for_condition()
			scope = self.parse_scope()
			return AST(type="For", condition=condition, stmts=scope)
		
		# Handle 'return' statements
		elif self.pos.peek().v == "?return":
			self.pos.consume()
			res= AST(type="Return", value=self.parse_expr())
			self.pos.expect(";")
			return res
		
		# NEW: Handle Function Declaration as a top-level statement
		elif self.pos.peek().v == "?fn":
			self.pos.consume() # Consume "?fn"
			name_node = self.parse_identifier_or_attribute_chain() 
			if self.pos.peek() and self.pos.peek().v == "(":
				self.pos.consume() # Consume '('
				arguments = self.parse_list(")") 

			scope_stmts = self.parse_scope()
			return AST(type="FunctionDeclare", name=name_node, arguments=arguments, stmts=scope_stmts)


		# Handle assignments, expressions, and function calls that start with an identifier
		elif self.pos.peek().t == TokenTypes.IDENTIFIER:
			left_hand_side = self.parse_callable_or_attribute_access_target() 

			if self.pos.peek() and self.pos.peek().v == "=":
				self.pos.consume()
				value = self.parse_expr()
				self.pos.expect(';')
				if isinstance(left_hand_side, AST) and left_hand_side.type == "GetAttribute":
					return AST(type="SetAttribute", target=left_hand_side, value=value)
				elif isinstance(left_hand_side, str):
					return AST(type="Reassign", target=left_hand_side, value=value)
				else:
					errors.SyntaxError(self.pos.peek(), f"Syntax Error: Invalid target for assignment: {left_hand_side}")
			else:
				self.pos.expect(';') # Expect semicolon to terminate expression statement
				return AST(type="Expression", value=left_hand_side)
		
		else: # If none of the above, it must be a general expression statement (e.g., `10;` or `a + b;`)
			expr = self.parse_expr()
			self.pos.expect(';')
			return AST(type="Expression", value=expr)
			
	def parse_stmts(self, end="EOF"):
		stmts=[]
		while self.pos.peek() and self.pos.peek().v != end:
			stmts.append(self.parse_stmt())
		return stmts

	def parse_prog(self):
		stmts = self.parse_stmts("EOF") 
		if self.pos.peek() and self.pos.peek().v != "EOF":
			errors.SyntaxError(self.pos.peek(), f"Syntax Error: Expected EOF, got '{self.pos.peek().v}'")
		return AST(type="Program", stmts=stmts)
