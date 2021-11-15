################################################################################
#Written by Rhea Senthil Kumar
################################################################################

#imports and setup
import ROOT as M
from math import pi
import argparse
import Helper as h
import multiprocessing as mp
from os import path
pool = mp.Pool(mp.cpu_count())

################################################################################
# Load MEGAlib into ROOT
M.gSystem.Load("$(MEGALIB)/lib/libMEGAlib.so")

# Initialize MEGAlib
G = M.MGlobal()
G.Initialize()

# We are good to go ...
GeometryName = "/volumes/selene/users/rhea/geomega/COSI.DetectorHead.geo.setup"

parser = argparse.ArgumentParser(description='Compare output parameters from event reconstruction files and source location.')
parser.add_argument('-f', '--filename', default='test.txt', help='txt file name used for calculating ARM. Contains path to tra file.')
parser.add_argument('-m', '--minevents', default='1000000', help='Minimum number of events to use')
parser.add_argument('-x', '--xcoordinate', type=float, default='26.1', help='X coordinate of position in 3D Cartesian coordinates')
parser.add_argument('-y', '--ycoordinate', type=float, default='0.3', help='Y coordinate of position in 3D Cartesian coordinates')
parser.add_argument('-z', '--zcoordinate', type=float, default='64', help='Z coordinate of position in 3D Cartesian coordinates')
parser.add_argument('-l', '--logarithmic', type=str, default='no', help='If set to yes, displays ARM plot on a logarithmic-scaled y-axis.')
parser.add_argument('-e', '--energy', type=float, default='662', help='Peak energy value for source. Outputs ARM histograms with a +-1.5% energy window.')
parser.add_argument('-t', '--title', type=str, default='Output Parameters Sorted by Compton Angle', help='Title for ARM Plot')
parser.add_argument('-b', '--batch', type=str, default='no', help='If set to yes, runs program in batch mode.')
parser.add_argument('-i', '--isotope', type=str, default='none', help='The name of the isotope')
parser.add_argument('-r', '--run', type=str, default='none', help='The name of the run')
parser.add_argument('-p', '--training', type=str, default='none', help='The name of the training output file')

args = parser.parse_args()

if args.filename != "":
  FileName = args.filename

X = float(args.xcoordinate)
Y = float(args.ycoordinate)
Z = float(args.zcoordinate)
print("INFO: Using location ({}/{}/{})".format(X, Y, Z))

if args.logarithmic != "":
    log = args.logarithmic

energy = args.energy
low_e = 0.985 * float(args.energy)
high_e = 1.015 * float(args.energy)

if int(args.minevents) < 1000000:
  MinEvents = int(args.minevents)

if args.title != "":
    title = args.title

run=args.run
isotope=args.isotope
training = args.training

title = "{} ({}, {} keV): ARM comparison ".format(run, isotope, energy)

Batch = False
if args.batch == 'yes':
    M.gROOT.SetBatch(True)
    Batch = True

################################################################################

#Read in file
trafiles = []
f = open(args.filename, "r")
line = str(f.readline()).strip()
while line:
  trafiles.append(line)
  print(trafiles[-1])
  line = str(f.readline()).strip()

# Load geometry:
Geometry = M.MDGeometryQuest()
if Geometry.ScanSetupFile(M.MString(GeometryName)) == True:
  print("Geometry " + GeometryName + " loaded!")
else:
  print("Unable to load geometry " + GeometryName + " - Aborting!")
  quit()


#ARM histograms sorted by phi of the event, separated by 20 degrees
HistARMlist = []
for i in range(0, 18):
    HistARMlist.append(M.TH1D("Angle Range " + str(i), title, 3601, -180, 180))

print("Starting data collection...")

# Load file
for y in range(0, len(trafiles)):
    Reader = M.MFileEventsTra()
    if Reader.Open(M.MString(trafiles[y])) == False:
        print("Unable to open file " + FileName + ". Aborting!")
        quit()
    else:
        print("File " + FileName + " loaded!")


#Fill Histogram values
    counter = 0
    while counter <= 1000000:
        Event = Reader.GetNextEvent()
        counter = counter + 1
        if not Event:
            break

        if (Event.GetType() == M.MPhysicalEvent.c_Compton) and (low_e <= Event.Ei() <= high_e):
            ARM_value = Event.GetARMGamma(M.MVector(X, Y, Z))*(180.0/pi);
            print("ARM_value: " + str(ARM_value))
            print("Phi: " + str(Event.Phi()))
            if 0 < Event.Phi() and Event.Phi() <= 0.175:
                HistARMlist[0].Fill(ARM_value);
            elif 0.175 < Event.Phi() and Event.Phi() <= 0.349:
                HistARMlist[1].Fill(ARM_value);
            elif 0.349 < Event.Phi() and Event.Phi() <= 0.523:
                HistARMlist[2].Fill(ARM_value);
            elif 0.523 < Event.Phi() and Event.Phi() <= 0.698:
                HistARMlist[3].Fill(ARM_value);
            elif 0.698 < Event.Phi() and Event.Phi() <= 0.873:
                HistARMlist[4].Fill(ARM_value);
            elif 0.873 < Event.Phi() and Event.Phi() <= 1.222:
                HistARMlist[5].Fill(ARM_value);
            elif 1.222 < Event.Phi() and Event.Phi() <= 1.396:
                HistARMlist[6].Fill(ARM_value);
            elif 1.396 < Event.Phi() and Event.Phi() <= 1.571:
                HistARMlist[7].Fill(ARM_value);
            elif 1.571 < Event.Phi() and Event.Phi() <= 1.745:
                HistARMlist[8].Fill(ARM_value);
            elif 1.745 < Event.Phi() and Event.Phi() <= 1.919:
                HistARMlist[9].Fill(ARM_value);
            elif 1.919 < Event.Phi() and Event.Phi() <= 2.094:
                HistARMlist[10].Fill(ARM_value);
            elif 2.094 < Event.Phi() and Event.Phi() <= 2.269:
                HistARMlist[11].Fill(ARM_value);
            elif 2.269 < Event.Phi() and Event.Phi() <= 2.443:
                HistARMlist[12].Fill(ARM_value);
            elif 2.443 < Event.Phi() and Event.Phi() <= 2.618:
                HistARMlist[13].Fill(ARM_value);
            elif 2.618 < Event.Phi() and Event.Phi() <= 2.793:
                HistARMlist[14].Fill(ARM_value);
            elif 2.793 < Event.Phi() and Event.Phi() <= 2.967:
                HistARMlist[15].Fill(ARM_value);
            elif 2.967 < Event.Phi() and Event.Phi() <= 3.142:
                HistARMlist[16].Fill(ARM_value);
            else:
                pass
print("\n")
print("Data collection complete. Getting data analysis parameters..." + "\n")

#get back the fwhm and rms values
#v1: see these values printed
#TODO v2: store these values into a file

FWHMlist = []
RMSlist = []

for i in range(len(HistARMlist)):
    lower_range = i*10
    upper_range = (i+1)*10
    range_str = str(lower_range) + " to " + str(upper_range)
    FWHMlist.append(h.getFWHM(HistARMlist[i]))
    RMSlist.append(round(HistARMlist[i].GetRMS(), 2))

    #print(range_str)
    #print(str(h.getFWHM(HistARMlist[i])))
    print("FWHM for range: " + range_str + ": " + str(h.getFWHM(HistARMlist[i])))
    print("RMS for range: " + range_str + ": " + str(round(HistARMlist[i].GetRMS(), 2)))

print(FWHMlist)
print(RMSlist)
