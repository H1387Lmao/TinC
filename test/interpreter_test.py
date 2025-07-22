import sys
import os

sys.path[0] = os.path.abspath(os.path.join(os.path.dirname(__file__), "../src"))

from lexer import *
from parser import *
from interpreter import *

ip = Interpreter()

debug = False

while True:
	c=input(">> ")
	if c == "exit":
		break
	if c == "debug":
		debug = True
		continue
	if c == "!debug":
		debug = not debug
		continue
	if c.startswith("!p "):
		args = c.split(" ")[1:]
		if args[0] == "var":
			print(ip.get_variable(args[1])[1])
		continue
	tokens=Lexer(c).tokenize()
	if debug:
		print(tokens)
	ast=Parser(tokens).parse_prog()
	if debug:
		print(ast)

	ip.execute_prog(ast)