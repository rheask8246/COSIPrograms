#!/bin/bash

#chmod u+r+x filename.sh
#./filename.sh
#chmod +x the_file_name

Usage() {
    	echo ""
	echo "General:"
	echo ""
	echo "ARM Output program: needs filename"
    	echo "-m <int>		Minimum number of events to use"
        echo "-x <int>          X coordinate of position in 3D Cartesian coordinates" 	
        echo "-y <int>          Y coordinate of position in 3D Cartesian coordinates" 
        echo "-z <int>          Z coordinate of position in 3D Cartesian coordinates" 
        echo "-l <str>          Displays ARM plot on logarithmic scale"
        echo "-e <float>        Peak energy value for source" 	
	echo "-t <str>          Title for ARM Plot" 
	echo "-d <str>		Destination of Copy"
	echo "-o <str>		Origin of data"
	echo "-n <int> 		Maximum number of events to use" 
}	


Origin=""
COPY=""
Geometry="/home/andreas/Science/Software/Nuclearizer/MassModel/COSI.DetectorHead.geo.setup"
#Options for ARM Output which can be set via command line
minevents=100000
xcoord=26.1
ycoord=0.3
zcoord=64
set_log="no"
energy=662
title="Arm Plots for Compton Events"
maxevents=100000

echo "Selected ARM Output Options:"
while getopts "m:x:y:z:m:l:e:t:d:o:n:" opt
do
case $opt in
m)
        minevents=$OPTARG;
        echo "* Running ARM Output with minimum events: $minevents";;
x)
        xcoord=$OPTARG;
        echo "Setting x coordinate of source to: $xcoord";;
y)
        ycoord=$OPTARG;
        echo "Setting y coordinate of source to: $ycoord";;
z)
        zcoord=$OPTARG;
        echo "Setting z coordinate of source to: $zcoord";;
l)
        set_log=$OPTARG;
        echo "Use logarithmic scale on y axis of plot? $set_los";;
e)      
        energy=$OPTARG;
        echo "Using energy peak value of: $energy";;
t)
        title=$OPTARG;
        echo "Setting ARM Plot Title to: $title";;
d)
	COPY=$OPTARG;
	echo "Setting copy folder to: $COPY";;
o)
	Origin=$OPTARG;
	echo "Setting the origin of the data to: $Origin";;
n)
	maxevents=$OPTARG;
	echo "* Running ARM Output with maximum events: $maxevents";;
esac
done

# minevents sanity check - must be integer
if ! [[ "$minevents" =~ ^[0-9]+$ ]]; then
  printf "Error: Minimum events must be an integer. \n"
  exit 1;
fi

# x coordinate sanity check - must be integer or float
if ! [[ "$xcoord" =~ ^[0-9]+$ || "$xcoord" =~ ^[+-]?[0-9]+\.?[0-9]*$ ]]; then
  printf "Error: 3D X coordinate must be an integer or a float. \n"
  exit 1;
fi

# y coordinate sanity check - must be integer or float
if ! [[ "$ycoord" =~ ^[0-9]+$ || "$ycoord" =~ ^[+-]?[0-9]+\.?[0-9]*$ ]]; then
  printf "Error: 3D Y coordinate must be an integer or a float. \n"
  exit 1;
fi

# z coordinate sanity check - must be integer or float
if ! [[ "$zcoord" =~ ^[0-9]+$ || "$zcoord" =~ ^[+-]?[0-9]+\.?[0-9]*$ ]]; then
  printf "Error: 3D Z coordinate must be an integer or a float. \n"
  exit 1;
fi

# set log sanity check - must be a string
if ! [[ -n ${set_log//[0-9]/} ]]; then
  printf "Error: Set log must be a string. \n"
  exit 1;
fi

# peak energy sanity check - must be integer or float
if ! [[ "$energy" =~ ^[+-]?[0-9]+\.?[0-9]*$ ]]; then
  printf "Error: Peak energy level must be a float. \n"
  exit 1;
fi

# title sanity check - must be a string
if ! [[ -n ${title//[0-9]/} ]]; then
  printf "Error: Title must be a string. \n"
  exit 1;
fi

# Origin folder sanity check - must have a valid folder entered 
if [[ -z "$Origin" ]]; then
  printf "Error: No origin folder for data entered. \n"
  exit 1;
fi

# COPY folder sanity check - must have a valid folder entered 
if [[ -z "$COPY" ]]; then
  printf "Error: No copy folder entered. \n"
  exit 1;
fi
  
  
type nuclearizer >/dev/null 2>&1

if [ $? -ne 0 ]; then
  echo "ERROR: nuclearizer must be installed"
  exit 1
fi
type revan >/dev/null 2>&1
if [ $? -ne 0 ]; then
  echo "ERROR: revan must be installed"
  exit 1
fi
# Step zero: Create list of runs:
Runs=""
Files=$(ls $Origin/*.roa.gz)

for File in ${Files}; do
  #cd /volumes/selene/users/yasaman/CopyData
  cd ${COPY}
  if [ ! -f $(basename $File) ]; then
    cp ${File} ${COPY}
  fi
  chmod +x ${File}
  echo "RunElement#" | awk -F. '{print $2}'
  echo "${File}"
  Runs+=" $(basename ${File} .roa.gz)"
done

echo "Runs: ${Runs}"

cp /volumes/selene/COSI_2016/ER/Pipeline/*.cfg ${COPY}
# Step one: Convert everything to evta files
for Run in ${Runs}; do
  mwait -p=nuclearizer -i=cores

  InputFile="${Run}.roa.gz"
  OutputFile="${Run}.evta.gz"
  timeout 60 nuclearizer -a -g ${Geometry} -c Nuclearizer_ER_Data.cfg -C ModuleOptions.XmlTagMeasurementLoaderROA.FileName=${InputFile} -C ModuleOptions.XmlTagEventSaver.FileName=${OutputFile} -c ModuleOptions.XmlTagSimulationLoader.UseStopAfter=True -C ModuleOpetions.XmlTagSimulationLoader.MaximumAcceptedEvents=${maxevents} &
done
wait

for Run in ${Runs}; do
  OutputFile="${Run}.evta.gz"
  if [ ! -f ${OutputFile} ]; then 
    echo “ERROR: Output file has not been created: ${OutputFile}”; 
    exit 1; 
   fi

done

# Step two: Run revan
#Algorithms="Classic Bayes MLP RF"
Algorithms="Classic"
for A in ${Algorithms}; do
  for Run in ${Runs}; do
    mwait -p=revan -i=cores
    # To do: for Bayes MLP & ER you have to replace the training data sets, i.e.
    # <BayesianComptonFile>/volumes/crius/users/andreas/COSI_2016/ER/Sims/Cs137/AllSky/ComptonTMVADataSets.p1.inc1.mc.goodbad.rsp</BayesianComptonFile>
    # <CSRTMVAFile>/volumes/crius/users/andreas/COSI_2016/ER/Sims/Cs137/AllSky/ComptonTMVA.v2.tmva</CSRTMVAFile>
    # <CSRTMVAMethods>MLP</CSRTMVAMethods>
    grep "TMVA" /volumes/selene/COSI_2016/ER/Pipeline/Revan_ER_MLP.cfg #Revan_ER_Bayes.cfg

    cd /volumes/selene/users/yasaman/CopyData
    ISOTOPE=$(echo ${Run} | awk -F. '{print $2}')
    if [[ ${A} == Classic ]] || [[ ${A} == Bayes ]]; then
      revan -a -n -c Revan_ER_${A}.cfg -g ${Geometry} -f ${Run}.evta.gz &
    elif [[ ${A} == MLP ]] || [[ ${A} == RF ]]; then
      revan -a -n -c Revan_ER_${A}.cfg -g ${Geometry} -f ${Run}.evta.gz #-C CSRTMVAFile==/volumes/crius/users/andreas/COSI_2016/ER/Sims/${ISOTOPE}/AllSky/ComptonTMVA.v2.tmva -C CSRTMVAMethods=${A} &
    else # replace =</volumes/crius/users/andreas/COSI_2016/ER?Sims/${ISOTOPE}/AllSky/ComptonTMVA.v2.tmva with 
      FileName=$(grep CSRTMVAFile Revan_ER_RF.cfg | awk -F'>' '{ print $2}' | awk -F'<' '{print $1}'); echo ${FileName/Cs137/Ba133}
      ${FileName/Cs137/Ba133}
      ${FileName/Cs137/${ISOTOPE}}
      echo "Error when running Revan. Check geometry, file names, or configuration."

    fi
  done
  wait
  for Run in ${Runs}; do
    mv ${Run}.tra.gz ${Run}.${A}.tra.gz
  done
done

for Run in ${Run}; do
   if [ -f ${Run}.txt ]; then
     rm ${Run}.txt
   fi

   for A in ${Algorithms}; do
#   echo “${Run}.${A}.tra.gz}” >> ${Run}.txt
   echo "${Run}.${A}.tra.gz" >> ${Run}.txt
done
   echo "python3 /volumes/selene/users/yasaman/COSIPrograms/ARMoutput.py -f ${Run}.txt -m $minevents -x $xcoord -y $ycoord -z $zcoord -l $set_log -e $energy -t $title"
   python3 /volumes/selene/users/yasaman/COSIPrograms/ARMoutput.py -f ${Run}.txt -m $minevents -x $xcoord -y $ycoord -z $zcoord -l $set_log -e $energy -t "$title" -b yes
done

