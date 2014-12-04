import socket, threading
import json
from ip_list import *

class StateListener(object):
	def __init__(self):
		self.tcp_loop = False
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.tcp_ip = vis_ip
		self.tcp_port = vis_port
		self.buffer_size = 2*4096
		
		self.statedict = None
		self.data_init = False
		
		self.thread = None
	
	
	def initialize(self):
		self.sock.connect((self.tcp_ip, self.tcp_port))
		self.tcp_loop = True
		self.thread = threading.Thread(target=self.tcpThread)
		print "Starting new TCP handler thread"
		self.thread.start()
	
	
	def getStateDict(self):
		return self.statedict
	
	
	def finalize(self):
		self.tcp_loop = False
	
	#thread for handling incoming TCP data
	def tcpThread(self):
		while self.tcp_loop:
			data = self.sock.recv(self.buffer_size)
			data = data.splitlines()[0]
			try:
				localdict = json.loads(str(data))
				channel = localdict['CHANNEL'].upper()
				if channel == "GLIDER_STATE":
					self.statedict = localdict
					if not self.data_init:
						self.data_init = True
			except:
				pass
		self.sock.close()
		print "Closing Visualization TCP Thread"



class TrajReplannerComms(object):
	def __init__(self):
		self.tcp_loop = False
		self.tcp_ip = julia_sm_ip
		self.tcp_port = julia_sm_port
		self.tcp_socket = None
		self.tcp_connection = None
		self.julia_connected = False
	
	
	def initializeTCP(self):
		self.tcp_loop = True
		threading.Thread(target=self.TCPServerThread).start()
		print "Success: TCP connection started"

	def TCPServerThread(self):   
		BUFFER_SIZE = 128
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
	
	
	def closeTCP(self):
		if self.julia_connected:
			self.tcp_connection.close()
		else:
			socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((self.tcp_ip, self.tcp_port))
			self.tcp_connection.close()
		self.tcp_socket.close()
		print 'Closed TCP connection'

	
	def sendShiftXY(self, X, Y):
		data = {"SOBJX": X , "SOBJY" : Y}
		msg = (json.JSONEncoder().encode(data))+'\n'
		self.tcp_connection.send(msg)
	


