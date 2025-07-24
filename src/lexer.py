from tokens import *
from position import *
import errors
import re

KEYWORDS = ("let", "if", "while", 'for','in', 'fn', 'return', 'use')

class Lexer:
	def __init__(self, source):
		self.position = TokenPosition(source)
	def get_identif(self):
		if self.ctk:
			string_match = re.match(r'^"(.*?)"$', self.ctk) or re.match(r"^'(.*?)'$", self.ctk)
			if string_match:
				value = string_match.group(1)
				self.tokens.append(Token(TokenTypes.STRING, value, self.position.copy()))
			elif self.ctk.isdigit():
				self.tokens.append(Token(TokenTypes.INT, int(self.ctk), self.position.copy()))
			elif self.ctk in KEYWORDS:
				self.tokens.append(Token(TokenTypes.KEYWORD, "?"+self.ctk, self.position.copy()))
			else:
				regex=re.compile(r'^[\$A-Za-z_][A-Za-z0-9_]*$')
				if bool(regex.match(self.ctk)):
					self.tokens.append(Token(TokenTypes.IDENTIFIER, self.ctk, self.position.copy()))
				else:
					invalid_chars = ''.join(dict.fromkeys(c for c in self.ctk if not re.match(r'[\$A-Za-z0-9_]', c)))
					label = "Character" if len(invalid_chars) == 1 else "Characters"
					suffix = "" if len(invalid_chars) == 1 else "s"
					invalid_chars = "["+", ".join(map(repr,list(invalid_chars)))+"]" if suffix else f"'{invalid_chars}'"
					errors.LexerError(self.ctk, self.position, f"LexerError: Invalid {label} {invalid_chars}")
			self.ctk = ""
	def get_symbol(self, char):
		types = {
			"+": TokenTypes.ADD,
			"-": TokenTypes.SUB,
			"*": TokenTypes.MUL,
			"/": TokenTypes.DIV,
			"++": TokenTypes.INCREMENT,
			"--": TokenTypes.DECREMENT,
			"->": TokenTypes.ARROW,
			"||": TokenTypes.OR,
			"&&": TokenTypes.AND,
			"!": TokenTypes.NOT,
			"^": TokenTypes.XOR,
			"=": TokenTypes.EQUALS,
			";": TokenTypes.SEMI,
			"\"": TokenTypes.DQT,
			"'": TokenTypes.SQT,
			",": TokenTypes.COMMA,
			'..': TokenTypes.RANGE
		}
		if char in "+-&|.":
			if self.position.peek(2) == char:
				self.position.consume()
				self.position.consume()
				self.tokens.append(Token(types[char*2], char*2, self.position.copy()))
			else:
				self.position.consume()
				if char == "-" and self.position.peek() == ">":
					self.tokens.append(Token(types['->'], "->", self.position.copy()))
					self.position.consume()
					return
				if char in "&.":
					errors.LexerError(char, self.position, f"Unknown Symbol: '{char}'")
				self.tokens.append(Token(types[char], char, self.position.copy()))
		else:
			self.position.consume()
			if char in "()":
				self.tokens.append(Token(TokenTypes.PAREN, char, self.position.copy()))
			elif char in "{}":
				self.tokens.append(Token(TokenTypes.BRACES, char, self.position.copy()))
			elif char in "[]":
				self.tokens.append(Token(TokenTypes.BRACKETS, char, self.position.copy()))
			elif char in "<>":
				if self.position.peek() != "=":
					return self.tokens.append(Token(TokenTypes.COMPARISON, char, self.position.copy())), self.position.consume()
				self.position.consume()
				self.tokens.append(Token(TokenTypes.COMPARISON, char+"=", self.position.copy()))
			elif char == "=":
				if self.position.peek() != "=":
					return self.tokens.append(Token(TokenTypes.EQUALS, char, self.position.copy()))
				self.position.consume()
				self.tokens.append(Token(TokenTypes.EQUALS, char+"=", self.position.copy()))
			else:
				if char == "!" and self.position.peek() == "=":
					return self.tokens.append(Token(TokenTypes.COMPARISON, char+"=", self.position.copy())), self.position.consume()
				self.tokens.append(Token(types[char], char, self.position.copy()))
	def tokenize(self):
		self.tokens = []
		
		self.ctk = ""

		while True:
			char = self.position.peek()
			if char == None: break
			if char in "\n\t":
				self.position.consume()
				continue

			if char in "+-*/()[]{}&|!; =<>,.":
				self.get_identif()
				if char == " ":
					self.position.consume()
					continue
				self.get_symbol(char)
			elif char in "\"'":
				self.get_identif()
				quote = char
				self.position.consume()  # consume the opening quote
				start = self.position
				value = ""
				while True:
					c = self.position.peek()
					if c is None:
						errors.LexerError(quote, self.position, "Unterminated string literal")
					if c == quote:
						self.position.consume()
						break
					value += c
					self.position.consume()
				self.tokens.append(Token(TokenTypes.STRING, value, self.position.copy()))
				continue

			else:
				self.ctk += char
				self.position.consume()

		self.get_identif()
		self.tokens.append(Token(-1, "EOF", self.position.copy()))
		return self.tokens
