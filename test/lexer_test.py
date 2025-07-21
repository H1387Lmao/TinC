import sys
import os

sys.path[0] = os.path.abspath(os.path.join(os.path.dirname(__file__), "../src"))

from lexer import *

while True:
	c=input(">> ")
	if c == "exit":
		break
	print(Lexer(c).tokenize())