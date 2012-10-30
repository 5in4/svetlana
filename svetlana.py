#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import subprocess
import sqlite3
import socket
from threading import Thread

import urwid
import cherrypy

OVERSCAN = True

if sys.platform.startswith('linux'):
	TTS = "espeak"
	TTS_ARGS = "-vde+f2"
	MPLAYER = "mplayer"
elif sys.platform.startswith('darwin'):
	TTS = "say"
	TTS_ARGS = ""
	MPLAYER = "mplayer"
elif sys.platform.startswith('win32'):
	TTS = "/path/to/espeak"
	MPLAYER = "/path/to/mplayer"
else:
	raise Exception('platform not supported')


class SvetlanaModel:

	def __init__(self):
		self.db = sqlite3.connect('svetlana.sqlite3')


	def demo_video(self, w):
		self.launch_video('../svetlana-video/v3_720p.mp4')

	def launch_video(self, url):
		try:
			p = subprocess.Popen([MPLAYER, '-fs', url], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
			out, err = p.communicate()
		except OSError:
			sys.exit(0)

	def launch_tts(self, string):
		try:
			p = subprocess.Popen([TTS, TTS_ARGS, string], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		except OSError:
			sys.exit(0)

	def get_people(self):
		c = self.db.cursor()
		people = []
		for row in c.execute("""SELECT id, name, surname FROM people"""):
			people.append(row)
		return people

	def get_person(self, person_id):
		c = self.db.cursor()
		c.execute('SELECT id, name, surname, picture, bio FROM people WHERE id=:pid ', {"pid": person_id})
		return c.fetchone()

	def get_commands(self):
		c  = self.db.cursor()
		commands = []
		for row in c.execute("""SELECT id, command FROM commands"""):
			commands.append(row)
		return commands

	def get_motd(self):
		c = self.db.cursor()
		c.execute('SELECT r1, r2, r3, r4 FROM motd ORDER BY RANDOM() LIMIT 1')
		mo = c.fetchone()
		try:
			m1 = mo[0].encode('utf-8')
		except AttributeError:
			m1 = ""
		try:
			m2 = mo[1].encode('utf-8')
		except AttributeError:
			m2 = ""
		try: 
			m3 = mo[2].encode('utf-8')
		except AttributeError:
			m3 = ""
		try:
			m4 = mo[3].encode('utf-8')
		except AttributeError:
			m4 = ""
		return (m1, m2, m3, m4)
		
	def phase1(self):
		self.launch_video("v1_720p.mp4")
		
	def phase2(self):
		self.launch_video("v2_720p.mp4")

	def phase3(self):
		self.launch_video("v3_720p.mp4")
		
	def phase4(self):
		self.launch_video("v4_720p.mp4")


class SvetlanaView(urwid.Frame):
	palette = [
		('std', 'light green', 'black'), 
		('alert', 'white', 'dark red'),
		('btn', 'light green', 'black'),
		('btn_select', 'black', 'light green'),
		]

	def __init__(self, model):
		self.model = model
		urwid.Frame.__init__(self, None)
		self.content_start()
		self.model.launch_tts('Guten Tag Genosse. Dies ist das Svetlana CCCP Unionsnetz.')

	def content(self, widget_list, header=""):
		body_pile = urwid.AttrWrap(urwid.LineBox(urwid.ListBox(urwid.SimpleListWalker(widget_list)), header), 'std')		
		if OVERSCAN:
			body_pile = urwid.Padding(body_pile, align='left', width=('relative', 100), min_width=None, left=3, right=3)
		self.set_body(body_pile)
		self.frame_header()

	def button(self, t, fn, user_data=None, style='btn', style_active='btn_select'):
		w = urwid.Button(t, fn, user_data)
		w = urwid.AttrWrap(w, style, style_active)
		return w

	def k(self, string):
		lat = ('a', 'A', 'b', 'B', 'c', 'C', 'd', 'D', 'e', 'E', 'f', 'F', 'g', 'G', 'h', 'H', 'i', 'I', 'j', 'J', 'k', 'K', 'l', 'L', 'm', 'M', 'n', 'N', 'o', 'O', 'p', 'P', 'q', 'Q', 'r', 'R', 's', 'S', 't', 'T', 'u', 'U', 'v', 'V', 'w', 'W', 'x', 'X', 'y', 'Y', 'z', 'Z',)
		kyr = ('a', 'Д', 'в', 'B', 'c', 'C', 'd', 'D', 'e', 'Э', 'ғ', 'F', 'g', 'G', 'h', 'H', 'ı', 'I', 'j', 'J', 'к', 'Ҡ', 'l', 'L', 'м', 'M', 'и', 'И', 'o', 'O', 'p', 'Р', 'q', 'Q', 'я', 'Я', 's', 'S', 'т', 'T', 'u', 'U', 'v', 'V', 'ш', 'Ш', 'ж', 'Ж', 'ч', 'Ч', 'z', 'Z',)
		for i in range(len(lat)):
			string = string.replace(lat[i], kyr[i])
		return string

	def content_start(self, w=None):
		btn_security = self.button(self.k("Umgebungsüberwachung"), self.content_security)
		btn_register = self.button(self.k("Personenregister"), self.content_register)
		btn_console = self.button(self.k("Steuerungskonsole"), self.content_console)

		btn_launch = self.button(self.k("dev: Demovideo"), self.model.demo_video)
		btn_quit = self.button(self.k("dev: Beenden"), self.exit_svetlana)
		self.content([btn_security, btn_register, btn_console, urwid.Divider(), btn_launch, btn_quit], self.k("Svetlana CCCP Unionsnetz"))

	def content_register(self, w=None):
		c = [self.button(self.k("Zurück zu Übersicht"), self.content_start), urwid.Divider()]
		for person in self.model.get_people():
			label = "{0} {1}".format(person[1], person[2])
			c.append(self.button(self.k(label), self.content_person, person[0]))
		self.content(c, self.k("Personenregister"))

	def content_security(self, w=None):
		h01 = urwid.Text("")
		h02 = urwid.Text("     ____________________________________________________________________________________________________________")
		h03 = urwid.Text("     |                                                                                                          |")
		h04 = urwid.Text("")
		h05 = urwid.Text("")
		h06 = urwid.Text("")
		h07 = urwid.Text("")
		h08 = urwid.Text("")
		h09 = urwid.Text("")
		h10 = urwid.Text("")
		h11 = urwid.Text("")
		h12 = urwid.Text("")
		h13 = urwid.Text("")
		h14 = urwid.Text("")
		h15 = urwid.Text("")
		h16 = urwid.Text("")
		h17 = urwid.Text("")
		h18 = urwid.Text("")
		h19 = urwid.Text("")
		h20 = urwid.Text("     ____________________________________________________________________________________________________________")
		c = [self.button(self.k("Zurück zu Übersicht"), self.content_start), urwid.Divider(), h01, h02, h03, h04, h05, h06, h07, h08, h09, h10, h11, h12, h13, h14, h15, h16, h17, h18, h19, h20]
		self.content(c, self.k("Umgebungsüberwachung"))

	def content_person(self, w, person_id):
		c = [self.button(self.k("Zurück zum Personenregister"), self.content_register), urwid.Divider()]
		person = urwid.Text(self.k("{0} {1}".format(self.model.get_person(person_id)[1], self.model.get_person(person_id)[2])))
		c.append(person)
		self.content(c, self.k("Personenauskunft"))

	def content_console(self, w=None):
		c = [self.button(self.k("Zurück zu Übersicht"), self.content_start), urwid.Divider()]
		for command in self.model.get_commands():
			label = ">> {0}".format(command[1])
			c.append(urwid.Text(self.k(label)))
		self.content(c, self.k("Bunkersteuerungskonsole"))

	def frame_header(self):
		motd = self.model.get_motd()
		h01 = urwid.Text("                                                                          ")
		h02 = urwid.Text("             --.                                                          ")
		h03 = urwid.Text("           __  \\\\       _____           _   _                             ")
		h04 = urwid.Text("          / /   \\\\     /  ___|         | | | |                             Gedanke des Moments:")
		h05 = urwid.Text("         / /\\   / )    \\ `--.__   _____| |_| | __ _ _ __   __ _           {0}".format(self.k(motd[0])))
		h06 = urwid.Text("          ` \\\\ / /      `--. \\ \\ / / _ \\ __| |/ _` | '_ \\ / _` |          {0}".format(self.k(motd[1])))
		h07 = urwid.Text("       .-    \\\\ /      /\\__/ /\\ V /  __/ |_| | (_| | | | | (_| |          {0}".format(self.k(motd[2])))
		h08 = urwid.Text("      //\\\\___/\\\\       \\____/  \\_/ \\___|\\__|_|\\__,_|_| |_|\\__,_|          {0}".format(self.k(motd[3])))
		h09 = urwid.Text("     //  \\____/\\)                                                         ")
		h10 = urwid.Text("    |/                                                                    ")
		h11 = urwid.Text("                                                                          ")
		c = [h01, h02, h03, h04, h05, h06, h07, h08, h09, h10, h11]

		header_pile = urwid.AttrWrap(urwid.LineBox(urwid.Pile(c)), 'std')		
		
		if OVERSCAN:
			header_pile = urwid.Padding(header_pile, align='left', width=('relative', 100), min_width=None, left=3, right=3)
		self.set_header(header_pile)


	def exit_svetlana(self, w):
		self.model.launch_tts("Auf Wiedersehen")
		raise urwid.ExitMainLoop()




class SvetlanaWeb(Thread):

	def __init__(self, model):
		Thread.__init__(self)
		self.daemon = True
		self.model = model
		cherrypy.config.update({'log.screen': False, 'server.socket_host': '192.168.0.4',})

	def run(self):
		cherrypy.quickstart(self.Routing(self.model))

	def stop(self):
		cherrypy.server.stop()

	class Routing(object):

		def __init__(self, model):
			self.model = model

		@cherrypy.expose
		def index(self):
			return("Hello world")

		@cherrypy.expose
		def video(self, url):
			self.model.launch_video(url)
			return("Playing video!")

		@cherrypy.expose
		def tts(self, string):
			self.model.launch_tts(string)
			return("Speaking to you!")
		
		@cherrypy.expose
		def phase1(self):
			self.model.phase1()
			return("Phase1 started")
		
		@cherrypy.expose
		def phase2(self):
			self.model.phase2()
			return("Phase2 started")

		@cherrypy.expose
		def phase3(self):
			self.model.phase3()
			return("Phase2 started")

		@cherrypy.expose
		def phase4(self):
			self.model.phase4()
			return("Phase4 started")

class SvetlanaController:

	def __init__(self):
		self.model = SvetlanaModel()
		self.web = SvetlanaWeb(self.model)
		self.view = SvetlanaView(self.model)		

	def run(self):
		self.web.start()
		self.loop = urwid.MainLoop(self.view, self.view.palette)
		self.loop.run() 
		self.web.stop()
		sys.exit(0)

if __name__ == '__main__':
	svetlana = SvetlanaController()
	svetlana.run()
