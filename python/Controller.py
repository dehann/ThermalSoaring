#!/usr/bin/env python

import fgFDM
#import fgCNTRL
import socket, struct, time, math, errno
import time
import numpy as np
import threading
import json
from helper import lla2flatearth
from ip_list import *

def interpret_address(addrstr):
    '''interpret a IP:port string'''
    a = addrstr.split(':')
    a[1] = int(a[1])
    return tuple(a)

def cross(a, b):
    c = [a[1]*b[2] - a[2]*b[1],
         a[2]*b[0] - a[0]*b[2],
         a[0]*b[1] - a[1]*b[0]]

    return c

# Fraction distance from x1 to x2, where line intersects with perpendicular line to x0
# x1 is ith point of the tape line
# x2 is i+1 th point of the tape line
# x0 is the position of the plane
def calcPerpendicularFrac(x1,x2,x0):
	a = np.array(x0)-np.array(x1)
	b = np.array(x2)-np.array(x1)
	b_ = np.linalg.norm(b)
	frac = np.dot(a,b/b_)/b_
	return frac

class FGBackseatDriver(object):
	def __init__(self):
		self.state_estimation = self.StateEstimation()

		self.K = np.zeros((2,12))
		self.K[0,6] = 5.0
		self.K[1,7] = 11.0
		self.Kphi = np.zeros((1,3))
		self.Kphi[0,0] = 1.0
		self.Kphi[0,1] = 1.0
		self.Kphi[0,2] = -0.5*1.5*self.Kphi[0,1]*math.atan(200.0*math.pi/180.0)

		self.udpgen = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		self.udpgen.connect(interpret_address(fg_control_ip_port))
		self.udpgen.setblocking(0)

		self.fg_dynamics = fgFDM.fgFDM()
		self.fg_dynamics_udp = udp_socket(fg_dynamics_ip_port)
		#self.fg_control = fgCNTRL.fgCNTRL()

		self.tcp_loop = False
		self.tcp_ip = julia_ip
		self.tcp_port = julia_port
		self.tcp_socket = None
		self.tcp_connection = None
		self.julia_connected = False

		self.tcp_vis_loop = False
		self.tcp_vis_ip = vis_ip
		self.tcp_vis_port = vis_port
		self.tcp_vis_socket = None
		self.tcp_vis_connections = []

		self.control_loop = False
		self.tape_init = False
		self.tape = None
		self.tape_reset = False
		self.tape_t0 = time.time()
		self.tape_count = 0
		
		self.file_write = False
		self.file_handle = None
		
		self.cur_idx = 0
		self.nxt_idx = self.cur_idx + 1
		self.phi_desired_tape = 0
		self.phi_desired = 0.0
		self.error_tape = None
		self.error_wall = None
		self.side_tape = None
		self.side_wall = None
		self.psi_delta = 0

		self.cur_wpt_x = 0
		self.cur_wpt_y = 0
		self.nxt_wpt_x = 0
		self.nxt_wpt_y = 0
		self.wall_l_x = 0
		self.wall_l_y = 0
		self.wall_r_x = 0
		self.wall_r_y = 0
		
		self.wind_vel = 0

		self.trigger_wall_l_x = 0
		self.trigger_wall_l_y = 0
		self.trigger_wall_r_x = 0
		self.trigger_wall_r_y = 0
	
	
	def initializeFileWrite(self, filename):
		self.file_write = True
		self.file_handle = file(filename, "a")
		
		
	def closeFileWrite(self):
		if self.file_write:
			self.file_write = False
			self.file_handle.close()
		print 'Closed file write'


	def initializeTCPThread(self):
		try:
			self.tcp_loop = True
			threading.Thread(target=self.juliaTCPServerThread).start()
			print "Success: TCP thread started"
		except:
			print "Error: unable to start TCP thread"
			return False


	def closeTCPThread(self):
		self.tcp_loop = False
		socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((self.tcp_ip, self.tcp_port))
		self.tcp_socket.close()	
		print 'Closed TCP thread'


	def initializeTCPVisThread(self):
		try:
			self.tcp_vis_loop = True
			threading.Thread(target=self.TCPVisualizationServerThread).start()
			print "Success: TCP Visualization thread started"
		except:
			print "Error: unable to start TCP Visualization thread"
			return False


	def closeTCPVisThread(self):
		self.tcp_vis_loop = False
		socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((self.tcp_vis_ip, self.tcp_vis_port))
		self.tcp_vis_socket.close()
		print 'Closed TCP Visualization thread'


	def closeControlThread(self):
		self.control_loop = False
		print 'Closed control thread'


	def initializeControlThread(self):
		try:
			self.control_loop = True
			threading.Thread(target=self.controlThread).start()
			print "Success: control thread started"
		except:
			print "Error: unable to start control thread"
			return False


	def ft2m(self, x):
		return x * 0.3048


	def m2ft(self, x):
		return x / 0.3048


	def kt2mps(self, x):
		return x * 0.514444444


	def mps2kt(self, x):
		return x / 0.514444444
		
	
	def heading2XY(self, h):
		e = -(h-90.0)#*mathpi/180.0
		if e <= -180.0:
			e = e + 360.0
		return e*math.pi/180.0


	def updateEstimatedState(self):
		buf = self.fg_dynamics_udp.recv(1000)
		self.fg_dynamics.parse(buf)
		self.state_estimation.updateStates(self.fg_dynamics)
		if self.file_write:
			np.savetxt(self.file_handle, self.state_estimation.x.transpose(), delimiter=",", newline="\n")


	def controller(self):
		u = -self.K*self.state_estimation.xBar()

		mmx = (u[0,0].item())
		mmy = (u[1,0].item())
		
		satx = 10.0
		saty = 2.0
		if mmx > satx: 
			mmx = satx
		if mmx < -satx:
			mmx = -satx
		if mmy > saty: 
			mmy = saty
		if mmy < -saty:
			mmy = -saty
		cntrstr = str(mmx)+"\t"+str(-mmy)+"\n"
		try:
			self.udpgen.send(cntrstr)
		except:
			print "Could not send control command - maybe no connection exists?"
			pass


	def parseTCPData(self, tcp_str):
		try:
			tcp_dict = json.loads(str(tcp_str))
			channel = tcp_dict['CHANNEL'].upper()
			if channel == "REQUEST_DATA":
				self.sendStateData(tcp_dict)
			elif channel == "NEW_TAPE":
				self.setNewTrajectoryTape(tcp_dict)
		except:
			print "Error: unable to parse JSON string"


	def sendStateData(self, dictionary):
		lat = self.state_estimation.x[0,0]
		lon = self.state_estimation.x[1,0]
		alt = self.state_estimation.x[2,0]
		v_north = self.state_estimation.x[3,0]
		v_east = self.state_estimation.x[4,0]
		v_down = self.state_estimation.x[5,0]
		phi = self.state_estimation.x[6,0]
		theta = self.state_estimation.x[7,0]
		psi = self.state_estimation.x[8,0]
		vcas = self.state_estimation.x[9,0]
		alpha = self.state_estimation.x[10,0]
		beta = self.state_estimation.x[11,0]
		state_data = {'CHANNEL':'GLIDER_STATE', 'LON':lon, 'LAT':lat, 'ALT':alt, 'V_NORTH':v_north, 'V_EAST':v_east, 'V_DOWN':v_down, 'PHI':phi, 'THETA':theta, 'HEADING':psi, 'VCAS':vcas, 'ALPHA':alpha, 'BETA':beta, 'CUR_INDEX':self.cur_idx}
		state_str = (json.JSONEncoder().encode(state_data))+'\n'
		if self.julia_connected:
			self.tcp_connection.send(state_str)


	def setNewTrajectoryTape(self, dictionary):
		print "New tape received"
		self.tape_count = self.tape_count + 1
		time_vec = dictionary['t']
		x_vec = dictionary['x']
		y_vec = dictionary['y']
		u_vec = dictionary['u']
		self.tape = dictionary
		self.tape['count'] = self.tape_count
		self.tape_init = True
		self.tape_reset = True
		self.cur_idx = 0
		self.nxt_idx = self.cur_idx + 1


	def juliaTCPServerThread(self):   
		BUFFER_SIZE = 4096
		while self.tcp_loop:
			self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			self.tcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
			self.tcp_socket.bind((self.tcp_ip, self.tcp_port))
			self.tcp_socket.listen(1)
			self.tcp_connection, addr = self.tcp_socket.accept()
			self.julia_connected = True
			print 'Connection address:', addr
			while self.tcp_loop:
				data = self.tcp_connection.recv(BUFFER_SIZE)
				if not data: break
				self.parseTCPData(str(data))
			self.tcp_connection.close()
			self.julia_connected = False
			print "Closed the TCP socket"


	def TCPVisualizationServerThread(self):
		self.tcp_vis_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.tcp_vis_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self.tcp_vis_socket.bind((self.tcp_vis_ip, self.tcp_vis_port))
		self.tcp_vis_socket.listen(5)
		while self.tcp_vis_loop:
			connection, addr = self.tcp_vis_socket.accept()
			self.tcp_vis_connections.append(connection)
			print 'Connection address for visualization:', addr
			threading.Thread(target=self.VisualizationClientThread, args=[connection]).start()
		for c in self.tcp_vis_connections:
			c.close()
		print "Closed all TCP visualization sockets"
			

	def VisualizationClientThread(self, conn):
		while self.tcp_vis_loop:
			try:
				lat = self.state_estimation.x[0,0]
				lon = self.state_estimation.x[1,0]
				alt = self.state_estimation.x[2,0]
				v_north = self.state_estimation.x[3,0]
				v_east = self.state_estimation.x[4,0]
				v_down = self.state_estimation.x[5,0]
				phi = self.state_estimation.x[6,0]
				theta = self.state_estimation.x[7,0]
				psi = self.state_estimation.x[8,0]
				vcas = self.state_estimation.x[9,0]
				alpha = self.state_estimation.x[10,0]
				beta = self.state_estimation.x[11,0]
				state_data = {'CHANNEL':'GLIDER_STATE', 'LON':lon, 'LAT':lat, 'ALT':alt, 'V_NORTH':v_north, 'V_EAST':v_east, 'V_DOWN':v_down, 'PHI':phi, 'THETA':theta, 'HEADING':psi, 'VCAS':vcas, 'ALPHA':alpha, 'BETA':beta, 'WIND_VEL_DOWN':self.wind_vel}
				state_str = (json.JSONEncoder().encode(state_data))+'\n'
				conn.send(state_str)
				if self.tape_init:
					self.tape['CUR_WPT'] = [self.cur_wpt_x,self.cur_wpt_y]
					self.tape['NXT_WPT'] = [self.nxt_wpt_x,self.nxt_wpt_y]
					self.tape['WALL_LEFT'] = [self.wall_l_x,self.wall_l_y]
					self.tape['WALL_RIGHT'] = [self.wall_r_x,self.wall_r_y]
					self.tape['DIST_FROM_LINE'] = self.error_tape
					self.tape['DIST_FROM_WALL'] = self.error_wall
					self.tape['DESIRED_PHI'] = float(self.phi_desired*180.0/math.pi)
					self.tape['DESIRED_PHI_TAPE'] = float(self.phi_desired_tape*180.0/math.pi)
					self.tape['TRIGGER_WALL_LEFT'] = [self.trigger_wall_l_x,self.trigger_wall_l_y]
					self.tape['TRIGGER_WALL_RIGHT'] = [self.trigger_wall_r_x,self.trigger_wall_r_y]
					tape_str = (json.JSONEncoder().encode(self.tape))+'\n'
					conn.send(tape_str)		
			except:
				#print "Exception occured"
				conn.close()
				break





	def calcCurLine(self, x, y, u):
		x1 = x[self.cur_idx][0]
		y1 = y[self.cur_idx][0]
		x2 = x[self.nxt_idx][0]
		y2 = y[self.nxt_idx][0]
		uav_x, uav_y = lla2flatearth(self.state_estimation.x[0,0], self.state_estimation.x[1,0])
		
		#for calculating the trigger wall (index 29)
		xt = x[29][0]
		yt = y[29][0]
		xt_p = x[28][0]
		yt_p = y[28][0]
		dxt = (xt-xt_p)
		dyt = (yt-yt_p)
		anglet = math.atan2(dyt, dxt) * 180.0/math.pi
		perpanglet = (anglet + 90) * math.pi/180.0
		self.trigger_wall_l_x = xt + 100*math.cos(perpanglet)
		self.trigger_wall_r_x = xt - 100*math.cos(perpanglet)
		self.trigger_wall_l_y = yt + 100*math.sin(perpanglet)
		self.trigger_wall_r_y = yt - 100*math.sin(perpanglet)

		#for calcuating the current line
		dx = (x2-x1)
		dy = (y2-y1)
		
		#for calculating error to and side of current line of tape
		err_num = abs(dy*uav_x - dx*uav_y - x1*y2 + x2*y1)
		err_den = np.sqrt(dx**2 + dy**2)
		self.error_tape = err_num/err_den
		self.side_tape = (uav_x - x1)*dy - (uav_y - y1)*dx
		if self.side_tape > 0:
		    self.side_tape = -1 #right of line
		else:
		    self.side_tape = 1 #left of line
		self.error_tape = self.error_tape*self.side_tape
		 
		#for calculating the current wall
		angle = math.atan2(dy, dx) * 180.0/math.pi
		perpangle = (angle + 90) * math.pi/180.0
		xperpleft = x2 + 50*math.cos(perpangle)
		xperpright = x2 - 50*math.cos(perpangle)
		yperpleft = y2 + 50*math.sin(perpangle)
		yperpright = y2 - 50*math.sin(perpangle)
		
		#for calculating the error to and side of current wall
		dx = (xperpright-xperpleft)
		dy = (yperpright-yperpleft)
		err_num = abs(dy*uav_x - dx*uav_y - xperpleft*yperpright + xperpright*yperpleft)
		err_den = np.sqrt(dx**2 + dy**2)
		self.error_wall = err_num/err_den
		self.side_wall = (uav_x - xperpleft)*dy - (uav_y - yperpleft)*dx
		if self.side_wall > 0:
		    self.side_wall = -1 #behind wall
		else:
		    self.side_wall = 1 #in front of wall
		    if self.cur_idx < (len(x)-2):
				self.cur_idx = self.nxt_idx
				self.nxt_idx = self.cur_idx + 1

		self.cur_wpt_x = x1
		self.cur_wpt_y = y1
		self.nxt_wpt_x = x2
		self.nxt_wpt_y = y2
		self.wall_l_x = xperpleft
		self.wall_l_y = yperpleft
		self.wall_r_x = xperpright
		self.wall_r_y = yperpright

		#index into current control from tape
		
		# TODO make this a linear interpolation look up
		frac = calcPerpendicularFrac([x1,y1],[x2,y2],[uav_x,uav_y])
		interpu =  u[self.cur_idx][0]
		#if (frac<1):
		#	interpu =  u[self.cur_idx][0] + frac*(u[self.nxt_idx][0] - u[self.cur_idx][0])
		if (self.side_wall==1):
			interpu = 0.0
		self.phi_desired_tape = interpu
		
		#calculate delta psi (difference between line angle and uav angle)
		uav_angle = self.heading2XY(self.state_estimation.x[8,0]*180.0/math.pi)
		vd = [0.0,0.0,0.0]
		vr = [0.0,0.0,0.0]
		vd[0] = math.cos(angle*math.pi/180.0)
		vd[1] = math.sin(angle*math.pi/180.0)
		vr[0] = math.cos(uav_angle)
		vr[1] = math.sin(uav_angle)
		#(angle*math.pi/180.0 - uav_angle)
		self.psi_delta = math.acos(vd[0]*vr[0] + vd[1]*vr[1])
		cr = cross(vd,vr)
		if cr[2]>0:
			self.psi_delta = -self.psi_delta
		
		#print "CURRENT INDEX", self.cur_idx
		#print "CURRENT WPT", x2, y2
		#print "DISTANCE TO WALL", self.error_wall
		#print "DISTANCE TO LINE", self.error_tape
		#print "ANGLE", angle
		#print "UAV_ANGLE", uav_angle*180.0/math.pi
		#print "DELTA_PSI", self.psi_delta*180.0/math.pi
		
		
		
	def calcPhiDesired(self):
		#print "Kphi", self.Kphi
		chibar = np.matrix([[self.phi_desired_tape],[0.5*math.atan(self.error_tape*math.pi/180.0)],[math.tan(self.psi_delta)]])
		#print "chibar", chibar
		self.phi_desired = self.Kphi*chibar
		if self.phi_desired[0,0] <-60.0*math.pi/180.0:
			self.phi_desired[0,0] = -60.0*math.pi/180.0
		if self.phi_desired[0,0] > 60.0*math.pi/180.0:
			self.phi_desired[0,0] = 60.0*math.pi/180.0
		
		#print "DESIRED_PHI", round(self.phi_desired[0,0]*180.0/math.pi,1), " | ", round(self.phi_desired_tape*180.0/math.pi,1), " ^ ", -round(self.state_estimation.x[5,0],2)
		self.state_estimation.updateDesiredStates('PHI', self.phi_desired[0,0]*180.0/math.pi)
		
		

	def controlThread(self):
		t = time.time()
		self.state_estimation.updateDesiredStates('THETA', 1.5)
		self.state_estimation.updateDesiredStates('PHI', 0.)
		while self.control_loop:
			time_elapsed = time.time() - t
			if time_elapsed >= 0.02:
				t = time.time()
				#print "dt",time_elapsed, self.tape_reset, self.tape_init
				if self.tape_init:
					if self.tape_reset:
						self.tape_t0 = time.time()
						time_vec = self.tape['t']
						x_vec = self.tape['x']
						y_vec = self.tape['y']
						u_vec = self.tape['u']
						self.tape_reset = False
					self.calcCurLine(x_vec, y_vec, u_vec)
					self.calcPhiDesired()
				
				self.controller()
			


	class StateEstimation(object):
		def __init__(self):
			self.x = np.matrix([[0.0],[0.0],[0.0],[0.0],[0.0],[0.0],[0.0],[0.0],[0.0],[0.0],[0.0],[0.0]])
			self.x_desired = np.matrix([[0.0],[0.0],[0.0],[0.0],[0.0],[0.0],[0.0],[0.0],[0.0],[0.0],[0.0],[0.0]])


		def xBar(self):
			return self.x - self.x_desired


		def updateDesiredStates(self, attr_str, attr_val):
			if attr_str.upper() == "LAT":
		  		self.x_desired[0,0] = attr_val
			elif attr_str.upper() == "LON":
				self.x_desired[1,0] = attr_val
			elif attr_str.upper() == "ALT":
				self.x_desired[2,0] = attr_val
			elif attr_str.upper() == "V_NORTH":
				self.x_desired[3,0] = attr_val
			elif attr_str.upper() == "V_EAST":
				self.x_desired[4,0] = attr_val
			elif attr_str.upper() == "V_DOWN":
				self.x_desired[5,0] = attr_val
			elif attr_str.upper() == "PHI":
				self.x_desired[6,0] = attr_val*math.pi/180.0
			elif attr_str.upper() == "THETA":
				self.x_desired[7,0] = attr_val*math.pi/180.0
			elif attr_str.upper() == "PSI":
				self.x_desired[8,0] = attr_val*math.pi/180.0
			elif attr_str.upper() == "VCAS":
				self.x_desired[9,0] = attr_val
			elif attr_str.upper() == "ALPHA":
				self.x_desired[10,0] = attr_val*math.pi/180.0
			elif attr_str.upper() == "BETA":
				self.x_desired[11,0] = attr_val*math.pi/180.0


		def updateStates(self, fg):
			# should do flat earth conversions here
			self.x[0,0] = fg.get('latitude', units='radians')+0.0
			self.x[1,0] = fg.get('longitude', units='radians')+0.0
			self.x[2,0] = fg.get('altitude', units='meters')+0.0

			self.x[3,0] = fg.get('v_north', units='mps')+0.0
			self.x[4,0] = fg.get('v_east', units='mps')+0.0
			self.x[5,0] = fg.get('v_down', units='mps')+0.0

			self.x[6,0] = fg.get('phi', units='radians')+0.0
			self.x[7,0] = fg.get('theta', units='radians')+0.0
			self.x[8,0] = fg.get('psi', units='radians')+0.0

			self.x[9,0] = fg.get('vcas', units='mps')+0.0
			self.x[10,0] = fg.get('alpha', units='radians')+0.0
			self.x[11,0] = fg.get('beta', units='radians')+0.0
			
			self.wind_vel = fg.get('v_wind_body_down', units='mps')+0.0
			

class udp_socket(object):
    '''a UDP socket'''
    def __init__(self, device, blocking=True, input=True):
        a = device.split(':')
        if len(a) != 2:
            print("UDP ports must be specified as host:port")
            sys.exit(1)
        self.port = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        if input:
            self.port.bind((a[0], int(a[1])))
            self.destination_addr = None
        else:
            self.destination_addr = (a[0], int(a[1]))
        if not blocking:
            self.port.setblocking(0)
        self.last_address = None

    def recv(self,n=1000):
        try:
            data, self.last_address = self.port.recvfrom(n)
        except socket.error as e:
            if e.errno in [ errno.EAGAIN, errno.EWOULDBLOCK ]:
                return ""
            raise
        return data

    def write(self, buf):
        try:
            if self.destination_addr:
                self.port.sendto(buf, self.destination_addr)
            else:
                self.port.sendto(buf, self.last_addr)
        except socket.error:
            pass


try:
	tlast = time.time()
	FGDriver = FGBackseatDriver()
	FGDriver.initializeTCPThread()
	FGDriver.initializeControlThread()
	FGDriver.initializeTCPVisThread()
	#FGDriver.initializeFileWrite("vdown.csv")
	while True:
		if time.time() - tlast >= 0.02:
			FGDriver.updateEstimatedState()
			tlast = time.time()
		#print 'IN STATE UPDATE LOOP'
except KeyboardInterrupt:
	FGDriver.closeTCPThread()
	FGDriver.closeControlThread()
	FGDriver.closeTCPVisThread()
	#FGDriver.closeFileWrite()
	print "Closing Flight Gear Driver"
