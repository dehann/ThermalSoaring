#!/usr/bin/env python

import socket, threading
import time
import json
import numpy as np
import random

from TCPHandlers import *
from PredictThermals import *
from GliderProperties import *
from helper import *


# class to manage which state the system is in
# This class will maintain current mode, receive state information and transition between modes
# as required. Present design calls for state retrieval over TCP from fg_control_04.py and transmit 
# next waypoint to TrajReplanner.jl over a different TCP connection
class StateMachine(object):
	def __init__(self):
		# mode 0 - startup
		# mode 1 - Marker (assuming will glider will climb at this point)
		# mode 2 - centering for climb
		# mode 3 - flytogoal
		# mode 4 - explore area
		# mode 5 - landing
		self.mode = 0
		self.glider = GliderProperties()
		self.predict_thermals = PredictThermals()
		self.homether = {"LAT" : 37.61633*math.pi/180.0, "LON" : -122.38334*math.pi/180.0}
		self.waypoints = {"LAT" : 37.64633*math.pi/180.0, "LON" : -122.38334*math.pi/180.0}
		self.cur_goal_x = 0.0
		self.cur_goal_y = 0.0
		#lla2flatearth(self.waypoints["LAT"],self.waypoints["LON"])
		self.prev_goal_x = 0.0
		self.prev_goal_y = 0.0
		self.cur_x = 0
		self.cur_y = 0

	def checkDistofWP(self):
		print "THE OFFSETS FOR THIS WAYPOINT ARE", self.cur_goal_x, self.cur_goal_y
	
	def evalTransitions(self, state):
		#print "MODE: ", self.mode
		self.cur_x, self.cur_y = lla2flatearth(state["LAT"],state["LON"])
		#print 'CURRENT POS: ', self.cur_x, self.cur_y
		#print 'CURRENT GOAL: ', self.cur_goal_x, self.cur_goal_y
		if self.mode == 0:
			d = self.inMode0(state)
		elif self.mode == 1:
			d =self.inMode1(state)
		elif self.mode == 2:
			d = self.inMode2(state)
		elif self.mode == 3:
			d = self.inMode3(state)
		
		if d:
			return d
			
	
	def inMode0(self, state):
		if state["JULIA_CONN"]:
			self.mode = 1
	
	def inMode1(self,state):
		if (state["ALT"] >= state["TARGET_ALT"]):
			# proceed to goal
			self.mode = 3
			#return {"X" : -self.prev_goal_x+self.cur_goal_x, "Y" : -self.prev_goal_y+self.cur_goal_y}
		#else:
			#print "ALT GAIN REQUIRED ", (state["TARGET_ALT"] - state["ALT"])
		
	
	def inMode2(self,state):
		# do something
		# we are not ready for centering yet, transition back to default marker
		self.mode = 1
	
	# Fly to goal
	def inMode3(self,state):
		dist_to_wp = math.sqrt((self.cur_goal_x-self.cur_x)**2+(self.cur_goal_y-self.cur_y)**2)
		dist_to_thermal = math.sqrt((self.cur_x)**2+(self.cur_y)**2)
		delta_alt = state["ALT"] - self.glider.getMinWorkAlt()
		
		if delta_alt > 0:
			if self.glider.evalMaxGlide(delta_alt) <= dist_to_thermal:
				print "Head home, I've exhausted my fuel"
				self.mode = 1
				tempx = self.cur_goal_x
				tempy = self.cur_goal_y
				self.cur_goal_x = 0.0
				self.cur_goal_y = 0.0
				return {"X" : -tempx, "Y" : -tempy}	#return home and gain alt
			if dist_to_wp < 400.0:
				print "DIST_TO_WP", dist_to_wp
				#print "ALT_A_CONE", self.glider.evalReqGlideAlt(-dist_to_thermal) 
				print "Reached current waypoint, selecting a new random waypoint"
				#randomize a point
				self.prev_goal_x = self.cur_goal_x
				self.prev_goal_y = self.cur_goal_y
				randx = random.uniform(-5000,5000)
				randy = random.uniform(-5000,5000)
				self.cur_goal_x = randx
				self.cur_goal_y = randy
				return {"X" : -self.prev_goal_x+self.cur_goal_x, "Y" : -self.prev_goal_y+self.cur_goal_y}
		else:
			# force landing (dud placeholder)
			self.mode = 5



# Main driver regulating propagation of the state machine in time
class FlowControl(object):
	def __init__(self):
		self.tcomms = TrajReplannerComms()
		self.mode_select = StateMachine()
		self.state_listener = StateListener()
	
	
	def initialize(self):
		self.tcomms.initializeTCP()
		self.state_listener.initialize()
		print "VISUALIZATION STATE LISTEN INITIALIZED"
		self.mode_select.checkDistofWP()
	
	
	def run(self):
		try:
			while True:
				if self.state_listener.data_init == True:
					state = self.state_listener.getStateDict()
					# Add additional information to for evaluation of state transitions to state dict
					state["TARGET_ALT"] = 1500.0
					if self.tcomms.julia_connected:
						state["JULIA_CONN"] = True
					else:
						state["JULIA_CONN"] = False
						
					d = self.mode_select.evalTransitions(state)
					if d:
						self.tcomms.sendShiftXY(d["X"],d["Y"])
				time.sleep(0.2)
		except KeyboardInterrupt:
			self.finalize()
	
	
	def keyboardDefaultTest(self):
		try:
			while 1==1:
				print "Shift zero"
				X = float(raw_input("X: "))
				Y = float(raw_input("Y: "))
				self.tcomms.sendShiftXY(X,Y)
		except KeyboardInterrupt:
			self.finalize()
	
	
	def finalize(self):
		self.state_listener.finalize()
		self.tcomms.closeTCP()
		print "Closing out FlowControl members"


flow = FlowControl()
flow.initialize()
#flow.keyboardDefaultTest()
flow.run()



