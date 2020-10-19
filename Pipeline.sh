#!/bin/bash

#chmod u+r+x filename.sh
#./filename.sh
#chmod +x the_file_name

Usage() {
  echo ""
  echo "General:"
  echo ""
  echo "ARM Output program: needs filename"
  echo "-m <int>          Minimum number of events to use"
  echo "-l <str>          Displays ARM plot on logarithmic scale"
  echo "-d <str>          Destination of Copy"
  echo "-o <str>          Origin of data"
  echo "-n <int>          Maximum number of events to use" 
  # a for Algorithm
  # g for geometry
}

ScriptPath="$( cd "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"

Origin="/volumes/selene/COSI_2016/ER/Data"
Data="Data"
Geometry="/home/andreas/Science/Software/Nuclearizer/MassModel/COSI.DetectorHead.geo.setup"
#Algorithms="Classic Bayes MLP RF"
Algorithms="Classic Bayes MLP RF"

#Options for ARM Output which can be set via command line
minevents=100000
xcoord=26.1
ycoord=0.3
zcoord=64
set_log="no"
energy=662
title="ARM Plots for Compton Events"
maxevents=100000

echo "Selected ARM Output Options:"
while getopts "m:l:d:o:n:" opt
do
case $opt in
m)
        minevents=$OPTARG;
        echo "* Running ARM Output with minimum events: $minevents";;
l)
        set_log=$OPTARG;
        echo "Use logarithmic scale on y axis of plot? $set_los";;
d)
  Data=$OPTARG;
  echo "Setting copy folder to: ${Data}";;
o)
  Origin=$OPTARG; 
  echo "Setting the origin of the data to: ${Origin}";;
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

# set log sanity check - must be a string
if ! [[ -n ${set_log//[0-9]/} ]]; then
  printf "Error: Set log must be a string. \n"
  exit 1;
fi

# Origin folder sanity check - must have a valid folder entered 
if ! [ -d "${Origin}" ]; then
  printf "Error: No origin folder for data entered. \n"
  exit 1;
fi

# Data folder sanity check - must have a valid folder entered 
if ! [ -d "${Data}" ]; then
  mkdir ${Data}
fi
  
# Check if the key programs are available
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
Files=$(ls ${Origin}/*.roa.gz ${Origin}/*.roa)

for File in ${Files}; do
  if [[ ${File} == *.roa ]]; then
    Runs+=" $(basename ${File} .roa)"
  elif [[ ${File} == *.roa.gz ]]; then
    Runs+=" $(basename ${File} .roa.gz)"
  fi
done

echo "Runs: ${Runs}"


# Copy the configuration files
cp ${Origin}/../Pipeline/*.cfg ${Data}

# Move into the data directory
cd ${Data}

# Step one: Convert everything to evta files
for Run in ${Runs}; do
  mwait -p=nuclearizer -i=cores

  InputFile="${Origin}/${Run}.roa.gz"
  OutputFile="${Run}.evta.gz"
  CfgFile=Nuclearizer_ER_Data.cfg
  
  timeout 10 nuclearizer -a -g ${Geometry} -c ${CfgFile} -C ModuleOptions.XmlTagMeasurementLoaderROA.FileName=${InputFile} -C ModuleOptions.XmlTagEventSaver.FileName=${OutputFile} -C ModuleOptions.XmlTagSimulationLoader.UseStopAfter=True -C ModuleOptions.XmlTagSimulationLoader.MaximumAcceptedEvents=${maxevents} &> ${Run}.nuclearizer.log &
done
echo "INFO: Waiting for all nuclearizer instances to finish"
wait



for Run in ${Runs}; do
  OutputFile="${Run}.evta.gz"
  if [ ! -f ${OutputFile} ]; then 
    echo “ERROR: Output file has not been created: ${OutputFile}”; 
    exit 1; 
  fi
done

# Step two: Run revan
for A in ${Algorithms}; do
  for Run in ${Runs}; do
    mwait -p=revan -i=cores
    
    ISOTOPE=$(echo ${Run} | awk -F. '{print $2}')
    if [[ ${A} == Classic ]] || [[ ${A} == Bayes ]]; then
      revan -a -n -c Revan_ER_${A}.cfg -g ${Geometry} -f ${Run}.evta.gz &> ${Run}.revan.${A}.log &
    elif [[ ${A} == MLP ]] || [[ ${A} == RF ]]; then
    
      TmvaFile=${Origin}/../Sims/${ISOTOPE}/AllSky/ComptonTMVA.v2.tmva
      if ! [ -f ${TmvaFile} ]; then
        echo "ERROR: TMVA file does not exist: ${TmvaFile}"
        continue
      fi
      
      WeightFile=${Origin}/../Sims/${ISOTOPE}/AllSky/ComptonTMVA.v2/N2/weights/TMVAClassification_${A}.weights.xml
      if ! [ -f ${WeightFile} ]; then
        echo "ERROR: TMVA file does not exist: ${WeightFile}"
        continue
      fi
      
      revan -a -n -c Revan_ER_${A}.cfg -g ${Geometry} -f ${Run}.evta.gz -C CSRTMVAFile=${TmvaFile} -C CSRTMVAMethods=${A} &> ${Run}.revan.${A}.log &
    else 
      echo "Error when running Revan: Unknown algorithm: ${A}"
    fi
  done
  echo "INFO: Waiting for all revan instances for algorithm ${A} to finish"
  wait
  for Run in ${Runs}; do
    mv ${Run}.tra.gz ${Run}.${A}.tra.gz
  done
done


for Run in ${Runs}; do
   mwait -p=python3 -i=cores

   if [ -f ${Run}.txt ]; then
     rm ${Run}.txt
   fi

   for A in ${Algorithms}; do
     echo "${Run}.${A}.tra.gz" >> ${Run}.txt
   done
   
   # Retrieve the positions from the data sheet
   Isotope=$( cat ${Origin}/DataSets.txt | grep ${Run} | awk '{ print $2 }')
   XCoord=$( cat ${Origin}/DataSets.txt | grep ${Run} | awk '{ print $4 }')
   YCoord=$( cat ${Origin}/DataSets.txt | grep ${Run} | awk '{ print $5 }')
   ZCoord=$( cat ${Origin}/DataSets.txt | grep ${Run} | awk '{ print $6 }')
   
   Lines=""
   if [[ ${Isotope} == Ba133 ]]; then
     Lines="356.017"
   elif [[ ${Isotope} == Cs137 ]]; then
     Lines="661.657"
   elif [[ ${Isotope} == Na22 ]]; then
     Lines="510.99 1274.577"
   elif [[ ${Isotope} == Y88 ]]; then
     Lines="898.042 1836.063"
   elif [[ ${Isotope} == Co60 ]]; then
     Lines="1173.237 1332.501"
   else
     echo "ERROR: Unknown isotope ${Isotope}"
     continue
   fi
   
   for L in ${Lines}; do
     echo "INFO: python3 ${ScriptPath}/ARMoutput.py -f ${Run}.txt -m $minevents -x $XCoord -y $YCoord -z $ZCoord -l $set_log -e ${L} -t $title -b yes"
     python3 ${ScriptPath}/ARMoutput.py -f ${Run}.txt -m $minevents -x $XCoord -y $YCoord -z $ZCoord -l $set_log -e ${L} -b yes -r ${Run} -i ${Isotope} &> ARM.${Run}.${L}keV.log &
   done
done

echo "INFO: Waiting for all python instances to finish"
wait

