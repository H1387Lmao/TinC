class TokenTypes:
	EOF = -1

	INT = 0
	IDENTIFIER = 1
	STRING = 2
	
	POINTER = 3
	
	ADD = 4
	SUB = 5
	MUL = 6
	DIV = 7
	INCREMENT = 20
	DECREMENT = 21

	PAREN = 8
	BRACKET = 9
	BRACES = 10

	AND = 11
	OR = 12
	XOR = 13
	NOT = 14

	EQUALS = 15
	SEMI = 16
	ARROW = 17
	DQT = 22
	SQT = 23
	
	COMPARISON = 18

	KEYWORD = 19

class Token:
	def __init__(self, t, v, position):
		self.t,self.v,self.position = t,v,position
	def __repr__(self):
		return f"Token({repr(self.t)}, {repr(self.v)})"

