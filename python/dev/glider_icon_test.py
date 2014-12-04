#!/usr/bin/env python

# start in non-inline mode, so we can use interactive plots
from pylab import *

import sys
import math
import numpy as np
from matplotlib.patches import PathPatch
from matplotlib.path import Path
from matplotlib.transforms import Affine2D

def heading2XY(h):
	e = -(h-90.0)
	if e <= -180.0:
		e = e + 360.0
	return e

def addAndGetGliderIcon(ax, x, y, heading, roll, altitude):
	roll_scale = abs(roll)
	if roll_scale > 90:
		roll_scale = 90
	roll_scale = abs(roll_scale-90)/90.

	if roll < 0:
		roll_side = 1 #left roll
	else:
		roll_side = -1 #right roll

	trans_mat = Affine2D()
	trans_mat.rotate_deg(90+heading2XY(heading))
	trans_mat.translate(x,y)

	glider_body = np.matrix([[-0.4, -9],[0, -9.8],[0.4, -9],[1.2, -7.5],[1.2, -6],[1.2, 3],[1.2, 8],[0, 17],[-1.2, 8],[-1.2, 3],[-1.2, -6],[-1.2, -7.5],[-0.4, -9]])
	glider_body_codes = [1, 3, 2, 3, 2, 2, 3, 2, 3, 2, 2, 3, 2]
	glider_body_path = Path(glider_body, glider_body_codes)
	glider_body_patch = PathPatch(glider_body_path, facecolor=(0.7, 0.7, 0.7), edgecolor=(0.2, 0.2, 0.45))
	glider_body_patch.set_transform(trans_mat + ax.transData)

	move = (1-roll_scale)*roll_side

	if roll_side < 0:
		leftw_bp = [roll_scale*27.2, -3+5*-move]
		leftw_fp1 = [roll_scale*26.2, -5+2*-move]
		leftw_fp2 = [roll_scale*27.2, -5+2*-move]
		color = (0.7+0.3*(1-roll_scale), 0.7+0.3*(1-roll_scale), 0.7+0.3*(1-roll_scale))
	else:
		leftw_bp = [roll_scale*27.2, -3+1.5*move]
		leftw_fp1 = [roll_scale*26.2, -5+3*move]
		leftw_fp2 = [roll_scale*27.2, -5+3*move]
		color = (0.7-0.3*(1-roll_scale), 0.7-0.3*(1-roll_scale), 0.7-0.3*(1-roll_scale))
	leftw_tran = [-1*(1-roll_scale), 0] 
	glider_leftw = np.matrix([[1.2, -3],[2.2, -3],leftw_fp1,leftw_fp2,leftw_bp,[3.2, 1],[2.2, 1],[1.2, 2],[1.2, -3]])
	glider_leftw[:,0] = glider_leftw[:,0] + leftw_tran[0]
	glider_leftw_codes = [1, 2, 2, 3, 2, 2, 3, 2, 2]
	glider_leftw_path = Path(glider_leftw, glider_leftw_codes)
	glider_leftw_patch = PathPatch(glider_leftw_path, facecolor=color, edgecolor=(0.2, 0.2, 0.45))
	glider_leftw_patch.set_transform(trans_mat + ax.transData)

	if roll_side > 0:
		rightw_bp = [roll_scale*-27.2, -3+5*move]
		rightw_fp1 = [roll_scale*-26.2, -5+2*move]
		rightw_fp2 = [roll_scale*-27.2, -5+2*move]
		color = (0.7-0.3*(1-roll_scale), 0.7-0.3*(1-roll_scale), 0.7-0.3*(1-roll_scale))
	else:
		rightw_bp = [roll_scale*-27.2, -3+1.5*-move]
		rightw_fp1 = [roll_scale*-26.2, -5+3*-move]
		rightw_fp2 = [roll_scale*-27.2, -5+3*-move]
		color = (0.7+0.3*(1-roll_scale), 0.7+0.3*(1-roll_scale), 0.7+0.3*(1-roll_scale))
	rightw_tran = [1*(1-roll_scale), 0] 
	glider_rightw = np.matrix([[-1.2, -3],[-2.2, -3],rightw_fp1,rightw_fp2,rightw_bp,[-3.2, 1],[-2.2, 1],[-1.2, 2],[-1.2, -3]])
	glider_rightw[:,0] = glider_rightw[:,0] + rightw_tran[0]
	glider_rightw_codes = [1, 2, 2, 3, 2, 2, 3, 2, 2]
	glider_rightw_path = Path(glider_rightw, glider_rightw_codes)
	glider_rightw_patch = PathPatch(glider_rightw_path, facecolor=color, edgecolor=(0.2, 0.2, 0.45))
	glider_rightw_patch.set_transform(trans_mat + ax.transData)

	if roll_side < 0:
		leftt_bp = [roll_scale*5, 14.5+4*-move]
		leftt_fp = [roll_scale*5, 13+2*-move]
		color = (0.7+0.3*(1-roll_scale), 0.7+0.3*(1-roll_scale), 0.7+0.3*(1-roll_scale))
		leftt_tran = [-0.7*(1-roll_scale), 0] 
	else:
		leftt_bp = [roll_scale*5, 14.5+1.5*move]
		leftt_fp = [roll_scale*5, 13+2*move]
		color = (0.7-0.3*(1-roll_scale), 0.7-0.3*(1-roll_scale), 0.7-0.3*(1-roll_scale))
		leftt_tran = [0.7*(1-roll_scale), 0] 
	glider_leftt = np.matrix([[0, 12],leftt_fp,leftt_bp,[0.5, 15],[0.5, 14],[0, 14],[0, 12]])
	glider_leftt[:,0] = glider_leftt[:,0] + leftt_tran[0]
	glider_leftt_codes = [1, 2, 2, 2, 3, 2, 2]
	glider_leftt_path = Path(glider_leftt, glider_leftt_codes)
	glider_leftt_patch = PathPatch(glider_leftt_path, facecolor=color, edgecolor=(0.2, 0.2, 0.45))
	glider_leftt_patch.set_transform(trans_mat + ax.transData)

	if roll_side > 0:
		rightt_bp = [roll_scale*-5, 14.5+4*move]
		rightt_fp = [roll_scale*-5, 13+2*move]
		color = (0.7-0.3*(1-roll_scale), 0.7-0.3*(1-roll_scale), 0.7-0.3*(1-roll_scale))
		rightt_tran = [0.7*(1-roll_scale), 0] 
	else:
		rightt_bp = [roll_scale*-5, 14.5+1.5*-move]
		rightt_fp = [roll_scale*-5, 13+2*-move]
		color = (0.7+0.3*(1-roll_scale), 0.7+0.3*(1-roll_scale), 0.7+0.3*(1-roll_scale))
		rightt_tran = [-0.7*(1-roll_scale), 0] 
	glider_rightt = np.matrix([[0, 12],rightt_fp,rightt_bp,[-0.5, 15],[-0.5, 14],[0, 14],[0, 12]])
	glider_rightt[:,0] = glider_rightt[:,0] + rightt_tran[0]
	glider_rightt_codes = [1, 2, 2, 2, 3, 2, 2]
	glider_rightt_path = Path(glider_rightt, glider_rightt_codes)
	glider_rightt_patch = PathPatch(glider_rightt_path, facecolor=color, edgecolor=(0.2, 0.2, 0.45))
	glider_rightt_patch.set_transform(trans_mat + ax.transData)

	if roll_side > 0:
		right_vpf = [-1.2*roll_scale, -6]
		right_vpb = [-1.2*roll_scale, -1.5]
		left_vpf = [1.2, -6]
		left_vpb = [1.2, -1.5]
	else:
		right_vpf = [-1.2, -6]
		right_vpb = [-1.2, -1.5]
		left_vpf = [1.2*roll_scale, -6]
		left_vpb = [1.2*roll_scale, -1.5]
	glider_visor = np.matrix([left_vpf,left_vpb,[0, -1],right_vpb,right_vpf,[0, -8],left_vpf])
	glider_visor_codes = [1, 2, 3, 2, 2, 3, 2]
	glider_visor_path = Path(glider_visor, glider_visor_codes)
	glider_visor_patch = PathPatch(glider_visor_path, facecolor=(0.1, 0.1, 0.1), edgecolor=(0.2, 0.2, 0.45))
	glider_visor_patch.set_transform(trans_mat + ax.transData)

	if roll_side > 0:
		t_bp = [0+4*(1-roll_scale), 16.3]
		t_fp = [0+4*(1-roll_scale), 15]
		t_tran = [0.7*(1-roll_scale), 0]
		color = (0.7+0.3*(1-roll_scale), 0.7+0.3*(1-roll_scale), 0.7+0.3*(1-roll_scale))
	else:
		t_bp = [0-4*(1-roll_scale), 16]
		t_fp = [0-4*(1-roll_scale), 15]
		t_tran = [0.7*-(1-roll_scale), 0]
		color = (0.7-0.3*(1-roll_scale), 0.7-0.3*(1-roll_scale), 0.7-0.3*(1-roll_scale))
	glider_t = np.matrix([[0, 14],t_fp,t_bp,[0, 16],[0 ,14]])
	glider_t[:,0] = glider_t[:,0] + t_tran[0]
	glider_t[3,0] = 0
	glider_t_codes = [1, 2, 2, 2, 2]
	glider_t_path = Path(glider_t, glider_t_codes)
	glider_t_patch = PathPatch(glider_t_path, facecolor=color, edgecolor=(0.2, 0.2, 0.45))
	glider_t_patch.set_transform(trans_mat + ax.transData)

	if roll_side < 0:
		ax.add_patch(glider_rightw_patch)
		ax.add_patch(glider_body_patch)
		ax.add_patch(glider_visor_patch)
		ax.add_patch(glider_leftw_patch)
	else:
		ax.add_patch(glider_leftw_patch)
		ax.add_patch(glider_body_patch)
		ax.add_patch(glider_visor_patch)
		ax.add_patch(glider_rightw_patch)
	ax.add_patch(glider_leftt_patch)
	ax.add_patch(glider_rightt_patch)
	ax.add_patch(glider_t_patch)
	return glider_body_patch, glider_leftw_patch, glider_rightw_patch, glider_leftt_patch, glider_rightt_patch, glider_visor_patch, glider_t_patch






from collections import deque

fig = plt.figure()
gs = GridSpec(3, 2)
ax = plt.subplot(gs[:, 0])
ax1 = plt.subplot(gs[0, 1])
ax2 = plt.subplot(gs[1, 1])
ax3 = plt.subplot(gs[2, 1])
plt.tight_layout()

ax.axis('equal')

bp, lwp, rwp, ltp, rtp, vp, tp = addAndGetGliderIcon(ax, 0,0,0,0,0)

trail_len = 1000
trail_x = deque(maxlen=trail_len)
trail_y = deque(maxlen=trail_len)
trail, = ax.plot([0.0], [0.0], color='m', linewidth=2)

# xx, yy = meshgrid(linspace(-150,150,50), linspace(-150,150,50))
# zz = zeros(xx.shape)
# for i in range(xx.shape[0]):
#     for j in range(xx.shape[1]):
#         zz[i,j] = sqrt(xx[i,j]**2+yy[i,j]**2)

# theCM = cm.get_cmap('bone')
# theCM._init()
# alphas = (linspace(1.0, -0.4, theCM.N))
# alphas[alphas<0] = 0
# theCM._lut[:-3,-1] = alphas

# # plot the calculated function values
# ax.pcolor(xx,yy,zz,cmap=theCM)
thermal_circle1 = plt.Circle((0,0), 1000, color='0.1', alpha=0.1)
thermal_circle2 = plt.Circle((0,0), 900, color='0.1', alpha=0.1)
thermal_circle3 = plt.Circle((0,0), 800, color='0.1', alpha=0.1)
thermal_circle4 = plt.Circle((0,0), 700, color='0.1', alpha=0.1)
thermal_circle5 = plt.Circle((0,0), 600, color='0.1', alpha=0.1)
ax.add_artist(thermal_circle1)
ax.add_artist(thermal_circle2)
ax.add_artist(thermal_circle3)
ax.add_artist(thermal_circle4)
ax.add_artist(thermal_circle5)

x = 0
y = 0
heading = 0
roll = 0
altitiude = 0

def on_key_press(event):
	global bp, lwp, rwp, ltp, rtp, vp, tp, x, y, heading, roll, altitude, ax

	if event.key == 'left':
		heading = (heading - 1)%360
		x = x + math.cos(heading2XY(heading)*math.pi/180)
		y = y + math.sin(heading2XY(heading)*math.pi/180)
	if event.key == 'right':
		heading = (heading + 1)%360
		x = x + math.cos(heading2XY(heading)*math.pi/180)
		y = y + math.sin(heading2XY(heading)*math.pi/180)
	#print "HEADING:", heading
	if event.key == 'up':
		x = x + cos(heading2XY(heading)*math.pi/180)
		y = y + sin(heading2XY(heading)*math.pi/180)
	if event.key == 'down':
		x = x - cos(heading2XY(heading)*math.pi/180)
		y = y - sin(heading2XY(heading)*math.pi/180)
	#print "X,Y:",x,",",y
	if event.key == 'a':
		roll = (roll - 1)
	if event.key == 'd':
		roll = (roll + 1)
	#print "ROLL:", roll

	trail_x.append(x)
	trail_y.append(y)
	trail.set_xdata(trail_x)
	trail.set_ydata(trail_y)

	xmin, xmax = ax.get_xlim()
	ymin, ymax = ax.get_ylim()
	width = abs(xmax-xmin) 
	height = abs(ymax-ymin)
	ax.set_xlim(x-width/2, x+width/2)
	ax.set_ylim(y-height/2, y+height/2)

	bp.remove()
	lwp.remove()
	rwp.remove()
	ltp.remove()
	rtp.remove()
	vp.remove()
	tp.remove()
	bp, lwp, rwp, ltp, rtp, vp, tp = addAndGetGliderIcon(ax,x,y,heading,roll,0)
	fig.canvas.draw()

#fig.canvas.mpl_disconnect(fig.canvas.manager.key_press_handler_id)
fig.canvas.mpl_connect('key_press_event', on_key_press)

plt.show()
