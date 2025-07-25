import errors
import pygame as pg
from eval import *

pg.font.init()

class GameWindow:
	def __init__(self, window):
		self.window = window
		self.entities=[]
	def start_window(self):
		self.screen = pg.display.set_mode(self.window['size'])
		pg.display.set_caption(self.window['title'])

		while True:
			for event in pg.event.get():
				if event.type == pg.QUIT:
					return
			self.update()

	def update(self):
		if self.window['update']:
			self.window['update']()
		self.screen.fill("#FFFFFF")
		for entity in self.entities:
			entity['draw'](self.screen)
		pg.display.flip()
	def add_entity(self, entity):
		self.entities.append(entity)

class createWindow(Function):
	def __init__(self, *args):
		super().__init__("createWindow", args)
	def _call(self):
		window = Table()
		window['title'] = self.args[0]
		window['size'] = self.args[1]
		window['GameWindow'] = GameWindow(window)
		window['add'] = lambda *args: window['GameWindow'].add_entity(*args)
		window['run'] = lambda: window['GameWindow'].start_window()

		return window
	

class Text(Function):
	def __init__(self, *args):
		super().__init__("Text", args)
	def _call(self):
		text = Table()
		text['pos'] = self.args[1]
		text['size'] = self.args[2]
		text['text'] = self.args[0]
		

		text['font'] = pg.font.SysFont(None, 32)

		def draw(surface):
			rendered = text['font'].render(text['text'], True, (0, 0, 0))
			surface.blit(rendered, text['pos'])

		text['draw'] = draw

		return text

class Circle(Function):
	def __init__(self, *args):
		super().__init__("Circle", args)
	def _call(self):
		circle = Table()
		circle['pos'] = self.args[0]
		circle['radius'] = self.args[1]

		def draw(surface):
			pg.draw.circle(surface, (0, 0, 0), circle['pos'], circle['radius'])


		circle['draw'] = draw

		return circle

class Rectangle(Function):
	def __init__(self, *args):
		super().__init__("Rectangle", args)

	def _call(self):
		rect = Table()
		rect['pos'] = self.args[0]
		rect['size'] = self.args[1]

		def draw(surface):
			pg.draw.rect(surface, (0, 0, 0), (*rect['pos'], *rect['size']))

		rect['draw'] = draw
		return rect


class Vector2(Function):
	def __init__(self, *args):
		super().__init__("Vector2", args)
	def _call(self):
		return (self.args[0], self.args[1])
