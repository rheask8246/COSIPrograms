import ROOT as M 
from math import pi
import argparse

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
parser.add_argument('-t', '--title', type=str, default='ARM Plot for Compton Events', help='Title for ARM Plot')

args = parser.parse_args()

if args.filename != "":
  FileName = args.filename

X = float(args.xcoordinate)
Y = float(args.ycoordinate)
Z = float(args.zcoordinate)

if args.logarithmic != "":
    log = args.logarithmic

low_e = 0.985 * float(args.energy)
high_e = 1.015 * float(args.energy)

if int(args.minevents) < 1000000:
  MinEvents = int(args.minevents)

if args.title != "":
    title = args.title

trafiles = [None, None, None, None]
f = open(args.filename, "r")
for x in range(0,4):
    trafiles[x] = str(f.readline()).strip()
    print(trafiles[x])


###################################################################################################################################################################################

# Load geometry:
Geometry = M.MDGeometryQuest()
if Geometry.ScanSetupFile(M.MString(GeometryName)) == True:
  print("Geometry " + GeometryName + " loaded!")
else:
  print("Unable to load geometry " + GeometryName + " - Aborting!")
  quit()
    
#Create Histogram list and color
HistARMlist = [None, None, None, None]
for i in range(0,4):
    HistARMlist[i] = M.TH1D("ARM Plot of Compton events" + str(i), title, 200, -180, 180)
    
HistARMlist[0].SetLineColor(M.kRed)
HistARMlist[1].SetLineColor(M.kGreen)
HistARMlist[2].SetLineColor(M.kBlue)
HistARMlist[3].SetLineColor(M.kBlack)

# Load file
for y in range(0,4):
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
            ARM_value = Event.GetARMGamma((M.MVector(X, Y, Z)), M.MCoordinateSystem.c_Cartesian3D)*(180/pi);
            print(ARM_value)
            HistARMlist[y].Fill(Event.GetARMGamma(M.MVector(X, Y, Z), M.MCoordinateSystem.c_Cartesian3D)*(180/pi));
        elif Event.GetType() == M.MPhysicalEvent.c_Photo:
            pass

#############################################################################################################################################################################

#Draw Histogram, Set Up Canvas
CanvasARM = M.TCanvas()
print("Drawing ARM histograms for each method...")
for m in range(0,4):
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

CanvasARM.cd()
CanvasARM.SetGridx()

#Create Legend [Method, RMS Value, Peak Height, Total Count, FWHM]
print("Creating legend...")
legend = M.TLegend(0.60, 0.10, 1, 0)
legend.SetHeader("Analysis Methods, RMS Values, Total Count", "C")
legend.SetNColumns(3)

legend.AddEntry(HistARMlist[0], "Classic Method", "l")
legend.AddEntry(HistARMlist[0], str(HistARMlist[0].GetRMS()), "l")
#peak height
legend.AddEntry(HistARMlist[0], str(HistARMlist[0].GetEntries()), "l") 

legend.AddEntry(HistARMlist[1], "Bayes Method", "l")
legend.AddEntry(HistARMlist[1], str(HistARMlist[1].GetRMS()), "l")
#peak height
legend.AddEntry(HistARMlist[1], str(HistARMlist[1].GetEntries()), "l")

legend.AddEntry(HistARMlist[2], "MLP Method", "l")
legend.AddEntry(HistARMlist[2], str(HistARMlist[2].GetRMS()), "l")
#peak height
legend.AddEntry(HistARMlist[2], str(HistARMlist[2].GetEntries()), "l")

legend.AddEntry(HistARMlist[3], "RF Method", "l")
legend.AddEntry(HistARMlist[3], str(HistARMlist[3].GetRMS()), "l")
#peak height
legend.AddEntry(HistARMlist[3], str(HistARMlist[3].GetEntries()), "l")

legend.Draw()

CanvasARM.Update()

# Prevent the canvases from being closed
import os
print("ATTENTION: Please exit by clicking: File -> Close ROOT! Do not just close the window by clicking \"x\"")
print("           ... and if you didn't honor this warning, and are stuck, execute the following in a new terminal: kill " + str(os.getpid()))
M.gApplication.Run()
