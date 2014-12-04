#!/usr/bin/env python

from pylab import *
import socket
import time
import threading
import json
from collections import deque
from glider_icon import *
import helper
from ip_list import *

#init plot
fig = plt.figure()
gs = GridSpec(3, 2)
ax = plt.subplot(gs[:, 0])
ax1 = plt.subplot(gs[0, 1])
ax2 = plt.subplot(gs[1, 1])
ax3 = plt.subplot(gs[2, 1])
plt.tight_layout()
ax.axis('equal')
ax.set_xlim(-1000, 1000)
ax.set_ylim(-1000, 1000)

#plot thermal
# xx, yy = meshgrid(linspace(-500,500,50), linspace(-500,500,50))
# zz = zeros(xx.shape)
# for i in range(xx.shape[0]):
#     for j in range(xx.shape[1]):
#         zz[i,j] = sqrt(xx[i,j]**2+yy[i,j]**2)
# theCM = cm.get_cmap('bone')
# theCM._init()
# alphas = (linspace(1.0, -0.4, theCM.N))
# alphas[alphas<0] = 0
# theCM._lut[:-3,-1] = alphas
#ax.pcolor(xx,yy,zz,cmap=theCM)
thermal_circle1 = plt.Circle((0,0), 400, color='0.1', alpha=0.1)
thermal_circle2 = plt.Circle((0,0), 200, color='0.1', alpha=0.1)
ax.add_artist(thermal_circle1)
ax.add_artist(thermal_circle2)

#init glider icon
bp, lwp, rwp, ltp, rtp, vp, tp = addAndGetGliderIcon(ax, 0,0,0,0,0)

#init glider trail
trail_len = 50000
trail_x = deque(maxlen=trail_len)
trail_y = deque(maxlen=trail_len)
trail, = ax.plot([0.0], [0.0], color='r', linewidth=2)

#init glider properties
glider_x = 0
glider_y = 0
glider_heading = 0
glider_roll = 0
glider_altitiude = 0
glider_center = True
glider_vdown = 0

#init tape
tape_count = 0
prev_tape_count = 0
tape_x = None
tape_y = None
tape, = ax.plot([0.0], [0.0], 'b--', linewidth=3)
ax.grid()
#init old tape 1
old_tape_x = None
old_tape_y = None
old_tape, = ax.plot([0.0], [0.0], 'b--', linewidth=3, alpha=0.4)

#init old tape 2
old2_tape_x = None
old2_tape_y = None
old2_tape, = ax.plot([0.0], [0.0], 'b--', linewidth=3, alpha=0.2)

#init altitude graph
alt_len = 200
alt_val = deque(maxlen=alt_len)
alt, = ax1.plot([0.0], [0.0], color='b', linewidth=3)
ax1.set_ylabel('altitude (m)')
ax1.set_xlim(0,alt_len)
ax1.grid()

#init phi graph
phi_len = 200
phi_val = deque(maxlen=phi_len)
phi, = ax2.plot([0.0], [0.0], color='r', linewidth=3)
phi_des_val = deque(maxlen=phi_len)
phi_des, = ax2.plot([0.0], [0.0], 'b--', linewidth=3)
ax2.set_ylabel('roll controller with\n feedforward prediction (degrees)')
ax2.set_xlim(0,phi_len)
ax2.set_ylim(-70,70)
ax2.grid()

#init vdown graph
vdown_len = 200
vdown_val = deque(maxlen=vdown_len)
vdown, = ax3.plot([0.0], [0.0], color='b', linewidth=3)
ax3.set_ylabel('CLIMB RATE (m/s)')
ax3.set_xlabel('most recent ' + str(vdown_len) + ' samples')
ax3.set_xlim(0,vdown_len)
ax3.set_ylim(-5,5)
ax3.grid()

#init wall
curwallleft, = ax.plot([0.0, 10.0], [0.0, 10.0], color='g', linewidth=2)
curwallright, = ax.plot([0.0, 10.0], [0.0, 10.0], color='c', linewidth=2)
triggerwall, = ax.plot([0.0, 10.0], [0.0, 10.0], color='m', linewidth=2)

#init tcp connection
tcp_ip = vis_ip
tcp_port = vis_port
buffer_size = 2*4096
tcp_loop = True

#init tcp data
tcp_dict = None
data_init = False
tape_init = False
glider_data = None
tape_data = None
glider_error = None
cur_wpt_x = 0
cur_wpt_y = 0
nxt_wpt_x = 0
nxt_wpt_y = 0
wall_l_x = 0
wall_l_y = 0
wall_r_x = 0
wall_r_y = 0
trigger_wall_l_x = 0
trigger_wall_l_y = 0
trigger_wall_r_x = 0
trigger_wall_r_y = 0
dist_from_line = 0
dist_from_wall = 0
desired_phi = 0
desired_phi_tape = 0


#thread for handling incoming TCP data
def tcpThread():
	global glider_data, tape_data, tcp_dict, data_init, tape_init, tape_x, tape_y, glider_x, glider_y, glider_heading, glider_roll, glider_altitiude, desired_phi, desired_phi_tape
	global cur_wpt_x, cur_wpt_y, nxt_wpt_x, nxt_wpt_y, wall_l_x, wall_l_y, wall_r_x, wall_r_y, dist_from_line, dist_from_wall, tape_count, glider_vdown, prev_tape_count
	global old_tape_x, old_tape_y, old2_tape_x, old2_tape_y, trigger_wall_l_x, trigger_wall_l_y, trigger_wall_r_x, trigger_wall_r_y
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
				tape_count = tape_data['count']
				if prev_tape_count != tape_count:
					prev_tape_count = tape_count
					if tape_count > 1:
						old2_tape_x = old_tape_x
						old2_tape_y = old_tape_y
					if tape_count > 0:
						old_tape_x = tape_x
						old_tape_y = tape_y
				tape_x = [item for sublist in tape_data['x'] for item in sublist]
				tape_y = [item for sublist in tape_data['y'] for item in sublist]
				cur_wpt_x = tape_data['CUR_WPT'][0]
				cur_wpt_y = tape_data['CUR_WPT'][1]
				nxt_wpt_x = tape_data['NXT_WPT'][0]
				nxt_wpt_y = tape_data['NXT_WPT'][1]
				wall_l_x = tape_data['WALL_LEFT'][0]
				wall_l_y = tape_data['WALL_LEFT'][1]
				wall_r_x = tape_data['WALL_RIGHT'][0]
				wall_r_y = tape_data['WALL_RIGHT'][1]
				trigger_wall_l_x = tape_data['TRIGGER_WALL_LEFT'][0]
				trigger_wall_l_y = tape_data['TRIGGER_WALL_LEFT'][1]
				trigger_wall_r_x = tape_data['TRIGGER_WALL_RIGHT'][0]
				trigger_wall_r_y = tape_data['TRIGGER_WALL_RIGHT'][1]
				dist_from_line = tape_data['DIST_FROM_LINE']
				dist_from_wall = tape_data['DIST_FROM_WALL']
				desired_phi = tape_data['DESIRED_PHI']
				desired_phi_tape = tape_data['DESIRED_PHI_TAPE']
			elif channel == "GLIDER_STATE":
				if not data_init:
					data_init = True
				glider_data = tcp_dict
				#glider_x, glider_y = lla2flatearth(glider_data['LAT'], glider_data['LON'])
				glider_x, glider_y = helper.lla2flatearth(glider_data['LAT'], glider_data['LON'])
				glider_heading = glider_data["HEADING"]*180/math.pi
				glider_roll = glider_data["PHI"]*180/math.pi
				glider_altitiude = glider_data["ALT"]
				glider_vdown = glider_data["V_DOWN"]
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
		old_tape.set_xdata(old_tape_x)
		old_tape.set_ydata(old_tape_y)
		old2_tape.set_xdata(old2_tape_x)
		old2_tape.set_ydata(old2_tape_y)

	trail_x.append(glider_x)
	trail_y.append(glider_y)
	trail.set_xdata(trail_x)
	trail.set_ydata(trail_y)

	alt_val.append(glider_altitiude)
	alt.set_xdata(linspace(0,alt_len,len(alt_val)))
	alt.set_ydata(alt_val)
	ax1.relim()
	ax1.autoscale_view(scalex=False, scaley=True)

	phi_val.append(desired_phi)
	phi.set_xdata(linspace(0,phi_len,len(phi_val)))
	phi.set_ydata(phi_val)
	phi_des_val.append(desired_phi_tape)
	phi_des.set_xdata(linspace(0,phi_len,len(phi_des_val)))
	phi_des.set_ydata(phi_des_val)

	vdown_val.append(-glider_vdown)
	vdown.set_xdata(linspace(0,vdown_len,len(vdown_val)))
	vdown.set_ydata(vdown_val)
	if glider_vdown < 0:
		vdown.set_color('g')
	else:
		vdown.set_color('r')

	curwallleft.set_xdata([nxt_wpt_x, wall_l_x])
	curwallleft.set_ydata([nxt_wpt_y, wall_l_y])
	curwallright.set_xdata([nxt_wpt_x, wall_r_x])
	curwallright.set_ydata([nxt_wpt_y, wall_r_y])
	triggerwall.set_xdata([trigger_wall_l_x, trigger_wall_r_x])
	triggerwall.set_ydata([trigger_wall_l_y, trigger_wall_r_y])

	bp.remove()
	lwp.remove()
	rwp.remove()
	ltp.remove()
	rtp.remove()
	vp.remove()
	tp.remove()
	bp, lwp, rwp, ltp, rtp, vp, tp = addAndGetGliderIcon(ax, glider_x, glider_y, glider_heading, glider_roll, 3.5)

	if glider_center:
		#center on glider
		xmin, xmax = ax.get_xlim()
		ymin, ymax = ax.get_ylim()
		width = abs(xmax-xmin) 
		height = abs(ymax-ymin)
		ax.set_xlim(glider_x-width/2, glider_x+width/2)
		ax.set_ylim(glider_y-height/2, glider_y+height/2)
		ax1.relim()

	fig.canvas.draw()

#key callback to close TCP thread
def on_key_close_tcp(event):
	if event.key == 'q':
		global tcp_loop
		tcp_loop = False
	elif event.key == 'c':
		global glider_center
		if glider_center:
			glider_center = False
		else:
			glider_center = True

#fig.canvas.mpl_disconnect(fig.canvas.manager.key_press_handler_id)
fig.canvas.mpl_connect('key_press_event', on_key_close_tcp)
timer = fig.canvas.new_timer(interval=50)
timer.add_callback(timer_callback, ax)
timer.start()

plt.show()

tcp_loop = False
