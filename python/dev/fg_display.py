#!/usr/bin/env python

import socket, struct, time, math, errno
import fgFDM
import fgCNTRL

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



def ft2m(x):
    return x * 0.3048

def m2ft(x):
    return x / 0.3048

def kt2mps(x):
    return x * 0.514444444

def mps2kt(x):
    return x / 0.514444444
    
def interpret_address(addrstr):
    '''interpret a IP:port string'''
    a = addrstr.split(':')
    a[1] = int(a[1])
    return tuple(a)

udp = udp_socket("127.0.0.1:5502")
#fgout = udp_socket("127.0.0.1:5503", input=True)
fgcntrin = udp_socket("127.0.0.1:5505")
#fgcntrout = udp_socket("127.0.0.1:5504")
#print interpret_address("127.0.0.1:5504")
cnt_out = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
cnt_out.connect(interpret_address("127.0.0.1:5504"))
cnt_out.setblocking(0)


tlast = time.time()
count = 0

fg = fgFDM.fgFDM()
cnt = fgCNTRL.fgCNTRL()

while True:
    buf = udp.recv(1000)
    cntlbuf = fgcntrin.recv(1000)
    fg.parse(buf)
    #fgout.write(fg.pack())
    cnt.parse(cntlbuf)
    #cnt_out.send(cnt.pack())
    count += 1
    if time.time() - tlast > 0.02:
        #print("%u FPS len=%u" % (count, len(cntlbuf)))
        count = 0
        tlast = time.time()
        print tlast, fg.get('theta', units='degrees'), ",", math.sqrt(fg.get('v_north', units='mps')**2 + fg.get('v_east', units='mps')**2)
        
        
        
        #print fg.get('alpha', units='degrees'),fg.get('v_wind_body_down', units='mps'),fg.get('v_down', units='mps')
        #print (fg.get('v_north', units='mps'),fg.get('v_east', units='mps'),fg.get('v_down', units='mps'))
        #print (fg.get('v_wind_body_north', units='mps'),fg.get('v_wind_body_east', units='mps'),fg.get('v_wind_body_down', units='mps'))
        
        '''fg.get('latitude', units='degrees'),
        fg.get('longitude', units='degrees'),
        fg.get('altitude', units='meters'),
        fg.get('vcas', units='mps'),'''
              #fg.get('A_Z_pilot', units='mpss'))
              #cnt.get('wind_dir_deg'))
        '''print (cnt.get('elevator'),
               cnt.get('aileron'),
               cnt.get('rudder'))'''
              

