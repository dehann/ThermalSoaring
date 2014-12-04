#!/usr/bin/env python
# parse and construct FlightGear NET CNTRL packets

import struct, math

class fgCNTRLError(Exception):
    '''fgCNTRL error class'''
    def __init__(self, msg):  
        Exception.__init__(self, msg)
        self.message = 'fgCNTRLError: ' + msg

class fgCNTRLVariable(object):
    '''represent a single fgCNTRL variable'''
    def __init__(self, index, arraylength, units):
        self.index   = index
        self.arraylength = arraylength
        self.units = units

class fgCNTRLVariableList(object):
    '''represent a list of fgCNTRL variable'''
    def __init__(self):
        self.vars = {}
        self._nextidx = 0
        
    def add(self, varname, arraylength=1, units=None):
        self.vars[varname] = fgCNTRLVariable(self._nextidx, arraylength, units=units)
        self._nextidx += arraylength

'''enum {
        FG_MAX_ENGINES = 4,
        FG_MAX_WHEELS = 16,
        FG_MAX_TANKS = 8
    };'''
    
class fgCNTRL(object):
  '''a flightgear native CNTRL parser/generator'''
  def __init__(self):
    self.FG_NET_CNTRL_VERSION = 27
    self.pack_string = '>I 4x 9d 2I I 16I 12d 4I 4d 8I 24I I 8I 5I I 5d 2I 4d 3d 2d 2d I 2I 108x'
    self.values = [0]*142
    self.FG_MAX_ENGINES = 4
    self.FG_MAX_WHEELS  = 16
    self.FG_MAX_TANKS   = 8
    self.RESERVED_SPACE = 25
    
    # supported unit mappings
    self.unitmap = {
        ('radians', 'degrees') : math.degrees(1),
        ('rps',     'dps')     : math.degrees(1),
        ('feet',    'meters')  : 0.3048,
        ('fps',     'mps')     : 0.3048,
        ('knots',   'mps')     : 0.514444444,
        ('knots',   'fps')     : 0.514444444/0.3048,
        ('fpss',    'mpss')    : 0.3048,
        ('seconds', 'minutes') : 60,
        ('seconds', 'hours')   : 3600,
        }
        
    # build a mapping between variable name and index in the values array
    # note that the order of this initialisation is critical - it must
    # match the wire structure
    self.mapping = fgCNTRLVariableList()
    self.mapping.add('version')

    # Aero controls
    self.mapping.add('aileron')	# [-1..1]
    self.mapping.add('elevator')
    self.mapping.add('rudder')
    self.mapping.add('aileron_trim')
    self.mapping.add('elevator_trim')
    self.mapping.add('rudder_trim')
    self.mapping.add('flaps')
    self.mapping.add('spoilers')
    self.mapping.add('speedbrake')
    
    # Aero control faults
    self.mapping.add('flaps_power') # true = power available
    self.mapping.add('flap_motor_ok')

    # Engine controls
    self.mapping.add('num_engines')
    self.mapping.add('master_bat', self.FG_MAX_ENGINES)
    self.mapping.add('master_alt', self.FG_MAX_ENGINES)
    self.mapping.add('magnetos', self.FG_MAX_ENGINES)
    self.mapping.add('starter_power', self.FG_MAX_ENGINES)
    self.mapping.add('throttle', self.FG_MAX_ENGINES)
    self.mapping.add('mixture', self.FG_MAX_ENGINES)
    self.mapping.add('condition', self.FG_MAX_ENGINES)
    self.mapping.add('fuel_pump_power', self.FG_MAX_ENGINES)
    self.mapping.add('prop_advance', self.FG_MAX_ENGINES)
    self.mapping.add('feed_tank_to', 4)
    self.mapping.add('reverse', self.FG_MAX_ENGINES)

    # Engine faults
    self.mapping.add('engine_ok', self.FG_MAX_ENGINES)
    self.mapping.add('mag_left_ok', self.FG_MAX_ENGINES)
    self.mapping.add('mag_right_ok', self.FG_MAX_ENGINES)
    self.mapping.add('spark_plugs_ok', self.FG_MAX_ENGINES)
    self.mapping.add('oil_press_status', self.FG_MAX_ENGINES)
    self.mapping.add('fuel_pump_ok', self.FG_MAX_ENGINES)

    # Fuel management
    self.mapping.add('num_tanks')
    self.mapping.add('fuel_selector', self.FG_MAX_TANKS)
    self.mapping.add('xfer_pump', 5)
    self.mapping.add('cross_feed')

    # Brake controls
    self.mapping.add('brake_left')
    self.mapping.add('brake_right')
    self.mapping.add('copilot_brake_left')
    self.mapping.add('copilot_brake_right')
    self.mapping.add('brake_parking')
    
    # Landing Gear
    self.mapping.add('gear_handle')

    # Switches
    self.mapping.add('master_avionics')
    
    # nav and Comm
    self.mapping.add('comm_1')
    self.mapping.add('comm_2')
    self.mapping.add('nav_1')
    self.mapping.add('nav_2')
    
    # wind and turbulance
    self.mapping.add('wind_speed_kt')
    self.mapping.add('wind_dir_deg')
    self.mapping.add('turbulence_norm')
    
    # temp and pressure
    self.mapping.add('temp_c')
    self.mapping.add('press_inhg')
    
    # other information about environment
    self.mapping.add('hground')
    self.mapping.add('magvar')

    # hazards
    self.mapping.add('icing')

    # simulation control
    self.mapping.add('speedup')
    self.mapping.add('freeze')
    
    # --- New since FlightGear 0.9.10 (FG_NET_CTRLS_VERSION = 27)
    # --- Add new variables just before this line.
    self.mapping.add('reserved', self.RESERVED_SPACE)
    
    self._packet_size = 744 #struct.calcsize(self.pack_string)

    self.set('version', self.FG_NET_CNTRL_VERSION)
      
    #print self.mapping._nextidx
    #print len(self.values)
    if len(self.values) != self.mapping._nextidx:
      raise fgCNTRLError('Invalid variable list in initialisation')
    
    
  def set(self, varname, value, idx=0, units=None):
    '''set a variable value'''
    if not varname in self.mapping.vars:
        raise fgCNTRLError('Unknown variable %s' % varname)
    if idx >= self.mapping.vars[varname].arraylength:
        raise fgCNTRLError('index of %s beyond end of array idx=%u arraylength=%u' % (
            varname, idx, self.mapping.vars[varname].arraylength))
    if units:
        value = self.convert(value, units, self.mapping.vars[varname].units)
    # avoid range errors when packing into 4 byte floats
    if math.isinf(value) or math.isnan(value) or math.fabs(value) > 3.4e38:
        value = 0
    self.values[self.mapping.vars[varname].index + idx] = value    
    
  def packet_size(self):
    '''return expected size of FG CNTRL packets'''
    return self._packet_size
  
  def convert(self, value, fromunits, tounits):
    '''convert a value from one set of units to another'''
    if fromunits == tounits:
        return value
    if (fromunits,tounits) in self.unitmap:
        return value * self.unitmap[(fromunits,tounits)]
    if (tounits,fromunits) in self.unitmap:
        return value / self.unitmap[(tounits,fromunits)]
    raise fgCNTRLError("unknown unit mapping (%s,%s)" % (fromunits, tounits))      
  
  def units(self, varname):
    '''return the default units of a variable'''
    if not varname in self.mapping.vars:
        raise fgCNTRLError('Unknown variable %s' % varname)
    return self.mapping.vars[varname].units

  def variables(self):
    '''return a list of available variables'''
    return sorted(self.mapping.vars.keys(),
                  key = lambda v : self.mapping.vars[v].index)
  
  def get(self, varname, idx=0, units=None):
    '''get a variable value'''
    if not varname in self.mapping.vars:
      raise fgCNTRLError('Unknown variable %s' % varname)
    if idx >= self.mapping.vars[varname].arraylength:
      raise fgCNTRLError('index of %s beyond end of array idx=%u arraylength=%u' % (
          varname, idx, self.mapping.vars[varname].arraylength))
    value = self.values[self.mapping.vars[varname].index + idx]
    if units:
      value = self.convert(value, self.mapping.vars[varname].units, units)
    return value
  
  def parse(self, buf):
    #print 'length is',len(buf)
    '''parse a FG CNTRL buffer'''
    try:
      t = struct.unpack(self.pack_string, buf)
    except struct.error, msg:
      raise fgCNTRLError('unable to parse - %s' % msg)
    self.values = list(t)
  
  def pack(self):
    '''pack a FD CNTRL buffer from current values'''
    for i in range(len(self.values)):
      if math.isnan(self.values[i]):
        self.values[i] = 0
    return struct.pack(self.pack_string, *self.values)
      
