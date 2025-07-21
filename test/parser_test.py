import sys
import os

sys.path[0] = os.path.abspath(os.path.join(os.path.dirname(__file__), "../src"))

from lexer import *
from parser import *

while True:
	c=input(">> ")
	if c == "exit":
		break
	tokens=Lexer(c).tokenize()
	print(tokens)
	print(Parser(tokens).parse_prog())