#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import subprocess
import socket
from threading import Thread

import urwid
import cherrypy

if sys.platform.startswith('linux'):
	TTS = "espeak"
	MPLAYER = "mplayer"
elif sys.platform.startswith('darwin'):
	TTS = "say"
	MPLAYER = "mplayer"
elif sys.platform.startswith('win32'):
	TTS = "/path/to/espeak"
	MPLAYER = "/path/to/mplayer"
else:
	raise Exception('platform not supported')


class SvetlanaModel:

	def __init__(self):
		pass


	def demo_video(self, w):
		self.launch_video('http://praegnanz.de/html5video/player/video_SD.mp4')

	def launch_video(self, url):
		try:
			p = subprocess.Popen([MPLAYER, '-fs', url], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
			out, err = p.communicate()
		except OSError:
			sys.exit(0)

	def launch_tts(self, string):
		try:
			p = subprocess.Popen([TTS, string], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		except OSError:
			sys.exit(0)	

class SvetlanaView(urwid.Frame):
	palette = [
		('std', 'light green', 'black'), 
		('alert', 'white', 'dark red'),
		('btn', 'black', 'light green'),
		('btn_select', 'dark gray', 'light green'),
		]

	def __init__(self, model):
		self.model = model
		urwid.Frame.__init__(self, None)
		self.content_start()
		self.set_header(self.frame_header())

	def content(self, widget_list):
		self.set_body(urwid.AttrWrap(urwid.ListBox(urwid.SimpleListWalker(widget_list)), 'std'))

	def button(self, t, fn):
		w = urwid.Button(t, fn)
		w = urwid.AttrWrap(w, 'btn', 'btn_select')
		return w

	def k(self, string):
		lat = ('a', 'A', 'b', 'B', 'c', 'C', 'd', 'D', 'e', 'E', 'f', 'F', 'g', 'G', 'h', 'H', 'i', 'I', 'j', 'J', 'k', 'K', 'l', 'L', 'm', 'M', 'n', 'N', 'o', 'O', 'p', 'P', 'q', 'Q', 'r', 'R', 's', 'S', 't', 'T', 'u', 'U', 'v', 'V', 'w', 'W', 'x', 'X', 'y', 'Y', 'z', 'Z',)
		kyr = ('д', 'Д', 'в', 'B', 'c', 'C', 'd', 'D', 'э', 'Э', 'ғ', 'F', 'g', 'G', 'h', 'H', 'ї', 'I', 'j', 'J', 'к', 'Ҡ', 'l', 'L', 'м', 'M', 'и', 'И', 'o', 'O', 'p', 'Р', 'q', 'Q', 'я', 'Я', 's', 'S', 'т', 'T', 'u', 'U', 'v', 'V', 'ш', 'Ш', 'ж', 'Ж', 'ч', 'Ч', 'z', 'Z',)
		for i in range(len(lat)):
			string = string.replace(lat[i], kyr[i])
		return string

	def content_start(self, w=None):
		btn_launch = self.button(self.k("Launch video"), self.model.demo_video)
		btn_register = self.button(self.k("Look up person"), self.content_register)
		btn_quit = self.button("Quit", self.exit_svetlana)
		self.content([btn_launch, btn_register, btn_quit])

	def content_register(self, w=None):
		self.content([self.button("Quit", self.exit_svetlana)])

	def frame_header(self):
		return urwid.AttrWrap(urwid.Text("\n          --.\n        __  \\\\       _____           _   _   \n       / /   \\\\     /  ___|         | | | |  \n      / /\\   / )    \\ `--.__   _____| |_| | __ _ _ __   __ _ \n       ` \\\\ / /      `--. \\ \\ / / _ \\ __| |/ _` | '_ \\ / _` |\n    .-    \\\\ /      /\\__/ /\\ V /  __/ |_| | (_| | | | | (_| |\n   //\\\\___/\\\\       \\____/  \\_/ \\___|\\__|_|\\__,_|_| |_|\\__,_| \n  //  \\____/\\)      \n |/\n "), 'std')

	def exit_svetlana(self, w):
		self.model.launch_tts("Auf Wiedersehen")
		raise urwid.ExitMainLoop()


class SvetlanaWeb(Thread):

	def __init__(self, model):
		Thread.__init__(self)
		self.daemon = True
		self.model = model
		cherrypy.config.update({'log.screen': False,})# 'server.socket_host': '0.0.0.0', 'server.socket_port': 80,})

	def run(self):
		cherrypy.quickstart(self.Routing(self.model))

	def stop(self):
		cherrypy.server.stop()

	class Routing(object):

		def __init__(self, model):
			self.model = model

		@cherrypy.expose
		def index(self):
			return("Привет мир!")

		@cherrypy.expose
		def video(self, url):
			self.model.launch_video(url)
			return("Видео началось")

		@cherrypy.expose
		def tts(self, string):
			self.model.launch_tts(string)
			return("Выступление началось!")


class SvetlanaController:

	def __init__(self):
		self.model = SvetlanaModel()
		self.web = SvetlanaWeb(self.model)
		self.view = SvetlanaView(self.model)


	def run(self):
		self.web.start()
		self.model.launch_tts('Svetlana gestartet')
		self.loop = urwid.MainLoop(self.view, self.view.palette)
		self.loop.run()
		self.web.stop()
		sys.exit(0)

if __name__ == '__main__':
	svetlana = SvetlanaController()
	svetlana.run()