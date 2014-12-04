#!/bin/bash
#* Written by Francesco Angelo Brisa, started January 2008.
#
# Copyright (C) 2013 Francesco Angelo Brisa
# email: fbrisa@gmail.com   -   fbrisa@yahoo.it
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

VERSION="2.28"

#######################################################
# THANKS TO
#######################################################
# Special thanks to Alessandro Garosi for FGComGui and 
# other patches
# Thanks to "Pat Callahan" for patches for fgrun compilation
# Thanks to "F-JJTH" for bug fixes and suggestions
# Thanks again to "F-JJTH" for OpenRTI and FGX 
# Thanks to André, ( taureau89_9 ) for debian stable packages fixes

LOGFILE=compilation_log.txt
WHATTOBUILD=
#AVAILABLE VALUES: CGAL PLIB OSG SIMGEAR FGFS DATA FGO FGX FGRUN OPENRTI OPENRADAR TERRAGEAR TERRAGEARGUI
WHATTOBUILDALL=( CGAL PLIB OSG SIMGEAR FGFS DATA FGRUN OPENRTI TERRAGEAR TERRAGEARGUI)
UPDATE=
STABLE=
APT_GET_UPDATE="y"
DOWNLOAD_PACKAGES="y"
COMPILE="y"
RECONFIGURE="y"
DOWNLOAD="y"
JOPTION=""
OOPTION=""
DEBUG=""

while getopts "suhc:p:a:d:r:j:O:i" OPTION; do
     case $OPTION in
         s) STABLE="STABLE" ;;
         u) UPDATE="UPDATE" ;;
         h) HELP="HELP" ;;
         a) APT_GET_UPDATE=$OPTARG ;;
         c) COMPILE=$OPTARG ;;
         p) DOWNLOAD_PACKAGES=$OPTARG ;;
         d) DOWNLOAD=$OPTARG ;;
         r) RECONFIGURE=$OPTARG ;;
         j) JOPTION=" -j"$OPTARG" " ;;
	 O) OOPTION=" -O"$OPTARG" " ;;
         ?) HELP="HELP" ;;
     esac
done
shift $(($OPTIND - 1))

if [ ! "$#" = "0" ]; then
	for arg in $*
	do
		if [ "$arg" == "UPDATE" ]; then
			UPDATE="UPDATE"
		else
			WHATTOBUILD=( "${WHATTOBUILD[@]}" "$arg" )
		fi
	done
else
	WHATTOBUILD=( "${WHATTOBUILDALL[@]}" )
fi

if [[ "$(declare -p WHATTOBUILD)" =~ '['([0-9]+)']="ALL"' ]]; then
	WHATTOBUILD=( "${WHATTOBUILDALL[@]}" )
fi

#############################################################"
# Some helper for redundant task

function _logSep(){
	echo "***********************************" >> $LOGFILE
}

function _gitUpdate(){
	if [ "$DOWNLOAD" != "y" ]; then
		return
	fi
	branch=$1
	set +e
	git diff --exit-code 2>&1 > /dev/null
	if [ $? != 1 ]; then
		set -e
		git checkout -f $branch
		git pull -r
	else
		set -e
		git stash save -u -q
		git checkout -f $branch
		git pull -r
		git stash pop -q
	fi
}

function _gitDownload(){
	if [ "$DOWNLOAD" != "y" ]; then
		return
	fi
	repo=$1
	if [ -f "README" -o -f "README.txt" ]; then
		echo "$repo exists already"
	else
		git clone $repo .
	fi
}

function _make(){
	if [ "$COMPILE" = "y" ]; then
	        pkg=$1
		cd "$CBD"/build/$pkg
		echo "MAKE $pkg" >> $LOGFILE
		make $JOPTION $OOPTION 2>&1 | tee -a $LOGFILE
		echo "INSTALL $pkg" >> $LOGFILE
		make install 2>&1 | tee -a $LOGFILE
	fi
}

#######################################################
OSG_STABLE_GIT_BRANCH="OpenSceneGraph-3.2"
PLIB_STABLE_GIT_BRANCH="master"
# common stable branch for flightgear, simgear and fgdata
FGSG_STABLE_GIT_BRANCH="release/3.2.0"
OPENRTI_STABLE_GIT_BRANCH="release-0.5"
# unstable branch: next for sg/fg, master for fgdata
FGSG_UNSTABLE_GIT_BRANCH="next"
FGDATA_UNSTABLE_GIT_BRANCH="master"
OPENRTI_UNSTABLE_GIT_BRANCH="master"
#OpenRadar
OR_STABLE_RELEASE="http://wagnerw.de/OpenRadar.zip"
#TerraGear
TG_STABLE_GIT_BRANCH="scenery/ws2.0"
TGGUI_STABLE_GIT_BRANCH="master"
CGAL_PACKAGE="https://gforge.inria.fr/frs/download.php/32183/CGAL-4.2-beta1.tar.gz"

#######################################################
# set script to stop if an error occours
set -e

if [ "$HELP" = "HELP" ]; then
	echo "$0 Version $VERSION"
	echo "Usage:"
	echo "./$0 [-u] [-h] [-s] [-e] [-f] [-i] [-g] [-a y|n] [-c y|n] [-p y|n] [-d y|n] [-r y|n] [ALL|CGAL|PLIB|OSG|OPENRTI|SIMGEAR|FGFS|DATA|FGO|FGX|FGRUN|OPENRADAR|TERRAGEAR|TERRAGEARGUI] [UPDATE]"
	echo "* without options or with ALL it recompiles the content of the WHATTOBUILDALL variable."
	echo "* Feel you free to customize the WHATTOBUILDALL variable available on the top of this script"
	echo "* Adding UPDATE it does not rebuild all (faster but to use only after one successfull first compile)"
	echo "Switches:"
	echo "* -u  such as using UPDATE"
	echo "* -h  show this help"
	echo "* -e  compile FlightGear with --with-eventinput option (experimental)"
	echo "* -g  compile with debug info for gcc"
	echo "* -a y|n  y=do an apt-get update n=skip apt-get update                      	default=y"
	echo "* -p y|n  y=download packages n=skip download packages                      	default=y"
	echo "* -c y|n  y=compile programs  n=do not compile programs                     	default=y"
	echo "* -d y|n  y=fetch programs from internet (cvs, svn, etc...)  n=do not fetch 	default=y"
	echo "* -j X    Add -jX to the make compilation		                             	default=None"
	echo "* -O X    Add -OX to the make compilation	           				default=None"
	echo "* -r y|n  y=reconfigure programs before compiling them  n=do not reconfigure	default=y"
	echo "* -s compile only last stable known versions					default=y"
	exit
fi

#######################################################
#######################################################
# Warning about compilation time and size
# Idea from Jester
echo "**************************************"
echo "*                                    *"
echo "* Warning, the compilation process   *"
echo "* is going to use 12 or more Gbytes  *"
echo "* of space and at least a couple of  *"
echo "* hours to download and build FG.    *"
echo "*                                    *"
echo "* Please, be patient ......          *"
echo "*                                    *"
echo "**************************************"

#######################################################
#######################################################
# Debian 4.0rX (Etch) backports.org
# From D-HUND
ISSUE=$(cat /etc/issue)
if [ "$ISSUE" = "Debian GNU/Linux 4.0 \n \l" ]; then
	clear
	echo "*****************************************************"
	echo "*    Note to users of Debian Etch (Stable 4.0rX)    *"
	echo "*****************************************************"
	echo
	echo "Since autumn 2008 it is not possible anymore to easily install fgfs"
	echo "cvs by using standard repositry. Therefore it is necessary to have"
	echo "backports.org in the apt sources.list to run this script."
	echo
	echo "If you're using synaptic you may follow these steps:"
	echo "  - Open synaptics menu 'Settings' --> 'Repositories'"
	echo "  - Click 'Add' and do"
	echo "      select 'Binaries (deb)'"
	echo "      enter Address:      'www.backports.org/backports.org/'"
	echo "      enter Distribution: 'etch-backports'"
	echo "      enter Section(s):   'main contrib non-free'"
	echo "  - Close Repositries window using 'OK'"
	echo "  - Click 'Reload' to update database."
	echo
	echo "If you have backports.org in your apt-repositries and want to get"
	echo "rid of this message have a look at the script."
	echo -n "[c] to continue or just [ENTER] to exit script: "
	if [ "$(read GOON)" != "c" ]; then
		echo "Script aborted!"
		exit 0
	fi
fi
#######################################################
#######################################################

echo $0 $* > $LOGFILE
echo "APT_GET_UPDATE=$APT_GET_UPDATE" >> $LOGFILE
echo "DOWNLOAD_PACKAGES=$DOWNLOAD_PACKAGES" >> $LOGFILE
echo "COMPILE=$COMPILE" >> $LOGFILE
echo "RECONFIGURE=$RECONFIGURE" >> $LOGFILE
echo "DOWNLOAD=$DOWNLOAD" >> $LOGFILE
echo "JOPTION=$JOPTION" >> $LOGFILE
echo "OOPTION=$OOPTION" >> $LOGFILE
echo "DEBUG=$DEBUG" >> $LOGFILE
_logSep

# discovering linux
if [ -e /etc/lsb-release ]; then
	. /etc/lsb-release
fi

DISTRO_PACKAGES="libopenal-dev libbz2-dev libalut-dev libalut0 cvs subversion cmake make build-essential automake zlib1g-dev zlib1g libwxgtk2.8-0 libwxgtk2.8-dev fluid gawk gettext libxi-dev libxi6 libxmu-dev libxmu6 libasound2-dev libasound2 libpng12-dev libpng12-0 libjasper1 libjasper-dev libopenexr-dev git-core libqt4-dev scons python-tk python-imaging-tk libsvn-dev libglew1.5-dev libxft2 libxft-dev libxinerama1 libxinerama-dev python-dev libboost-dev libcurl4-gnutls-dev libqt4-opengl-dev libqtwebkit-dev libjpeg-dev libpoppler-glib-dev librsvg2-dev libcairo2-dev libgtk2.0-dev libgtkglext1-dev libxrandr-dev  libxml2-dev libgdal-dev libgmp-dev libmpfr-dev libgdal-dev libtiff4-dev python-dev libbz2-dev libqt4-dev libboost-dev libboost-thread-dev libboost-system-dev"

UBUNTU_PACKAGES="freeglut3-dev libapr1-dev libfltk1.3-dev libfltk1.3"
DEBIAN_PACKAGES_STABLE="freeglut3-dev libjpeg8-dev libjpeg8 libfltk1.1-dev libfltk1.1"
DEBIAN_PACKAGES_TESTING="freeglut3-dev libjpeg8-dev libjpeg8 libfltk1.3-dev libfltk1.3"
DEBIAN_PACKAGES_UNSTABLE="freeglut3-dev libjpeg8-dev libjpeg8 libfltk1.3-dev libfltk1.3"

# checking linux distro and version to differ needed packages
if [ "$DISTRIB_ID" = "Ubuntu" -o "$DISTRIB_ID" = "LinuxMint" ]; then
	echo "$DISTRIB_ID $DISTRIB_RELEASE" >> $LOGFILE
	DISTRO_PACKAGES="$DISTRO_PACKAGES $UBUNTU_PACKAGES"
else
	echo "DEBIAN I SUPPOSE" >> $LOGFILE
	DEBIAN_PACKAGES=$DEBIAN_PACKAGES_STABLE
	if [ ! "$(apt-cache search libfltk1.3)" = "" ]; then
	  DEBIAN_PACKAGES=$DEBIAN_PACKAGES_TESTING
	fi
	DISTRO_PACKAGES="$DISTRO_PACKAGES $DEBIAN_PACKAGES"
fi
_logSep

if [ "$DOWNLOAD_PACKAGES" = "y" ]; then
	echo -n "PACKAGE INSTALLATION ... " >> $LOGFILE
	LIBOPENALPACKAGE=$(apt-cache search libopenal | grep "libopenal. " | sed s/\ .*//)
	DISTRO_PACKAGES=$DISTRO_PACKAGES" "$LIBOPENALPACKAGE
	# checking linux distro and version to differ needed packages
	if [ "$DISTRIB_ID" = "Ubuntu" -o "$DISTRIB_ID" = "LinuxMint" ]; then
		if [ "$APT_GET_UPDATE" = "y" ]; then
			echo "Asking your password to perform an apt-get update"
			sudo apt-get update
		fi
		echo "Asking your password to perform an apt-get install ... "
		sudo apt-get install $DISTRO_PACKAGES 
	else
		if [ "$APT_GET_UPDATE" = "y" ]; then
			echo "Asking root password to perform an apt-get update"
			su -c "apt-get update"
		fi
		echo "Asking root password to perform an apt-get install ... "
		su -c "apt-get install $DISTRO_PACKAGES"
	fi
fi

CBD=$(pwd)
LOGFILE=$CBD/$LOGFILE
echo "DIRECTORY= $CBD" >> $LOGFILE
_logSep
mkdir -p install
SUB_INSTALL_DIR=install
INSTALL_DIR=$CBD/$SUB_INSTALL_DIR
cd "$CBD"
mkdir -p build

#######################################################
# BACKWARD COMPATIBILITY WITH 1.9.14a
#######################################################

if [ -d "$CBD"/fgfs/flightgear ]; then
	echo "Move to the new folder structure"
	rm -rf OpenSceneGraph
	rm -rf plib
	rm -rf build
	rm -rf install/fgo
	rm -rf install/fgx
	rm -rf install/osg
	rm -rf install/plib
	rm -rf install/simgear
	rm -f *.log*
	rm -f run_*.sh
	mv openrti/openrti tmp && rm -rf openrti && mv tmp openrti
	mv fgfs/flightgear tmp && rm -rf fgfs && mv tmp flightgear
	mv simgear/simgear tmp && rm -rf simgear && mv tmp simgear
	mkdir -p install/flightgear && mv install/fgfs/fgdata install/flightgear/fgdata
	echo "Done"
fi

#######################################################
# PLIB
#######################################################
PLIB_INSTALL_DIR=plib
INSTALL_DIR_PLIB=$INSTALL_DIR/$PLIB_INSTALL_DIR
cd "$CBD"
mkdir -p "plib"

if [[ "$(declare -p WHATTOBUILD)" =~ '['([0-9]+)']="PLIB"' ]]; then
	if [ ! "$UPDATE" = "UPDATE" ]; then
		echo "****************************************" | tee -a $LOGFILE
		echo "**************** PLIB ******************" | tee -a $LOGFILE
		echo "****************************************" | tee -a $LOGFILE

		cd "$CBD"/plib
		_gitDownload git://gitorious.org/libplib/libplib.git
		_gitUpdate $PLIB_STABLE_GIT_BRANCH

		if [ "$RECONFIGURE" = "y" ]; then
			cd "$CBD"
			mkdir -p build/plib
			echo "CONFIGURING plib" >> $LOGFILE
			cd "$CBD"/build/plib
			cmake -DCMAKE_INSTALL_PREFIX:PATH="$INSTALL_DIR_PLIB" ../../plib
		fi

		_make plib
	fi
fi

#######################################################
# CGAL
#######################################################
CGAL_INSTALL_DIR=cgal
INSTALL_DIR_CGAL=$INSTALL_DIR/$CGAL_INSTALL_DIR
cd "$CBD"

if [[ "$(declare -p WHATTOBUILD)" =~ '['([0-9]+)']="CGAL"' ]]; then
	echo "****************************************" | tee -a $LOGFILE
	echo "***************** CGAL *****************" | tee -a $LOGFILE
	echo "****************************************" | tee -a $LOGFILE

	if [ ! -d "cgal" ]; then
		echo "Download CGAL... $CGAL_PACKAGE"
		wget -O cgal.tar.gz $CGAL_PACKAGE
		tar -zxf cgal.tar.gz
		mv CGAL* cgal
	fi

	if [ ! "$UPDATE" = "UPDATE" ]; then
		if [ "$RECONFIGURE" = "y" ]; then
			cd "$CBD"
			mkdir -p build/cgal
			cd "$CBD"/build/cgal
			echo "CONFIGURING CGAL ... " >> $LOGFILE
			cmake -DCMAKE_INSTALL_PREFIX:PATH="$INSTALL_DIR_CGAL" ../../cgal/ 2>&1 | tee -a $LOGFILE
			echo "CONFIGURING CGAL DONE" >> $LOGFILE
		fi
	fi

	_make cgal
fi

#######################################################
# OpenSceneGraph
#######################################################
OSG_INSTALL_DIR=openscenegraph
INSTALL_DIR_OSG=$INSTALL_DIR/$OSG_INSTALL_DIR
cd "$CBD"
mkdir -p "openscenegraph"

if [[ "$(declare -p WHATTOBUILD)" =~ '['([0-9]+)']="OSG"' ]]; then
	echo "****************************************" | tee -a $LOGFILE
	echo "**************** OSG *******************" | tee -a $LOGFILE
	echo "****************************************" | tee -a $LOGFILE

	cd "$CBD"/openscenegraph
	_gitDownload http://github.com/openscenegraph/osg.git

	_gitUpdate $OSG_STABLE_GIT_BRANCH

	if [ ! "$UPDATE" = "UPDATE" ]; then
		if [ "$RECONFIGURE" = "y" ]; then
			cd "$CBD"
			mkdir -p build/openscenegraph
			cd "$CBD"/build/openscenegraph
			rm -f CMakeCache.txt
			cmake 	-DCMAKE_BUILD_TYPE="Release" \
				-DCMAKE_INSTALL_PREFIX:PATH="$INSTALL_DIR_OSG" ../../openscenegraph/ 2>&1 | tee -a $LOGFILE
		fi
	fi

	_make openscenegraph

	#FIX FOR 64 BIT COMPILATION
	if [ -d "$INSTALL_DIR_OSG/lib64" ]; then
		if [ -L "$INSTALL_DIR_OSG/lib" ]; then
			echo "link already done"
		else
			ln -s "$INSTALL_DIR_OSG/lib64" "$INSTALL_DIR_OSG/lib"
		fi
	fi
fi

#######################################################
# OPENRTI
#######################################################
OPENRTI_INSTALL_DIR=openrti
INSTALL_DIR_OPENRTI=$INSTALL_DIR/$OPENRTI_INSTALL_DIR
cd "$CBD"
mkdir -p "openrti"

if [[ "$(declare -p WHATTOBUILD)" =~ '['([0-9]+)']="OPENRTI"' ]]; then
	echo "****************************************" | tee -a $LOGFILE
	echo "**************** OPENRTI ***************" | tee -a $LOGFILE
	echo "****************************************" | tee -a $LOGFILE

	cd "$CBD"/openrti
	_gitDownload git://gitorious.org/openrti/openrti.git

	if [ "$STABLE" = "STABLE" ]; then
		_gitUpdate $OPENRTI_STABLE_GIT_BRANCH
	else
		_gitUpdate $OPENRTI_UNSTABLE_GIT_BRANCH
	fi

	if [ ! "$UPDATE" = "UPDATE" ]; then
		if [ "$RECONFIGURE" = "y" ]; then
			cd "$CBD"
			mkdir -p build/openrti
			cd "$CBD"/build/openrti
			rm -f CMakeCache.txt
			cmake 	-DCMAKE_BUILD_TYPE="Release" \
				-DCMAKE_INSTALL_PREFIX:PATH="$INSTALL_DIR_OPENRTI" ../../openrti 2>&1 | tee -a $LOGFILE
		fi
	fi
	
	_make openrti
fi

#######################################################
# SIMGEAR
#######################################################
SIMGEAR_INSTALL_DIR=simgear
INSTALL_DIR_SIMGEAR=$INSTALL_DIR/$SIMGEAR_INSTALL_DIR
cd "$CBD"
mkdir -p "simgear"

if [[ "$(declare -p WHATTOBUILD)" =~ '['([0-9]+)']="SIMGEAR"' ]]; then
	echo "****************************************" | tee -a $LOGFILE
	echo "**************** SIMGEAR ***************" | tee -a $LOGFILE
	echo "****************************************" | tee -a $LOGFILE

	cd "$CBD"/simgear
	_gitDownload git://gitorious.org/fg/simgear.git

	if [ "$STABLE" = "STABLE" ]; then
		_gitUpdate $FGSG_STABLE_GIT_BRANCH
	else
		_gitUpdate $FGSG_UNSTABLE_GIT_BRANCH
	fi
	
	if [ ! "$UPDATE" = "UPDATE" ]; then
		if [ "$RECONFIGURE" = "y" ]; then
			cd "$CBD"
			mkdir -p build/simgear
			cd "$CBD"/build/simgear
			rm -f CMakeCache.txt
			cmake 	-D CMAKE_BUILD_TYPE="Release" \
				-D ENABLE_RTI=OFF \
				-D CMAKE_INSTALL_PREFIX:PATH="$INSTALL_DIR_SIMGEAR" \
				-D CMAKE_PREFIX_PATH="$INSTALL_DIR_OSG;$INSTALL_DIR_OPENRTI;$INSTALL_DIR_PLIB" \
				../../simgear 2>&1 | tee -a $LOGFILE
		fi
	fi
	
	_make simgear
fi

#######################################################
# FGFS
#######################################################
FGFS_INSTALL_DIR=flightgear
INSTALL_DIR_FGFS=$INSTALL_DIR/$FGFS_INSTALL_DIR
cd "$CBD"
mkdir -p "flightgear"
mkdir -p $INSTALL_DIR_FGFS/fgdata

if [[ "$(declare -p WHATTOBUILD)" =~ '['([0-9]+)']="FGFS"' || "$(declare -p WHATTOBUILD)" =~ '['([0-9]+)']="DATA"' ]]; then
	echo "****************************************" | tee -a $LOGFILE
	echo "************** FLIGHTGEAR **************" | tee -a $LOGFILE
	echo "****************************************" | tee -a $LOGFILE

	cd "$CBD"/flightgear
	if [[ "$(declare -p WHATTOBUILD)" =~ '['([0-9]+)']="FGFS"' ]]; then
		_gitDownload git://gitorious.org/fg/flightgear.git

		if [ "$STABLE" = "STABLE" ]; then
			_gitUpdate $FGSG_STABLE_GIT_BRANCH
		else
			_gitUpdate $FGSG_UNSTABLE_GIT_BRANCH
		fi

		if [ ! "$UPDATE" = "UPDATE" ]; 	then
			if [ "$RECONFIGURE" = "y" ]; then
	                        cd "$CBD"
       				mkdir -p build/flightgear
	                        cd "$CBD"/build/flightgear
				rm -f CMakeCache.txt
				cmake 	-D CMAKE_BUILD_TYPE="Release" \
					-D ENABLE_RTI=OFF \
					-D ENABLE_FLITE=ON \
					-D CMAKE_INSTALL_PREFIX:PATH="$INSTALL_DIR_FGFS" \
					-D CMAKE_PREFIX_PATH="$INSTALL_DIR_OSG;$INSTALL_DIR_PLIB;$INSTALL_DIR_SIMGEAR;$INSTALL_DIR_OPENRTI" \
					../../flightgear 2>&1 | tee -a $LOGFILE
			fi
		fi

		_make flightgear
	fi

	cd $INSTALL_DIR_FGFS/fgdata
	if [[ "$(declare -p WHATTOBUILD)" =~ '['([0-9]+)']="DATA"' ]]; then
		echo "****************************************" | tee -a $LOGFILE
		echo "**************** DATA ******************" | tee -a $LOGFILE
		echo "****************************************" | tee -a $LOGFILE

		if [ ! "$UPDATE" = "UPDATE" ]; then
			_gitDownload git://gitorious.org/fg/fgdata.git

			if [ "$STABLE" = "STABLE" ]; then
				_gitUpdate $FGSG_STABLE_GIT_BRANCH
			else
				_gitUpdate $FGDATA_UNSTABLE_GIT_BRANCH
			fi
		else
			cd $INSTALL_DIR_FGFS/fgdata
			_gitUpdate $FGDATA_UNSTABLE_GIT_BRANCH
		fi
	fi
	cd "$CBD"

	SCRIPT=run_fgfs.sh
	echo "#!/bin/sh" > $SCRIPT
	echo "cd \$(dirname \$0)" >> $SCRIPT
	echo "cd $SUB_INSTALL_DIR/$FGFS_INSTALL_DIR/bin" >> $SCRIPT
	echo "export LD_LIBRARY_PATH=../../$PLIB_INSTALL_DIR/lib:../../$OSG_INSTALL_DIR/lib:../../$SIMGEAR_INSTALL_DIR/lib:../../$OPENRTI_INSTALL_DIR/lib" >> $SCRIPT
	echo "./fgfs --fg-root=\$PWD/../fgdata/ \$@" >> $SCRIPT
	chmod 755 $SCRIPT

	SCRIPT=run_fgfs_debug.sh
	echo "#!/bin/sh" > $SCRIPT
	echo "cd \$(dirname \$0)" >> $SCRIPT
	echo "cd $SUB_INSTALL_DIR/$FGFS_INSTALL_DIR/bin" >> $SCRIPT
	echo "export LD_LIBRARY_PATH=../../$PLIB_INSTALL_DIR/lib:../../$OSG_INSTALL_DIR/lib:../../$SIMGEAR_INSTALL_DIR/lib:../../$OPENRTI_INSTALL_DIR/lib" >> $SCRIPT
	echo "gdb  --directory="\$P1"/fgfs/source/src/ --args fgfs --fg-root=\$PWD/../fgdata/ \$@" >> $SCRIPT
	chmod 755 $SCRIPT

	SCRIPT=run_fgcom.sh
	echo "#!/bin/sh" > $SCRIPT
	echo "cd \$(dirname \$0)" >> $SCRIPT
	echo "cd $SUB_INSTALL_DIR/$FGFS_INSTALL_DIR/bin" >> $SCRIPT
	echo "./fgcom \$@" >> $SCRIPT
	chmod 755 $SCRIPT
fi

#######################################################
# FGO!
#######################################################
FGO_INSTALL_DIR=fgo
INSTALL_DIR_FGO=$INSTALL_DIR/$FGO_INSTALL_DIR
cd "$CBD"

if [[ "$(declare -p WHATTOBUILD)" =~ '['([0-9]+)']="FGO"' ]]; then
	echo "****************************************" | tee -a $LOGFILE
	echo "***************** FGO ******************" | tee -a $LOGFILE
	echo "****************************************" | tee -a $LOGFILE

	if [ "$DOWNLOAD" = "y" ]; then
		rm -rf fgo*.tar.gz
		wget https://sites.google.com/site/erobosprojects/flightgear/add-ons/fgo/download/fgo-1.5.2.tar.gz -O fgo.tar.gz
		cd install
		tar zxvfh ../fgo.tar.gz
		cd ..
	fi

	SCRIPT=run_fgo.sh
	echo "#!/bin/sh" > $SCRIPT
	echo "cd \$(dirname \$0)" >> $SCRIPT
	echo "cd $SUB_INSTALL_DIR" >> $SCRIPT
	echo "p=\$(pwd)" >> $SCRIPT
	echo "cd $FGO_INSTALL_DIR" >> $SCRIPT
        echo "export LD_LIBRARY_PATH=\$p/plib/lib:\$p/OpenSceneGraph/lib:\$p/simgear/lib"  >> $SCRIPT
	echo "python fgo" >> $SCRIPT
	chmod 755 $SCRIPT
fi

#######################################################
# FGx
#######################################################
FGX_INSTALL_DIR=fgx
INSTALL_DIR_FGX=$INSTALL_DIR/$FGX_INSTALL_DIR
cd "$CBD"
mkdir -p "fgx"

if [[ "$(declare -p WHATTOBUILD)" =~ '['([0-9]+)']="FGX"' ]]; then
	echo "****************************************" | tee -a $LOGFILE
	echo "***************** FGX ******************" | tee -a $LOGFILE
	echo "****************************************" | tee -a $LOGFILE

	cd "$CBD"/fgx
	_gitDownload git://gitorious.org/fgx/fgx.git fgx

	_gitUpdate $FGX_STABLE_GIT_BRANCH

	cd "$CBD"/fgx/src/
	#Patch in order to pre-setting paths
	cd resources/default/
	cp x_default.ini x_default.ini.orig
	cat x_default.ini | sed s/\\/usr\\/bin\\/fgfs/INSTALL_DIR_FGXMY_SLASH_HERE..MY_SLASH_HEREfgfsMY_SLASH_HEREbinMY_SLASH_HEREfgfs/g > tmp1
	cat tmp1 | sed s/\\/usr\\/share\\/flightgear/INSTALL_DIR_FGXMY_SLASH_HERE..MY_SLASH_HEREfgfsMY_SLASH_HEREfgdata/g > tmp2
	cat tmp2 | sed s/\\/usr\\/bin\\/terrasync/INSTALL_DIR_FGXMY_SLASH_HERE..MY_SLASH_HEREfgfsMY_SLASH_HEREbinMY_SLASH_HEREterrasync/g > tmp3
	cat tmp3 | sed s/\\/usr\\/bin\\/fgcom/INSTALL_DIR_FGXMY_SLASH_HERE..MY_SLASH_HEREfgcomMY_SLASH_HEREbinMY_SLASH_HEREfgcom/g > tmp4
	cat tmp4 | sed s/\\/usr\\/bin\\/js_demo/INSTALL_DIR_FGXMY_SLASH_HERE..MY_SLASH_HEREfgfsMY_SLASH_HEREbinMY_SLASH_HEREjs_demo/g > tmp5
	INSTALL_DIR_FGX_NO_SLASHS=$(echo "$INSTALL_DIR_FGX" | sed -e 's/\//MY_SLASH_HERE/g')
	cat tmp5 | sed s/INSTALL_DIR_FGX/"$INSTALL_DIR_FGX_NO_SLASHS"/g > tmp
	cat tmp | sed s/MY_SLASH_HERE/\\//g > x_default.ini
	rm tmp*
	cd ..

	if [ ! "$UPDATE" = "UPDATE" ]; then
		if [ "$RECONFIGURE" = "y" ]; then
			mkdir -p $INSTALL_DIR_FGX
			cd $INSTALL_DIR_FGX
			qmake ../../fgx/src
		fi
	fi
	
	if [ "$COMPILE" = "y" ]; then
		cd $INSTALL_DIR_FGX
		echo "MAKE AND INSTALL FGX" >> $LOGFILE
		echo "make $JOPTION $OOPTION " >> $LOGFILE
		make $JOPTION $OOPTION | tee -a $LOGFILE
		cd ..
	fi
	cd "$CBD"

	SCRIPT=run_fgx.sh
	echo "#!/bin/sh" > $SCRIPT
	echo "cd \$(dirname \$0)" >> $SCRIPT
	echo "cd $ " >> $SCRIPT
	echo "p=\$(pwd)" >> $SCRIPT
	echo "cd $FGX_INSTALL_DIR" >> $SCRIPT
        echo "export LD_LIBRARY_PATH=\$p/plib/lib:\$p/OpenSceneGraph/lib:\$p/simgear/lib"  >> $SCRIPT
	echo "./fgx" >> $SCRIPT
	chmod 755 $SCRIPT
fi

#######################################################
# FGRUN
#######################################################
FGRUN_INSTALL_DIR=fgrun
INSTALL_DIR_FGRUN=$INSTALL_DIR/$FGRUN_INSTALL_DIR
cd "$CBD"
mkdir -p "fgrun"

if [[ "$(declare -p WHATTOBUILD)" =~ '['([0-9]+)']="FGRUN"' ]]; then
	echo "****************************************" | tee -a $LOGFILE
	echo "**************** FGRUN *****************" | tee -a $LOGFILE
	echo "****************************************" | tee -a $LOGFILE

	cd "$CBD"/fgrun
	_gitDownload git://gitorious.org/fg/fgrun.git

	if [ "$STABLE" = "STABLE" ]; then
		_gitUpdate $FGSG_STABLE_GIT_BRANCH
	else
		_gitUpdate $FGSG_UNSTABLE_GIT_BRANCH
	fi

	if [ ! "$UPDATE" = "UPDATE" ]; then
		if [ "$RECONFIGURE" = "y" ]; then
                        cd "$CBD"
                        mkdir -p build/fgrun
                        cd "$CBD"/build/fgrun
			rm -f ../../fgrun/CMakeCache.txt
			cmake -D CMAKE_BUILD_TYPE="Release" \
                              -D CMAKE_INSTALL_PREFIX:PATH="$INSTALL_DIR_FGRUN" \
                              -D CMAKE_PREFIX_PATH="$INSTALL_DIR_OSG;$INSTALL_DIR_PLIB;$INSTALL_DIR_SIMGEAR" \
                              ../../fgrun/ 2>&1 | tee -a $LOGFILE
		fi
	fi
	
	_make fgrun

	cd "$CBD"

	SCRIPT=run_fgrun.sh
	echo "#!/bin/sh" > $SCRIPT
	echo "cd \$(dirname \$0)" >> $SCRIPT
	echo "cd $SUB_INSTALL_DIR/$FGRUN_INSTALL_DIR/bin" >> $SCRIPT
	echo "export LD_LIBRARY_PATH=../../$PLIB_INSTALL_DIR/lib:../../$OSG_INSTALL_DIR/lib:../../$SIMGEAR_INSTALL_DIR/lib" >> $SCRIPT
	echo "./fgrun --fg-exe=\$PWD/../../$FGFS_INSTALL_DIR/bin/fgfs --fg-root=\$PWD/../../$FGFS_INSTALL_DIR/fgdata   \$@" >> $SCRIPT
	chmod 755 $SCRIPT
fi

#######################################################
# OPENRADAR
#######################################################
OR_INSTALL_DIR=openradar
INSTALL_DIR_OR=$INSTALL_DIR/$OR_INSTALL_DIR
cd "$CBD"

if [[ "$(declare -p WHATTOBUILD)" =~ '['([0-9]+)']="OPENRADAR"' ]]; then
	echo "****************************************" | tee -a $LOGFILE
	echo "************** OPENRADAR ***************" | tee -a $LOGFILE
	echo "****************************************" | tee -a $LOGFILE

	if [ "$DOWNLOAD" = "y" ]; then
		wget $OR_STABLE_RELEASE -O OpenRadar.zip
		cd install
		unzip -o ../OpenRadar.zip
		cd ..
	fi

	SCRIPT=run_openradar.sh
	echo "#!/bin/sh" > $SCRIPT
	echo "cd \$(dirname \$0)" >> $SCRIPT
	echo "cd install/OpenRadar" >> $SCRIPT
	echo "java -jar OpenRadar.jar" >> $SCRIPT
	chmod 755 $SCRIPT
fi

#######################################################
#######################################################
# TERRAGEAR
#######################################################
#######################################################

TG_INSTALL_DIR=terragear
INSTALL_DIR_TG=$INSTALL_DIR/$TG_INSTALL_DIR
cd "$CBD"
mkdir -p "terragear"

if [[ "$(declare -p WHATTOBUILD)" =~ '['([0-9]+)']="TERRAGEAR"' ]]; then
	echo "****************************************" | tee -a $LOGFILE
	echo "*************** TERRAGEAR **************" | tee -a $LOGFILE
	echo "****************************************" | tee -a $LOGFILE

	cd "$CBD"/terragear
	_gitDownload git://gitorious.org/fg/terragear.git

	_gitUpdate $TG_STABLE_GIT_BRANCH

	if [ ! "$UPDATE" = "UPDATE" ]; then
		if [ "$RECONFIGURE" = "y" ]; then
			cd "$CBD"
			mkdir -p build/terragear
			cd "$CBD"/build/terragear
			rm -f CMakeCache.txt
			cmake 	-DCMAKE_BUILD_TYPE="Debug" \
				-DCMAKE_INSTALL_PREFIX:PATH="$INSTALL_DIR_TG" \
				-DCMAKE_PREFIX_PATH="$INSTALL_DIR_SIMGEAR;$INSTALL_DIR_CGAL" \
				../../terragear/ 2>&1 | tee -a $LOGFILE
		fi
	fi

	_make terragear

	cd "$CBD"
	echo "#!/bin/sh" > run_tg-construct.sh
	echo "cd $(dirname $0)" >> run_tg-construct.sh
	echo "cd install/terragear/bin" >> run_tg-construct.sh
	echo "export LD_LIBRARY_PATH=$INSTALL_DIR_SIMGEAR/lib:$INSTALL_DIR_CGAL/lib" >> run_tg-construct.sh
	echo "./tg-construct \$@" >> run_tg-construct.sh

	echo "#!/bin/sh" > run_ogr-decode.sh
	echo "cd $(dirname $0)" >> run_ogr-decode.sh
	echo "cd install/terragear/bin" >> run_ogr-decode.sh
	echo "export LD_LIBRARY_PATH=$INSTALL_DIR_SIMGEAR/lib:$INSTALL_DIR_CGAL/lib" >> run_ogr-decode.sh
	echo "./ogr-decode \$@" >> run_ogr-decode.sh

	echo "#!/bin/sh" > run_genapts850.sh
	echo "cd $(dirname $0)" >> run_genapts850.sh
	echo "cd install/terragear/bin" >> run_genapts850.sh
	echo "export LD_LIBRARY_PATH=$INSTALL_DIR_SIMGEAR/lib:$INSTALL_DIR_CGAL/lib" >> run_genapts850.sh
	echo "./genapts850 \$@" >> run_genapts850.sh
fi
_logSep

#######################################################
#######################################################
# TERRAGEAR GUI
#######################################################
#######################################################

TGGUI_INSTALL_DIR=terrageargui
INSTALL_DIR_TGGUI=$INSTALL_DIR/$TGGUI_INSTALL_DIR
cd "$CBD"
mkdir -p "terrageargui"

if [[ "$(declare -p WHATTOBUILD)" =~ '['([0-9]+)']="TERRAGEARGUI"' ]]; then
	echo "****************************************" | tee -a $LOGFILE
	echo "************* TERRAGEAR GUI ************" | tee -a $LOGFILE
	echo "****************************************" | tee -a $LOGFILE

	cd "$CBD"/terrageargui
	_gitDownload git://gitorious.org/fgscenery/terrageargui.git

	_gitUpdate $TGGUI_STABLE_GIT_BRANCH
	
	if [ ! "$UPDATE" = "UPDATE" ]; then
		if [ "$RECONFIGURE" = "y" ]; then
			cd "$CBD"
			mkdir -p build/terrageargui
			cd "$CBD"/build/terrageargui
			rm -f ../../terrageargui/CMakeCache.txt
			cmake 	-DCMAKE_BUILD_TYPE="Release" \
				-DCMAKE_INSTALL_PREFIX="$INSTALL_DIR_TGGUI" ../../terrageargui 2>&1 | tee -a $LOGFILE
		fi
	fi
	
	_make terrageargui

	cd "$CBD"
	# Fill TerraGear Root field
	if [ ! -f ~/.config/TerraGear/TerraGearGUI.conf ]; then
		echo "Fill TerraGear Root field" >> $LOGFILE
		echo "[paths]" > TerraGearGUI.conf
		echo "terragear=$INSTALL_DIR_TG/bin" >> TerraGearGUI.conf
		mkdir -p ~/.config/TerraGear
		mv TerraGearGUI.conf ~/.config/TerraGear
	fi

	echo "Create run_terrageargui.sh" >> $LOGFILE
	echo "#!/bin/sh" > run_terrageargui.sh
	echo "cd \$(dirname \$0)" >> run_terrageargui.sh
	echo "cd install/terrageargui/bin" >> run_terrageargui.sh
        echo "export LD_LIBRARY_PATH=$INSTALL_DIR_SIMGEAR/lib:$INSTALL_DIR_CGAL/lib" >> run_terrageargui.sh
	echo "./TerraGUI \$@" >> run_terrageargui.sh
fi


echo "download_and_compile.sh has finished to work"

cd "$CBD"
