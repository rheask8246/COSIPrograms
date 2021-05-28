#!/bin/bash

Geometry="/home/andreas/Science/Software/Nuclearizer/MassModel/COSI.DetectorHead.geo.setup"

# Step zero: Create list of runs:
Runs=""
for File in `ls ../Data/*.roa.gz`; do
#for File in `ls ../Data/Cs*.roa.gz`; do
  echo "RunElement#" | awk -F. '{print $2}'
  echo "${File}"
  Runs+=" $(basename ${File} .roa.gz)"
done

echo "Runs: ${Runs}"


# Step one: Convert everything to evta files
for Run in ${Runs}; do
  mwait -p=nuclearizer -i=cores

  InputFile="../Data/${Run}.roa.gz"
  OutputFile="${Run}.evta.gz"
  nuclearizer -a -g ${Geometry} -c Nuclearizer_ER_Data.cfg -C ModuleOptions.XmlTagMeasurementLoaderROA.FileName=${InputFile} -C ModuleOptions.XmlTagEventSaver.FileName=${OutputFile} &
done
wait


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
    grep "TMVA" Revan_ER_MLP.cfg #Revan_ER_Bayes.cfg
    mkdir -p /volumes/selene/users/rhea/revan/NewRun
    cd /volumes/selene/users/rhea/revan/NewRun
    ISOTOPE=$(echo ${Run} | awk -F. '{print $2}')
    if [[${A} == Classic ]] || [[${A} == Bayes ]]; then
      revan -a -n -c Revan_ER_${A}.cfg -g ${Geometry} -f ${Run}.evta.gz &
    elif [[${A} == MLP ]] || {{${A} == RF}}; then
      revan -a -n -c Revan_ER_${A}.cfg -g ${Geometry} -f ${Run}.evta.gz -C CSRTMVAFile==</volumes/crius/users/andreas/COSI_2016/ER?Sims/${ISOTOPE}/AllSky/ComptonTMVA.v2.tmva -C CSRTMVAMethods=${A} &
    else
      echo "Error when running Revan. Check geometry, file names, or configuration."
    fi
  done
  wait
  for Run in ${Runs}; do
    mv ${Run}.tra.gz ${Run}.${A}.tra.gz
  done
done

for Run in ${Runs}; do
  # Run Rhea's program
  file="${Run}.${A}.tra.gz"
  i = 1
  while read line; do
  #Reading each line
  echo "Line No, $i: $line"
  i = $((i+1))
  done < $file
  #do ARM program
  python3 /volumes/selene/users/rhea/COSIPrograms/ARMoutput.py
done

#

