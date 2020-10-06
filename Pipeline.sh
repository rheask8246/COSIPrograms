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
        echo "-m <int>          Minimum number of events to use"
        echo "-l <str>          Displays ARM plot on logarithmic scale"
        echo "-e <float>        Peak energy value for source" 	
	echo "-t <str>          Title for ARM Plot" 
	echo "-d <str>		Destination of Copy"
	echo "-o <str>		Origin of data"
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

echo "Selected ARM Output Options:"
while getopts "m:x:y:z:m:l:e:t:d:o:" opt
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
esac
done

#check all the inputs to see if they are reasonable. 
#PATH and COPY must be valid inputs
if [[ $minevents !=~ ^[+-]?[0-9]+$ ]]; then
  printf "Error: Minimum events must be an integer \n"
  exit 1;
fi

if [[ -z "$Origin" ]]; then
  printf "Error: No origin folder for data entered \n"
  exit 1;
fi

if [[ -z "$COPY" ]]; then
  printf "Error: No copy folder entered \n"
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
  nuclearizer -a -g ${Geometry} -c Nuclearizer_ER_Data.cfg -C ModuleOptions.XmlTagMeasurementLoaderROA.FileName=${InputFile} -C ModuleOptions.XmlTagEventSaver.FileName=${OutputFile} &
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
   for A in ${Algorithms}; do
#   echo “${Run}.${A}.tra.gz}” >> ${Run}.txt
   echo "${Run}.${A}.tra.gz" >> ${Run}.txt
done
   python3 /volumes/selene/users/yasaman/COSIPrograms/ARMoutput.py -f ${Run}.txt -m $minevents -x $xcoord -y $ycoord -z $zcoord -l $set_log -e $energy -t $title
done

