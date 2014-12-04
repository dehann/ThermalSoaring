#!/usr/bin/env python

#Import Module Statements
import math
import re
import copy

'''This module contains a number of helper functions related to the calculation
and conversion of Latitudes and Longitudes. This includes conversion between
LAT/LON and milliarcseconds, new LAT/LON points given an offset from a known
LAT/LON point, and angles and distances between LAT/LON points. Functions for
Earth radius of curvatures along Normal and Meridian are also included, to all-
ow Longitudanal changes with Latitude to be correctly adjusted, as well as to
correctly place circles (by adjustment into ellipses) on a LAT/LON grid. Final-
ly, it also contains a custom Point class, to create point objects (x,y,z,
etc.).
Nick Rypkema - 06/2011 - DSTO Sydney
'''

class Point:
    '''Class that contains position information for waypoints and vehicle loca-
    tions, as well as speeds.
    '''
    def __init__(self, x=None, y=None, d=None, a=None, h=None, s=None,
           form=None):
        self.x = x              #x position in milliarcseconds (Longitude)
        self.y = y              #y position in milliarcseconds (Latitude)
        if d != None and a != None:
            self.d = d
            self.a = None
        else:
            self.d = d          #depth from water surface in meters
            self.a = a          #altitude from seafloor in meters
        self.h = h              #heading in radians
        self.s = s              #speed in knots
        if form == None or (form == 'dubins' and h == None):
            self.form = 'transit'
        else:
            self.form = form    #type of waypoint (trackline, transit, dubins)
    def __str__(self):
        return ('('+str(self.x)+','+str(self.y)+','+str(self.d)+'m,'
                +str(self.a)+'m,'+str(self.h)+'^,'+self.form+')')

def lla2flatearth(lat, lon):
    Tlat = 37.61633
    Tlon = -122.38334
    #print "_______", lat*180.0/math.pi, lon*180.0/math.pi
    dx, headx = distanceHeading(Tlat*3600000, Tlon*3600000, Tlat*3600000, lon*180.0/math.pi*3600000)
    dy, heady = distanceHeading(Tlat*3600000, Tlon*3600000, lat*180.0/math.pi*3600000, Tlon*3600000)
    if (headx*180.0/math.pi > 180):
        dx = -dx
    if (heady*180.0/math.pi > 90) and (heady*180.0/math.pi < 270):
        dy = -dy
    #print "DX, HEADX, DY, HEADY", dx, headx*180.0/math.pi, dy, heady*180.0/math.pi
    return dx, dy

def degMinToMas(degs_mins):
    '''Converts a Latitude or Longitude String to a milliarcseconds Float.
    :param verbose: 'degs_mins' must be a String of the form 100N50.500. Coord-
    inate system is such that degrees N and E returns a positive value (x and y
    assumed respectively) and degrees S and W returns a negative value. Returns
    a Float.
    '''
    degMinArray = re.split('[A-Z]+', degs_mins)
    #^ split input String to get numbers of degrees and minutes ^
    degrees = int(degMinArray[0])
    #^ degrees is always on integer ^
    minutes = float(degMinArray[1])
    if ('S' in degs_mins) or ('W' in degs_mins):
        return -(degrees*60*60*1000 + minutes*60*1000)
    return degrees*60*60*1000 + minutes*60*1000
    #^ calculate and return the number of milliarcseconds ^

def masToDegMin(mas,xy):
    '''Converts a milliarcseconds Float into a Latitude or Longitude String.
    :param verbose: 'mas' must be a Float, and 'xy' must be a String of the fo-
    rm 'x' or 'y' EXCLUSIVELY. This String indicates if the return is to be a
    Latitude String ('y' - vertical) or a Longitude String ('x' - horizontal).
    The sign of 'mas' determines the degrees direction, with a negative return-
    ing either N or W and positive either S or E. Returns a String with minute-
    s to 4 decimal places.
    '''
    if xy == 'x':
        if mas < 0:
            direction = 'W'
        else:
            direction = 'E'
    elif xy == 'y':
        if mas < 0:
            direction = 'S'
        else:
            direction = 'N'
    #^ determine axis and direction of input value ^
    mas = abs(mas)
    degrees = int(mas/(60*60*1000))
    remaining_mas = mas - (degrees*60*60*1000)
    minutes = remaining_mas/(60*1000)
    return str(degrees) + direction + '%.4f' % minutes
    #^ calculate Latitude or Longitude and format the return string with degre-
    #es to 4 decimal places ^

def masLatOffsetHeading(lat, meters, heading):
    '''Calculates a Latitude given an offset and heading from an intial Latitu-
    de.
    :param verbose: 'lat' must be a Float in milliarcseconds, 'meters' is the
    number of meters offset from 'lat', and 'heading' is the heading in degrees
    from 'lat'. Returns a Float representing a Latitude offset from 'lat'.
    '''
    angle = (360-heading)-270
    if angle < 0:
        angle += 360
    #^ convert from traditional ship heading to scientific angle format ^
    offset_y = math.sin(math.radians(angle))*meters
    #^ calculate the offset from 'lat' in Longitude using trig. sin(theta)=o/h.
    return masLatOffset(lat, offset_y)
    #^ calculate the offset, taking into account Earth ellipsoid ^

def masLonOffsetHeading(lat, meters, heading):
    '''Calculates a Longitude given an offset and heading from an intial Latit-
    ude.
    :param verbose: 'lat' must be a Float in milliarcseconds, 'meters' is the
    number of meters offset from 'lat', and 'heading' is the heading in degrees
    from 'lat'. Returns a Float representing a Longitude offset from 'lat'.
    '''
    angle = (360-heading)-270
    if angle < 0:
        angle += 360
    #^ convert from traditional ship heading to scientific angle format ^
    offset_x = math.cos(math.radians(angle))*meters
    #^ calculate the offset from 'lat' in Longitude using trig. cos(theta)=a/h.
    return masLonOffset(lat, offset_x)
    #^ calculate the offset, taking into account Earth ellipsoid ^
    
def masLatOffset(lat, meters):
    '''Calculates a Latitude given an offset from an initial Latitude.
    :param verbose: 'lat' must be a Float in milliarcseconds, and 'meters' is
    the number of meters offset from 'lat'. Returns a Float representing a
    Latitude offset in milliarcseconds from 'lat'.
    '''
    lat = lat/3600000
    #^ convert milliarcseconds to degrees ^
    RM = M(lat)
    #^ calculate Meridional radius of Earth ^
    return (3600000*meters)/((math.pi/180)*RM)
    #^ calculate the offset in milliarcseconds ^

def masLonOffset(lat, meters):
    '''Calculates a Longitude given an offset from an initial Latitude.
    :param verbose: 'lat' must be a Float in milliarcseconds, and 'meters' is
    the number of meters offset from 'lat'. Returns a Float representing a
    Longitude offset in milliarcseconds from 'lat'.
    '''
    lat = lat/3600000
    #^ convert milliarcseconds to degrees ^
    RN = N(lat)
    #^ calculate Normal radius of Earth ^
    return (3600000*meters)/((math.pi/180)*RN*math.cos(math.radians(lat)))
    #^ calculate the offset in milliarcseconds ^

def N(phi):
    '''Calculates the Normal radius of the Earth using an ellipsoidal model.
    :param verbose: 'phi' is a Float in degrees (usually a Latitude). Returns
    the radius of the Earth in the Normal at a specific angle (Latitude), if
    the Earth was a sphere.
    '''
    a = 6378137
    e = 0.08181919084
    return a/(1-(e**2)*(math.sin(math.radians(phi)))**2)**0.5
    #^ see 'Radius of the Earth - Radii used in Geodesy' by J.R.Clynch for in-
    #depth explanation ^

def M(phi):
    '''Calculates the Meridional radius of Earth using an ellipsoidal model.
    :param verbose: 'phi' is a Float in degrees (usually a Latitude). Returns
    the radius of the Earth in the Meridional at a specific angle (Latitude),
    if the Earth was a sphere.
    '''
    a = 6378137
    e = 0.08181919084
    return (a*(1-e**2))/(1-(e**2)*(math.sin(math.radians(phi)))**2)**1.5
    #^ see 'Radius of the Earth - Radii used in Geodesy' by J.R.Clynch for in-
    #depth explanation ^

def mDistance(lat1, lon1, lat2, lon2):
    '''Calculates the distance in meters between two LAT/LON points.
    :param verbose: 'lat1', 'lon1', 'lat2', 'lon2', are all in milliarcseconds.
    Returns the distance between ('lat1','lon1') and ('lat2','lon2') in meters.
    '''
    lat1 = lat1/3600000
    lon1 = lon1/3600000
    lat2 = lat2/3600000
    lon2 = lon2/3600000
    #^ convert from milliarcseconds to degrees ^
    RN = N(lat1)
    #^ calculate Normal radius of Earth ^
    RM = M(lat1)
    #^ calculate Meridional radius of Earth ^
    distX = RN*math.cos(math.radians(lat1))*(lon2-lon1)*math.pi/180
    #^ calculate the distance in meters along Longitudinal axis ^
    distY = RM*(lat2-lat1)*math.pi/180
    #^ calculate the distance in meters along Latitudinal axis ^
    return math.sqrt(distX**2+distY**2)
    #^ calculate total distance using trig. ^

def radHeading(lat1, lon1, lat2, lon2):
    '''Calculates the angle in ship heading format between two LAT/LON points.
    :param verbose: 'lat1', 'lon1', 'lat2', 'lon2', are all in milliarcseconds.
    Returns the angle between ('lat1','lon1') and ('lat2','lon2') in the format
    of a ship's heading in radians.
    '''
    lat1 = lat1/3600000
    lon1 = lon1/3600000
    lat2 = lat2/3600000
    lon2 = lon2/3600000
    #^ convert from milliarcseconds to degrees ^
    RN = N(lat1)
    #^ calculate Normal radius of Earth ^
    RM = M(lat1)
    #^ calculate Meridional radius of Earth ^
    distX = RN*math.cos(math.radians(lat1))*(lon2-lon1)*math.pi/180
    #^ calculate the distance in meters along Longitudinal axis ^
    distY = RM*(lat2-lat1)*math.pi/180
    #^ calculate the distance in meters along Latitudinal axis ^
    return piToHeading(math.atan2(distY,distX))
    #^ calculate heading using trig. ^
    
def distanceHeading(lat1, lon1, lat2, lon2):
    '''Calculates the distance in meters and the angle in ship heading format
    between two LAT/LON points.
    :param verbose: 'lat1', 'lon1', 'lat2', 'lon2', are all in milliarcseconds.
    Returns the the distance between ('lat1','lon1') and ('lat2','lon2') in
    meters angle between ('lat1','lon1') and ('lat2','lon2') in the format of a
    ship's heading in radians.
    '''
    lat1 = lat1/3600000
    lon1 = lon1/3600000
    lat2 = lat2/3600000
    lon2 = lon2/3600000
    #^ convert from milliarcseconds to degrees ^
    RN = N(lat1)
    #^ calculate Normal radius of Earth ^
    RM = M(lat1)
    #^ calculate Meridional radius of Earth ^
    distX = RN*math.cos(math.radians(lat1))*(lon2-lon1)*math.pi/180
    #^ calculate the distance in meters along Longitudinal axis ^
    distY = RM*(lat2-lat1)*math.pi/180
    #^ calculate the distance in meters along Latitudinal axis ^
    return math.sqrt(distX**2+distY**2), piToHeading(math.atan2(distY,distX))
    #^ calculate total distance and heading using trig. ^

def piToHeading(val):
    '''Converts a radian angle from scientific angle format to ship heading
    format.
    :param verbose: 'val' must be in radians, and in the format of a scientific
    angle. sci angle format is -pi->0->+pi with 0 directed East (+ x axis), and
    ship heading format is 0->+2*pi with 0 directed North (+ y axis). Returns
    the corresponding angle in radians in the format of a ship heading.
    '''
    ret = val
    if val < 0:
        ret += 2*math.pi
    ret += 1.5*math.pi
    if ret > 2*math.pi:
        ret -=2*math.pi
    ret = 2*math.pi - ret
    return ret

#convert from 0->2pi with 0 north to -pi->0->pi with 0 east
def headingToPi(val):
    '''Converts a radian angle from a ship heading format to a scientific angle
    format.
    :param verbose: 'val' must be in radians, and in the format of a scientific
    angle. sci angle format is -pi->0->+pi with 0 directed East (+ x axis), and
    ship heading format is 0->+2*pi with 0 directed North (+ y axis). Returns
    the corresponding angle in radians in the format of a scientific angle.
    '''
    ret = val
    ret = 2*math.pi - ret
    ret -= 1.5*math.pi
    if ret < -math.pi:
        ret += 2*math.pi
    return ret

def normalizeLon(lat):
    '''Calculates the eccentricity of an ellipse corresponding to a circle pla-
    ced at a specific Latitude.
    :param verbose: 'lat' must be in milliarcseconds. Returns the eccentricity
    of the ellipse corresponding to a circle placed at 'lat', a ratio.
    '''
    lat = lat/3600000
    RN = N(lat)
    RM = M(lat)
    distX = RN*math.cos(math.radians(lat))*math.pi/180
    distY = RM*math.pi/180
    return (distY/distX)
    #^ calculate the ellipse ratio of latitude (y) over longitude (x) ^

#-----------------------------------------------------------------------------#
#Some Example Test Cases
'''lat1 = degMinToMas('35S05.5')
lon1 = degMinToMas('150E42.8')
lat2 = degMinToMas('35S5.6704')
lon2 = degMinToMas('150E42.8')
print mDistance(lat1,lon1,lat2,lon2)

lat1 = degMinToMas('35S05.3686')
lon1 = degMinToMas('150E42.9303')
lat2 = degMinToMas('35S05.3567')
lon2 = degMinToMas('150E43.9622')
print radHeading(lat1,lon1,lat2,lon2)*180/math.pi

lat1 = degMinToMas('35S05.55')
lon1 = degMinToMas('150E43.1')
lon2 = lon1+masLonOffsetHeading(lat1,150,315)
print masToDegMin(lon2,'x')
lat2 = lat1+masLatOffsetHeading(lat1,150,315)
print masToDegMin(lat2,'y')
print masToDegMin(lon2+masLonOffsetHeading(lat2,10,315+90),'x')
print masToDegMin(lat2+masLatOffsetHeading(lat2,10,315+90),'y')'''
