A graduate class project in underactuated robotics at MIT -- towards long endurance flight with an unpowered glider.

Background
----------

In-situ replanning for autonomous thermal soaring.

`Video <https://vimeo.com/113614425>`_

Installing Flightgear
======================

Copy download_and_compile.sh into a separate dictory on your computer and run to install FG.
Copy fgstuff/cxml_cl/input_protocol.xml into the Flightgear install/fgdata/protocol directory.
Copy run_fgfs.sh into the directory of FG installation and launch from there. 

Run python and julia scripts separately.

Prerequisits
============

::

    Julia 0.3
    Python 
    NLopt

In Julia
--------

::

    Pkg.add("NLopt")
    Pkg.add("JuMP")
    Pkg.add("Winston")

Add to bashrc
-------------

::

    export PYTHONPATH=$PYTHONPATH: bla/bla/bla/ThermalSoaring/python/

Running the processes
=====================

There are five processes to execute:

::

    ./run_fgfs.sh
    ./python/Controller.py
    ./python/VisualizationClient.py
    ./python/StateMachine.py
    julia julia/TrajReplanner.jl


