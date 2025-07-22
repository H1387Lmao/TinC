import errors

class Position:
	def __init__(self, index, source):
		self.index = index
		self.source = source
	def peek(self, amount=1):
		idx=self.index + amount
		if idx>=len(self.source):
			return None
		return self.source[idx]
	def consume(self):
		self.index+=1
		return self.peek(0)
	def getall(self):
		return (self.index, self.lineno, self.column, self.source)

	def back(self):
		self.index-=1
		return self.peek(0)

class TokenPosition(Position):
	def __init__(self, source,index=-1,ln=0,col=0):
		super().__init__(index,source)

		self.lineno=ln
		self.column=col
	def consume(self):
		self.index+=1
		self.column+=1
		if self.peek(0) == "\n":
			self.column = 0
			self.lineno+=1
		return self.peek(0)
	def copy(self):
		return TokenPosition(self.source, self.index,self.lineno, self.column)

class ParserPosition(Position):
	def __init__(self, source, index=-1):
		super().__init__(index,source)
	def peek(self, amount=1):
		res = super().peek(amount)
		if res == "\n":
			self.column = 0
			self.lineno+=1
		return res
	def expect(self, type):
		if type == self.peek().v:
			return self.consume()
		errors.SyntaxError(self.peek(),
			f"SyntaxError: Expected '{type}' got %tk.v%"
		)
	def copy(self):
		return ParserPosition(self.source, self.index)