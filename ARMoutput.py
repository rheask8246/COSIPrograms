###############################################################################################################################################################################
#Written by Rhea Senthil Kumar
###############################################################################################################################################################################

import ROOT as M
from math import pi
import argparse
import Helper as h
import multiprocessing as mp
from os import path
pool = mp.Pool(mp.cpu_count())

#################################################################################################################################################################################

# Load MEGAlib into ROOT
M.gSystem.Load("$(MEGALIB)/lib/libMEGAlib.so")

# Initialize MEGAlib
G = M.MGlobal()
G.Initialize()

# We are good to go ...
GeometryName = "/volumes/selene/users/rhea/geomega/COSI.DetectorHead.geo.setup"

parser = argparse.ArgumentParser(description='Create comparison of ARM plots from event reconstruction files and source location.')
parser.add_argument('-f', '--filename', default='ComptonTrackIdentification.p1.sim.gz', help='txt file name used for calculating ARM. Contains paths to tra files.')
parser.add_argument('-m', '--minevents', default='1000000', help='Minimum number of events to use')
parser.add_argument('-x', '--xcoordinate', type=float, default='26.1', help='X coordinate of position in 3D Cartesian coordinates')
parser.add_argument('-y', '--ycoordinate', type=float, default='0.3', help='Y coordinate of position in 3D Cartesian coordinates')
parser.add_argument('-z', '--zcoordinate', type=float, default='64', help='Z coordinate of position in 3D Cartesian coordinates') 
parser.add_argument('-l', '--logarithmic', type=str, default='no', help='If set to yes, displays ARM plot on a logarithmic-scaled y-axis.') 
parser.add_argument('-e', '--energy', type=float, default='662', help='Peak energy value for source. Outputs ARM histograms with a +-1.5% energy window.')
parser.add_argument('-t', '--title', type=str, default='"ARM Plot for Compton Events"', help='Title for ARM Plot')
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
    
###################################################################################################################################################################################

#Read in Files
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
    
#Create Histogram list and color
HistARMlist = []
for i in range(0, len(trafiles)):
    HistARMlist.append(M.TH1D("ARM Plot of Compton events" + str(i), title, 3601, -180, 180))
    
HistARMlist[0].SetLineColor(M.kRed)
if len(HistARMlist) >= 2: 
  HistARMlist[1].SetLineColor(M.kGreen)
if len(HistARMlist) >= 3: 
  HistARMlist[2].SetLineColor(M.kBlue)
if len(HistARMlist) >= 4: 
  HistARMlist[3].SetLineColor(M.kBlack)

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
            print(ARM_value)
            HistARMlist[y].Fill(Event.GetARMGamma(M.MVector(X, Y, Z))*(180.0/pi));
        elif Event.GetType() == M.MPhysicalEvent.c_Photo:
            pass

#Parallelizing
FWHMs = [None]*len(trafiles)
RMSs = [None]*len(trafiles)
Peaks = [None]*len(trafiles)
#if __name__ == '__main__':
for i in range(0, len(trafiles)):
    FWHMs[i] = pool.apply(h.bootstrapFWHM, args=(HistARMlist[i], 1000,))
    RMSs[i] = pool.apply(h.bootstrapRMS, args=(HistARMlist[i], 1000,))
    Peaks[i] = pool.apply(h.bootstrapPeak, args=(HistARMlist[i], 1000,))
pool.close()
pool.join()

#############################################################################################################################################################################

#Draw Histogram, Set Up Canvas

max = HistARMlist[0].GetMaximum()
for m in range(1, len(trafiles)):
    if HistARMlist[m].GetMaximum()>max:
        max = HistARMlist[m].GetMaximum()
for m in range(0, len(trafiles)):
    HistARMlist[m].SetMaximum(1.1*max)

CanvasARM = M.TCanvas("CanvasARM", title, 650, 800)
print("Drawing ARM histograms for each method...")
for m in range(0, len(trafiles)):
    if log == 'yes':
        M.gPad.SetLogy()
        HistARMlist[0].GetYaxis().SetTitle("Counts [logarithmic]")
        HistARMlist[m].Draw("same")
    else:
        HistARMlist[0].GetYaxis().SetTitle("Counts")
        HistARMlist[m].Draw("same")
HistARMlist[0].SetTitle(title)
HistARMlist[0].GetXaxis().SetTitle("ARM [deg]")
HistARMlist[0].GetXaxis().CenterTitle()
HistARMlist[0].GetYaxis().CenterTitle()
HistARMlist[0].GetYaxis().SetTitleOffset(1.7)

CanvasARM.cd()
CanvasARM.SetGridx()
CanvasARM.SetBottomMargin(0.5)

#Create Legend [Method, RMS Value, Peak Height, Total Count, FWHM]
print("Creating legend...")
Header = M.TH1D("Legend Header placeholder", " ", 1, -180, 180)
Header.SetLineColor(M.kWhite)
legend = M.TLegend(0.15, 0.35, 0.85, 0.1)
legend.SetTextSize(0.017)
legend.SetNColumns(5)

legend.AddEntry(Header, "Analysis Methods", "l")
legend.AddEntry(Header, "RMS Value", "l")
legend.AddEntry(Header, "Peak Height", "l")
legend.AddEntry(Header, "Total Count", "l")
legend.AddEntry(Header, "FWHM", "l")

legend.AddEntry(HistARMlist[0], "Classic Method", "l")
legend.AddEntry(HistARMlist[0], str(round(HistARMlist[0].GetRMS(), 2)) + "+-" + str(RMSs[0]), "l")
legend.AddEntry(HistARMlist[0], str(h.getMaxHist(HistARMlist[0])) + "+-" + str(Peaks[0]), "l")
legend.AddEntry(HistARMlist[0], str(HistARMlist[0].GetEntries()), "l") 
legend.AddEntry(HistARMlist[0], str(h.getFWHM(HistARMlist[0])) + "+-"+ str(FWHMs[0]), "l")

if len(HistARMlist) >= 2: 
  legend.AddEntry(HistARMlist[1], "Bayes Method", "l")
  legend.AddEntry(HistARMlist[1], str(round(HistARMlist[1].GetRMS(), 2)) + "+-" + str(RMSs[1]), "l")
  legend.AddEntry(HistARMlist[1], str(h.getMaxHist(HistARMlist[1])) + "+-" + str(Peaks[1]), "l")
  legend.AddEntry(HistARMlist[1], str(HistARMlist[1].GetEntries()), "l")
  legend.AddEntry(HistARMlist[1], str(h.getFWHM(HistARMlist[1])) + "+-"+ str(FWHMs[1]), "l")

if len(HistARMlist) >= 3: 
  legend.AddEntry(HistARMlist[2], "MLP Method", "l")
  legend.AddEntry(HistARMlist[2], str(round(HistARMlist[2].GetRMS(), 2)) + "+-" + str(RMSs[2]), "l")
  legend.AddEntry(HistARMlist[2], str(h.getMaxHist(HistARMlist[2])) + "+-" + str(Peaks[2]), "l")
  legend.AddEntry(HistARMlist[2], str(HistARMlist[2].GetEntries()), "l")
  legend.AddEntry(HistARMlist[2], str(h.getFWHM(HistARMlist[2])) + "+-"+ str(FWHMs[2]), "l")

if len(HistARMlist) >= 4: 
  legend.AddEntry(HistARMlist[3], "RF Method", "l")
  legend.AddEntry(HistARMlist[3], str(round(HistARMlist[3].GetRMS(), 2)) + "+-" + str(RMSs[3]), "l")
  legend.AddEntry(HistARMlist[3], str(h.getMaxHist(HistARMlist[3])) + "+-" + str(Peaks[3]), "l")
  legend.AddEntry(HistARMlist[3], str(HistARMlist[3].GetEntries()), "l")
  legend.AddEntry(HistARMlist[3], str(h.getFWHM(HistARMlist[3])) + "+-"+ str(FWHMs[3]), "l")

legend.Draw()

CanvasARM.Update()

#create txt file with comparable metrics
methods = ["Classic Method", "Bayes Method", "MLP Method", "RF Method"]
print("writing to a txt file...")
#if not path.exists("log.FileName.txt"):
metrics_file = open(training+".log.txt", "a+")

#metrics_file.write("Length of FWHMS: " + str(len(FWHMs)) + "\n")
#metrics_file.write("Length of HistARMlist: "+ str(len(HistARMlist))+ "\n")
metrics_file.write(args.filename + ": ")
for i in range(0, len(FWHMs)):
    metrics_file.write(str(h.getFWHM(HistARMlist[i])) + "\t")
#    metrics_file.write(str(FWHMs[i]) + "\t")
for i in range(0, len(FWHMs)):
    metrics_file.write(str(round(HistARMlist[i].GetRMS(), 2)) + "\t")
#    metrics_file.write(str(RMSs[i]) + "\t")
metrics_file.write("\n")
metrics_file.close()
#else:
#    metrics_file = open("log.FileName.txt", "a+")
#    metric_file.write("Energy Line: " + str(energy) + "\t")
#    for i in range(0, len(FWHMs)):
#        metrics_file.write(str(FWHMs[i]) + "\t")
#    for i in range(0, len(FWHMs)):    
#        metrics_file.write(str(RMSs[i]) + "\t")
#    metrics_file.write("\n")
#    metrics_file.close()

# Prevent the canvases from being closed

if Batch == False:
    import os
    print("ATTENTION: Please exit by clicking: File -> Close ROOT! Do not just close the window by clicking \"x\"")
    print("           ... and if you didn't honor this warning, and are stuck, execute the following in a new terminal: kill " + str(os.getpid()))
    M.gApplication.Run()
if Batch == True:
    CanvasARM.SaveAs("Results_{}_{}_{}keV.pdf".format(run, isotope, energy))
    
