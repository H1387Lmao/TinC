import errors
from eval import *

class createWindow(Function):
	def __init__(self, *args):
		super().__init__("createWindow", args)
	def _call(self):
		window = Table()
		window['size'] = self.args[1:2]
		window['run'] = lambda: print("running")

		return window
