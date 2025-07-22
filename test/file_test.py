import sys
import os

target = sys.argv[1] if len(sys.argv)!=1 else sys.exit()
target = os.path.abspath(target)

sys.path[0] = os.path.abspath(os.path.join(os.path.dirname(__file__), "../src"))

from lexer import *
from parser import *
from interpreter import *

if os.path.isfile(target):
	with open(target) as f:
		content = f.read()
	tokens = Lexer(content).tokenize()
	ast = Parser(tokens).parse_prog()
	print(ast)
	Interpreter().execute_prog(ast)
else:
	print("file not found.")
	print(target)
