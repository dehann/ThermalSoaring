from helper import *
import math

# Some clever mechanism to predict possible thermal locations
# Infrared camers, doppler radar data, expert knowledge, etc.
# Just the one known thermal location for now
class PredictThermals(object):
	def __init__(self):
		self.nextTher = {"LAT" : 37.61633, "LON" : -122.38334}
	
	def distance(self, state):
		dist = mDistance(self.nextTher["LAT"]*3600000, self.nextTher["LON"]*3600000, state["LAT"]*3600000*180.0/math.pi, state["LON"]*3600000*180.0/math.pi)
		return dist
		
	
	
	
