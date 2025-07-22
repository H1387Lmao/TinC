class Function:
	def __init__(self, name, args):
		self.name = name
		self.args = args

class println(Function):
	def __init__(self, args):
		super().__init__("println", args)
		self.__call()
	def __call(self):
		print(*self.args)
class cprint(Function):
	def __init__(self, args):
		super().__init__("print", args)
		self.__call()
	def __call(self):
		print(*self.args, end="")
stdlibrary={}
stdlibrary['println'] = println
stdlibrary['print'] = cprint