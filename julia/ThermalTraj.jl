module ThermalTraj

using JuMP
using NLopt
using JSON

export printTest
export heading2XY
export initTrajModel!
export solveTraj!

function printTest()
  println("Testing print from module ThermalTraj")
end

function heading2XY(h)
    e = -(h-90.0)#*pi/180.0
    if e <= -180.0
        e += 360.0
    end
    return e*pi/180.0
end

# function to setup the optimization model, but not optimize the traj
function initTrajModel!(m, x0, nodes, l_x, b_u)
    b_dx = 25.9 #80.0/3.6
    b_dy = 0
    dt = 0.6;
    #println("Constant forward body speed of [", b_dx, ", ", b_dy,"] [m/s]")

    umax = 40.0*pi/180.0;

    # Set the objective function
    @setNLObjective(m, Min,  sum{(l_x[1,i])^2+(l_x[2,i])^2, i = 1:nodes} 
                    + 100.0*sum{(b_u[i])^2,i=1:floor(nodes*4.0/5.0)} 
                    - 50.0 *sum{ l_x[4,i-3]*l_x[4,i] ,i=4:nodes})
    
    x = linspace(x0[1],0.,nodes);
    y = linspace(x0[2],0.,nodes);
    
    phi0 = -20.0*pi/180.0
    if x0[4] > 0
    	phi0 = 20.0*pi/180.0
    end
    
    for n in 1:nodes
        #initialize variables
        setValue(l_x[1,n],x[n])
        setValue(l_x[2,n],y[n])
        setValue(l_x[3,n],0.0)
        setValue(l_x[4,n],phi0)
        setValue(l_x[5,n],0.0)
        setValue(b_u[n],0.0)
    end
    
 	expdt = exp(dt)
 	
	#a34 = 0.06039
	#a35 = 0.23181
	#a44 = 0.69768
	#a54 = 0.34478
	#a55 = 0.58275
	#b32 = 0.0091949
	#b42 = 0.42167
	#b52 = 0.090857
	
	#a34 = 0.092057
	#a35 = 0.19781
	#a44 = 0.74082
	#a54 = 0.50137
	#a55 = 0.40657
	#b32 = 0.011964
	#b42 = 0.36043
	#b52 = 0.11599
	
	a34 = 0.082852
	a35 = 0.17803
	a44 = 0.74082
	a54 = 0.50137
	a55 = 0.40657
	b32 = 0.010768
	b42 = 0.36043
	b52 = 0.11599
	
	# initial condition constraints on dynamics
    @addNLConstraint(m, b_u[1] <= umax)
    @addNLConstraint(m, -b_u[1] <= umax)
    @addNLConstraint(m, l_x[4,1] <= umax)
    @addNLConstraint(m, -l_x[4,1] <= umax)
    @addNLConstraint(m, l_x[1,1] == x0[1] + (expdt*cos(x0[3]) - cos(x0[3]))*b_dx  )
    @addNLConstraint(m, l_x[2,1] == x0[2] + (expdt*sin(x0[3]) - sin(x0[3]))*b_dx  )
    @addNLConstraint(m, l_x[3,1] == x0[3] + a34*x0[4] + a35*x0[5] + b32*b_u[1]  )
    @addNLConstraint(m, l_x[4,1] == x0[4]*a44 + b42*b_u[1]  )
    @addNLConstraint(m, l_x[5,1] == x0[5]*a55 + a54*x0[4] + b52*b_u[1]  )
    
    
    for n in 1:(nodes-1)
        # dynamics constraints
        @addNLConstraint(m, l_x[1,n+1] == l_x[1,n] + (expdt*cos(l_x[3,n]) - cos(l_x[3,n]))*b_dx  )
		@addNLConstraint(m, l_x[2,n+1] == l_x[2,n] + (expdt*sin(l_x[3,n]) - sin(l_x[3,n]))*b_dx  )
		@addNLConstraint(m, l_x[3,n+1] == l_x[3,n] + a34*l_x[4,n] + a35*l_x[5,n] + b32*b_u[n+1]  )
		@addNLConstraint(m, l_x[4,n+1] == l_x[4,n]*a44 + b42*b_u[n+1]  )
		@addNLConstraint(m, l_x[5,n+1] == l_x[5,n]*a55 + a54*l_x[4,n] + b52*b_u[n+1]  )
        @addNLConstraint(m, b_u[n+1] <= umax)
        @addNLConstraint(m, -b_u[n+1] <= umax)
        @addNLConstraint(m, l_x[4,n+1] <= umax)
        @addNLConstraint(m, -l_x[4,n+1] <= umax)
    end
end

function solveTraj!(x0,u,x)
    # Setup the optimization scheme
    m = Model(solver=NLoptSolver(algorithm=:LD_SLSQP))
    # state variables for for direct transcription
    nodes = size(u)[1]
    @defVar(m, l_x[1:5,1:nodes])
    # input decision variables -- u[1] is actually u[0] 
    @defVar(m, b_u[1:nodes])
    
    initTrajModel!(m, x0, nodes, l_x, b_u)
    # Test the solving capability
    
    toc = @elapsed status = solve(m)
    
    # get optimal values in general numeric array
    for i in 1:nodes, j in 1:5
        x[j,i] = getValue(l_x[j,i])
        u[i] = getValue(b_u[i])
    end
    
    println("TrajOpt compute time: ", toc)
end


end
