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


#using Cs137 Run 043-046 for testing...
#Path to tra file: /volumes/selene/users/rhea/revan/Run043
#path to txt file: /volumes/selene/users/rhea/COSIPrograms/alltra.txt

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
for i in range(0, 9):
    HistARMlist.append(M.TH1D("Angle Range " + str(i), title, 3601, -180, 180))

"""
HistARMlist[0].SetLineColor(M.kRed)
HistARMlist[1].SetLineColor(M.kRed-9)
HistARMlist[2].SetLineColor(M.kMagenta)
HistARMlist[3].SetLineColor(M.kMagenta+2)
HistARMlist[4].SetLineColor(M.kViolet)
HistARMlist[5].SetLineColor(M.kBlue)
HistARMlist[6].SetLineColor(M.kBlue-10)
HistARMlist[7].SetLineColor(M.kCyan)
HistARMlist[8].SetLineColor(M.kCyan-7)
HistARMlist[9].SetLineColor(M.kBlue-2)
HistARMlist[10].SetLineColor(M.kGreen)
HistARMlist[11].SetLineColor(M.kGreen+2)
HistARMlist[12].SetLineColor(M.kGreen-9)
HistARMlist[13].SetLineColor(M.kYellow)
HistARMlist[14].SetLineColor(M.kYellow-6)
HistARMlist[15].SetLineColor(M.kOrange)
HistARMlist[16].SetLineColor(M.kOrange+7)
HistARMlist[17].SetLineColor(M.kRed+3)
"""

HistARMlist[0].SetLineColor(M.kRed)
HistARMlist[1].SetLineColor(M.kPink)
HistARMlist[2].SetLineColor(M.kMagenta)
HistARMlist[3].SetLineColor(M.kViolet)
HistARMlist[4].SetLineColor(M.kBlue)
HistARMlist[5].SetLineColor(M.kAzure)
HistARMlist[6].SetLineColor(M.kCyan)
HistARMlist[7].SetLineColor(M.kTeal)
HistARMlist[8].SetLineColor(M.kGreen)

#TODO: only works with one tra file right now
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
            print(Event.Phi())
            if 0 < Event.Phi() and Event.Phi() <= 0.349:
                HistARMlist[0].Fill(Event.GetARMGamma(M.MVector(X, Y, Z))*(180.0/pi));
            elif 20 < Event.Phi() and Event.Phi() <= 0.698:
                HistARMlist[1].Fill(Event.GetARMGamma(M.MVector(X, Y, Z))*(180.0/pi));
            elif 40 < Event.Phi() and Event.Phi() <= 1.047:
                HistARMlist[2].Fill(Event.GetARMGamma(M.MVector(X, Y, Z))*(180.0/pi));
            elif 60 < Event.Phi() and Event.Phi() <= 1.396:
                HistARMlist[3].Fill(Event.GetARMGamma(M.MVector(X, Y, Z))*(180.0/pi));
            elif 80 < Event.Phi() and Event.Phi() <= 1.745:
                HistARMlist[4].Fill(Event.GetARMGamma(M.MVector(X, Y, Z))*(180.0/pi));
            elif 100 < Event.Phi() and Event.Phi() <= 2.094:
                HistARMlist[5].Fill(Event.GetARMGamma(M.MVector(X, Y, Z))*(180.0/pi));
            elif 120 < Event.Phi() and Event.Phi() <= 2.443:
                HistARMlist[6].Fill(Event.GetARMGamma(M.MVector(X, Y, Z))*(180.0/pi));
            elif 140 < Event.Phi() and Event.Phi() <= 2.793:
                HistARMlist[7].Fill(Event.GetARMGamma(M.MVector(X, Y, Z))*(180.0/pi));
            elif 160 < Event.Phi() and Event.Phi() <= 3.142:
                HistARMlist[8].Fill(Event.GetARMGamma(M.MVector(X, Y, Z))*(180.0/pi));
            else:
                pass

"""
#Parallelizing
FWHMs = [None]*9
RMSs = [None]*9
Peaks = [None]*9
#if __name__ == '__main__':
for i in range(0, 9):
    FWHMs[i] = pool.apply(h.bootstrapFWHM, args=(HistARMlist[i], 1000,))
    RMSs[i] = pool.apply(h.bootstrapRMS, args=(HistARMlist[i], 1000,))
    Peaks[i] = pool.apply(h.bootstrapPeak, args=(HistARMlist[i], 1000,))
pool.close()
pool.join()
"""

#Draw Histogram, Set Up Canvas

max = HistARMlist[0].GetMaximum()
for m in range(1, len(HistARMlist)):
    if HistARMlist[m].GetMaximum() > max:
        max = HistARMlist[m].GetMaximum()
for m in range(0, len(HistARMlist)):
    HistARMlist[m].SetMaximum(1.1*max)

CanvasARM = M.TCanvas("CanvasARM", title, 650, 800)
print("Drawing ARM histograms for each method...")
for m in range(0, len(HistARMlist)):
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

legend.AddEntry(Header, "Scatter Angle Bins", "l")
legend.AddEntry(Header, "RMS Value", "l")
legend.AddEntry(Header, "Peak Height", "l")
legend.AddEntry(Header, "Total Count", "l")
legend.AddEntry(Header, "FWHM", "l")

for i in range(len(HistARMlist)):
    legend.AddEntry(HistARMlist[i], "Classic Method", "l")
    legend.AddEntry(HistARMlist[i], str(round(HistARMlist[i].GetRMS(), 2)), "l")
    legend.AddEntry(HistARMlist[i], str(h.getMaxHist(HistARMlist[i])), "l")
    legend.AddEntry(HistARMlist[i], str(HistARMlist[i].GetEntries()), "l")
    legend.AddEntry(HistARMlist[i], str(h.getFWHM(HistARMlist[i])), "l")
legend.Draw()
CanvasARM.Update()

#create txt file with comparable metrics
methods = ["Classic Method", "Bayes Method", "MLP Method", "RF Method"]
print("writing to a txt file...")
metrics_file = open(training+".log.txt", "a+")


metrics_file.write(args.filename + ": " + "\n")
metrics_file.write("FWHM:" + "\n")
for i in range(0, len(HistARMlist)):
    metrics_file.write(str(h.getFWHM(HistARMlist[i])) + "\t")
metrics_file.write("RMS:" + "\n")
for i in range(0, len(HistARMlist)):
    metrics_file.write(str(round(HistARMlist[i].GetRMS(), 2)) + "\t")
metrics_file.write("\n")
metrics_file.close()

"""
#get back the fwhm and rms values
#v1: see these values printed
#TODO v2: store these values into a file
for i in range(len(HistARMlist)):
    lower_range = i*20
    upper_range = (i+1)*20
    range_str = str(lower_range) + " to " + str(upper_range)
    print("FWHM for range: %s" + str(h.getFWHM(HistARMlist[i])) % range_str)
    print("RMS for range: %s" + str(round(HistARMlist[i].GetRMS(), 2)) % range_str)
"""

if Batch == False:
    import os
    print("ATTENTION: Please exit by clicking: File -> Close ROOT! Do not just close the window by clicking \"x\"")
    print("           ... and if you didn't honor this warning, and are stuck, execute the following in a new terminal: kill " + str(os.getpid()))
    M.gApplication.Run()
if Batch == True:
    CanvasARM.SaveAs("Results_{}_{}_{}keV.pdf".format(run, isotope, energy))
