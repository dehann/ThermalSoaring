#!/bin/sh
cd $(dirname $0)
cd install/flightgear/bin
export LD_LIBRARY_PATH=../../plib/lib:../../openscenegraph/lib:../../simgear/lib:../../openrti/lib
./fgfs  --timeofday=noon \
        --units-meters \
        --fg-root=$PWD/../fgdata/ \
        --aircraft=ask13 \
        --native-fdm=socket,out,20,127.0.0.1,5502,udp \
        --generic=socket,in,20,127.0.0.1,5506,udp,input_protocol \
        --turbulence=0.5 \
        --airport=KSFO \
        --runway=10L \
        --altitude=1300 \
        --heading=113 \
        --uBody=30 \
        --offset-distance=1.0 \
        --offset-azimuth=0 \
        --httpd=8080 \
        --ai-scenario=thermal_demo \
        --disable-real-weather-fetch \
        --enable-clouds3d \
        --wind=0@0 
        $@

#--fdm=null --disable-real-weather-fetch --telnet=5501 --enable-clouds3d --native-ctrls=socket,out,20,127.0.0.1,5505,udp --native-ctrls=socket,in,20,127.0.0.1,5504,udp --native-fdm=socket,in,20,127.0.0.1,5503,udp
