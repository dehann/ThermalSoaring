#!/usr/bin/env python

from pylab import *
import socket
import time
import threading
import json
from collections import deque
from glider_icon import *
from helper import lla2flatearth

#init plot
fig, ax = plt.subplots()
ax.axis('equal')

#init glider icon
bp, lwp, rwp, ltp, rtp, vp, tp = addAndGetGliderIcon(ax, 0,0,0,0,0)

#init glider trail
trail_len = 1000
trail_x = deque(maxlen=trail_len)
trail_y = deque(maxlen=trail_len)
trail, = ax.plot([0.0], [0.0], color='m', linewidth=2)

#init glider properties
glider_x = 0
glider_y = 0
glider_heading = 0
glider_roll = 0
glider_altitiude = 0

#init tape
new_tape = True
tape_x = None
tape_y = None
tape, = ax.plot([0.0], [0.0], color='b', linewidth=1)

#init tcp connection
tcp_ip = '127.0.0.1'
tcp_port = 5511
buffer_size = 4096
tcp_loop = True

#init tcp data
tcp_dict = None
data_init = False
tape_init = False
glider_data = None
tape_data = None


#thread for handling incoming TCP data
def tcpThread():
	global glider_data, tape_data, tcp_dict, data_init, tape_init, tape_x, tape_y, glider_x, glider_y, glider_heading, glider_roll, glider_altitiude
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.connect((tcp_ip, tcp_port))
	while tcp_loop:
		data = s.recv(buffer_size)
		data = data.splitlines()[0]
		try:
			tcp_dict = json.loads(str(data))
			channel = tcp_dict['CHANNEL'].upper()
			if channel == "NEW_TAPE":
				if not tape_init:
					tape_init = True
				tape_data = tcp_dict
				tape_x = [item for sublist in tape_data['x'] for item in sublist]
				tape_y = [item for sublist in tape_data['y'] for item in sublist]
			elif channel == "GLIDER_STATE":
				if not data_init:
					data_init = True
				glider_data = tcp_dict
				glider_x, glider_y = lla2flatearth(glider_data['LAT'], glider_data['LON'])
				glider_heading = glider_data["HEADING"]*180/math.pi
				glider_roll = glider_data["PHI"]*180/math.pi
				glider_altitiude = glider_data["ALT"]
		except:
			pass
	s.close()
	print "Closing Visualization TCP Thread"

t = threading.Thread(target=tcpThread)
t.start()

#timer to update figure
def timer_callback(axes):
	global ax, bp, lwp, rwp, ltp, rtp, vp, tp

	if tape_init:
		tape.set_xdata(tape_x)
		tape.set_ydata(tape_y)

	trail_x.append(glider_x)
	trail_y.append(glider_y)
	trail.set_xdata(trail_x)
	trail.set_ydata(trail_y)

	bp.remove()
	lwp.remove()
	rwp.remove()
	ltp.remove()
	rtp.remove()
	vp.remove()
	tp.remove()
	bp, lwp, rwp, ltp, rtp, vp, tp = addAndGetGliderIcon(ax, glider_x, glider_y, glider_heading, glider_roll, glider_altitiude)

	#center on glider
	xmin, xmax = xlim()
	ymin, ymax = ylim()
	width = abs(xmax-xmin) 
	height = abs(ymax-ymin)
	xlim(glider_x-width/2, glider_x+width/2)
	ylim(glider_y-height/2, glider_y+height/2)
	fig.canvas.draw()

#key callback to close TCP thread
def on_key_close_tcp(event):
	global tcp_loop
	tcp_loop = False

#fig.canvas.mpl_disconnect(fig.canvas.manager.key_press_handler_id)
fig.canvas.mpl_connect('key_press_event', on_key_close_tcp)
timer = fig.canvas.new_timer(interval=100)
timer.add_callback(timer_callback, ax)
timer.start()

plt.show()

tcp_loop = False
