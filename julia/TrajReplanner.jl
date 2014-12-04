
using JSON
using JuMP
using NLopt
#using Winston
using ThermalTraj
using PyCall
@pyimport helper

OBJSHIFT = [0.0,0.0]
OBJ = [0.0,0.0]

smclient = connect(ip"127.0.0.1",5512)
println("Connected to StateMachine server")

# server on 5512 is for state machine connection
@async begin
	while true
		println("waiting for new message")
		smmsg = readline(smclient)
		smdata = JSON.parse(smmsg)

		OBJSHIFT[1] = -smdata["SOBJX"]
		OBJSHIFT[2] = -smdata["SOBJY"]
		println("SET SHFTABS ", OBJSHIFT[1], ", ", OBJSHIFT[2])
	end
end

#create connection to Python Autopilot
client = connect(ip"127.0.0.1",5510)
println("Connected")

# and immediately request the current position from Python
# Commands to send to Python Autopilot
channel = "REQUEST_DATA"

my_dict = ["CHANNEL"=> channel]
reqPosMsg = json(my_dict)

# placeholder for trajectory tape
nodes = 35
x = zeros(5,nodes);
u = zeros(nodes);

Re = 6378137

dt = 0.5;
t = linspace(0,dt*nodes,nodes);

# run behaviors
tapeMsg = ""

#request state from python
println("Requesting data from Python controller")
print(client,reqPosMsg)
#block on reply from python
msgdata = readline(client)


### known position of thermal only using for initial testing, shiftabs used to move objective center
# Thermal at KSO tower
#<latitude>37.61633</latitude>
#<longitude>-122.38334</longitude>
#<strength-fps>13.49</strength-fps>
#<diameter-ft>4800.0</diameter-ft>
#Tlat = 37.61633
#Tlon = -122.38334

msg = JSON.parse(msgdata)
println("Now prepare for first trajectory optimization")
#dlat = (msg["LAT"]*180.0/pi - Tlat)*pi/180.0
#dlon = (msg["LON"]*180.0/pi - Tlon)*pi/180.0

x0 = zeros(5)
println("Heading received ", msg["HEADING"])
x0[3] = heading2XY(msg["HEADING"]*180.0/pi)
#x0[1] = Re*dlon
#x0[2] = Re*dlat
dx, dy = helper.lla2flatearth(msg["LAT"], msg["LON"])
x0[1] = dx
x0[2] = dy

if (x0[1]>100000.0)
	println("ERROR, x0 is way to large for trajectory optimization")
end

lastSendT = 0.0
nextSendDelay = 0.0

while true
	println("x0: ", x0)

	#solve new opt problem
	solveTraj!(x0,u,x)

	#pack new json tape
	#x[4,:] = (sign(u).*max(abs(x[4,:]'),abs(u)))'
	tapeX = x[1,:] - OBJ[1]
	tapeY = x[2,:] - OBJ[2]
	#OBJ[1] = 0.0
	#OBJ[2] = 0.0
	tape = ["CHANNEL"=> "NEW_TAPE", "t"=> t, "u"=>-x[4,:], "x"=>tapeX, "y"=>tapeY]
	tapeMsg = json(tape)
	println("Ready with new tape")
	
	if lastSendT != 0.0
		for j in 1:200
			#println("Requesting new data")
			print(client,reqPosMsg)
			msgdata = readline(client)
			chkNewTapeMsg = JSON.parse(msgdata)
			if chkNewTapeMsg["CUR_INDEX"] >= (pp-1)
				println("PP ", pp, " | ", nodes)
				break
			else
				sleep( dt/2.0 )
			end
			
			if j>= 199
				println("Failed to reach the PP new tape goal in a reasonable amount of time, sending new tape.")
			end
		end
	end
	
	#send tape
	println("Sending new tape")
	print(client,tapeMsg)
	lastSendT = time()

	pp = floor(83.0*nodes/100.0)
	#nextSendDelay = t[pp]
	rpx0 = x[:,pp]
	#println(rpx0)
	if rpx0[3]<-pi
		rpx0[3] += 2pi
	end
	if rpx0[3]>pi
		rpx0[3] -= 2pi
	end
	#println(rpx0)
	x0 = rpx0
	# incorporate shift from state machine logic
	OBJ[1] = OBJ[1] + OBJSHIFT[1]
	OBJ[2] = OBJ[2] + OBJSHIFT[2]
	println("SHFTABS ", -OBJ[1], ", ", -OBJ[2])
	x0[1] = x0[1] + OBJSHIFT[1]
	x0[2] = x0[2] + OBJSHIFT[2]
	OBJSHIFT[1] = 0.0
	OBJSHIFT[2] = 0.0	
	# reset shift after it has been incorporated into the current plan
end


close(client)
close(smclient)




