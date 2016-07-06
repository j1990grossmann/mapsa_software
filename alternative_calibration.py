
from classes import *
import xml.etree.ElementTree
from xml.dom import minidom
from xml.etree.ElementTree import Element, SubElement, Comment
#import ROOT
#from ROOT import TGraph
import sys, select, os, array
from array import array
import ROOT
from ROOT import TGraph, TCanvas, gPad, TFile, TLine, THStack, TH1I, TH1F, TMath

import numpy as np

import matplotlib.pyplot as plt
from matplotlib.pyplot import show, plot

from optparse import OptionParser



#The current fast trimming procedure
def traditional_trim( xvec, yvec, prev_trim, trimdac, xdacval):
	"This changes a passed list into this function"
	halfmax = max(yvec)/2.0
	print yvec
	maxbin = np.where(yvec==max(yvec))
	for ibin in range(0,len(xvec)-1):		
		xval = xvec[ibin]
		xval1 = xvec[ibin+1]
		yval = yvec[ibin]
		yval1 = yvec[ibin+1]
		print "ibin " + str(ibin)
		#if xdacval<1000:
			#print "maxbin" + str(maxbin[0][0])
			#print "iy1 "+str(iy1)+" ibin " + str(ibin) + " xdacval "+ str(xdacval)
		if (yval1-halfmax)<0.0 and ibin>maxbin[0][0]:
			xdacval = (abs(yval-halfmax)*xval + abs(yval1-halfmax)*xval1)/(abs(yval-halfmax) + abs(yval1-halfmax))
			#print "ptrim " + str(prev_trim) 
			#print "halfmax " +  str(halfmax) + " xvec " + str(xvec[maxbin])
			#if abs(yval-halfmax)<abs(yval1-halfmax):
			#	xdacval = xval
			#else:
			#	xdacval = xval1
			#print "xdacval " + str(xdacval)
			trimdac = 31 + prev_trim - int(round(xdacval*1.456/3.75))
			xdacval = xdacval*1.456/3.75
			#print trimdac
			break	
		if ibin==len(xvec)-2:
			trimdac = int(prev_trim)
			print "UNTRIMMED"
			break
	return






parser = OptionParser()
parser.add_option('-s', '--setting', metavar='F', type='string', action='store',
default	=	'none',
dest	=	'setting',
help	=	'settings ie default, calibration, testbeam etc')

parser.add_option('-c', '--charge', metavar='F', type='int', action='store',
default	=	70,
dest	=	'charge',
help	=	'Charge for caldac')

parser.add_option('-w', '--shutterdur', metavar='F', type='int', action='store',
default	=	0xFFFFF,
dest	=	'shutterdur',
help	=	'shutter duration')


parser.add_option('-n', '--number', metavar='F', type='int', action='store',
default	=	0x5,
dest	=	'number',
help	=	'number of calstrobe pulses to send')

parser.add_option('-r', '--res', metavar='F', type='int', action='store',
default	=	1,
dest	=	'res',
help	=	'resolution 1,2,3... 1 is best')

parser.add_option('-y', '--string ', metavar='F', type='string', action='store',
default	=	'',
dest	=	'string',
help	=	'extra string')

parser.add_option('-t', '--type', metavar='TYPE', type='int', action='store',
default	=	0,
dest	=	'cal_type',
help	=	'Type of fast calibration to be performed: 0 standard, 1 experimental')

parser.add_option('-k', '--k_repetiions', metavar='REPETIONS', type='int', action='store',
default	=	1,
dest	=	'k_reps',
help	=	'K repetions of aquisitions with shutterduration s')


(options, args) = parser.parse_args()



a = uasic(connection="file://connections_test.xml",device="board0")
mapsa = MAPSA(a)
read = a._hw.getNode("Control").getNode('firm_ver').read()
a._hw.dispatch()
print "Running firmware version " + str(read)


#a._hw.getNode("Control").getNode("logic_reset").write(0x1)
#a._hw.dispatch()
a._hw.getNode("Control").getNode("MPA_clock_enable").write(0x1)
a._hw.dispatch()


no_mpa_light = 6
smode = 0x0
sdur = options.shutterdur


snum = options.number
sdel = 0xF
slen = 0xF
sdist = 0xFF



dcindex=1

buffnum=1



	
mpa = []  
for i in range(1,no_mpa_light+1):
		mpa.append(mapsa.getMPA(i))


Confnum=1
configarr = []
if options.setting=='calibration':
	CE=1
else:
	CE=0
SP=0

nshut = 1


config = mapsa.config(Config=1,string='default')
config.upload()


confdict = {'OM':[3]*6,'RT':[0]*6,'SCW':[0]*6,'SH2':[0]*6,'SH1':[0]*6,'THDAC':[0]*6,'CALDAC':[options.charge]*6,'PML':[1]*6,'ARL':[1]*6,'CEL':[CE]*6,'CW':[0]*6,'PMR':[1]*6,'ARR':[1]*6,'CER':[CE]*6,'SP':[SP]*6,'SR':[1]*6,'TRIMDACL':[31]*6,'TRIMDACR':[31]*6}
config.modifyfull(confdict) 

mapsa.daq().Strobe_settings(snum,sdel,slen,sdist,cal=CE)
x1 = array('d')
y1 = []


rangeval = options.k_reps
count_arr=np.zeros((no_mpa_light,256,48))
for xx in range(0,256):
	x = xx
	if x%options.res!=0:
		continue
	if x%10==0:
		print "THDAC " + str(x)

	config.modifyperiphery('THDAC',[x]*6)
	config.upload()
	config.write()
	for z in range (0,rangeval):
		mapsa.daq().Sequencer_init(smode,sdur)
		pix,mem = mapsa.daq().read_data(buffnum)
		ipix=0
		for p in pix:
			p.pop(0)
			p.pop(0)
			count_arr[ipix][x]=count_arr[ipix][x]+np.array(array('d',p))
			if (x==75 and ipix==0):
				print ipix
				print count_arr[ipix][x]
			if z ==(rangeval-1):
				y1.append([])
				y1[ipix].append(array('d',count_arr[ipix][x]))
			ipix+=1
	x1.append(x)
	
calibconfs = config._confs
calibconfsxmlroot = config._confsxmlroot


c3 = TCanvas('c3', '', 700, 900)
c3.Divide(2,3)
		
c1 = TCanvas('c1', '', 700, 900)
c1.Divide(2,3)
#The Precalibration curves
xvec =  np.array(x1, dtype='uint16')
thdacvv = []
yarrv = []
xdvals = []
linearr = []
xdacval = 0.
stackarr = []
for i in range(0,no_mpa_light):
	backup=TFile("plots/backup_preCalibration_"+options.string+"_MPA"+str(i)+".root","recreate")
	calibconfxmlroot	=	calibconfsxmlroot[i]
	xdvals.append(0.)
	c1.cd(i+1)
	thdacv = []
	yarr =  np.array(y1[i])
	linearr.append([])
	gr1 = []
	lines = []
	yarrv.append(yarr)
	stackarr.append(THStack('a','pixel curves;DAC Value (1.456 mV);Counts (1/1.456)'))
	# hstack = THStack('a','pixel curves;DAC Value (1.456 mV);Counts (1/1.456)')
	for iy1 in range(0,len(yarr[0,:])):
		yvec = yarr[:,iy1]
		if max(yvec)==0:
			print "zero"
		gr1.append(TH1I(str(iy1),';DAC Value (1.456 mV);Counts (1/1.456)',len(x1),0,x1[-1]))
		gr1[iy1].Sumw2(ROOT.kFALSE)
		for j in np.nditer(xvec):
			gr1[iy1].SetBinContent(gr1[iy1].FindBin(j),(np.array(yvec,dtype='int')[j]))
		gr1[iy1].Sumw2(ROOT.kTRUE)
		color=iy1%9+1
		gr1[iy1].SetLineColor(color)
		gr1[iy1].SetMarkerColor(color)
		gr1[iy1].SetFillColor(color)
		gr1[iy1].SetLineStyle(1)
		gr1[iy1].SetLineWidth(1)
		gr1[iy1].SetFillStyle(1)
		gr1[iy1].SetMarkerStyle(1)
		gr1[iy1].SetMarkerSize(.5)
		gr1[iy1].SetMarkerStyle(20)
		cloned = gr1[iy1].Clone()
		cloned.SetDirectory(0)
		stackarr[i].Add(cloned)
		if iy1==(len(yarr[0,:])-1):
			stackarr[i].Draw('nostack hist e1 x0')
			for lines1 in linearr[i]:
				#for j in np.nditer(xvec):
				lines1.Draw("same")
			if(stackarr[i].GetMaximum()>1):
				Maximum = TMath.Power(10,(round(TMath.Log10(stackarr[i].GetMaximum()))))
				stackarr[i].SetMinimum(.1)
				stackarr[i].SetMaximum(Maximum)
				gPad.SetLogy()
			gPad.Update()
		gr1[iy1].SetLineColor(1)
		gr1[iy1].SetMarkerColor(1)
		gr1[iy1].SetFillColor(1)
		gr1[iy1].Write(str(iy1))
		#Get prevous trim value for the channel
		if iy1%2==0:
			prev_trim = int(calibconfxmlroot[(iy1)/2+1].find('TRIMDACL').text)
		else:
			prev_trim = int(calibconfxmlroot[(iy1+1)/2].find('TRIMDACR').text)
		trimdac = 0
		# Now we have the routine to find the midpoint
		traditional_trim(xvec,yvec,prev_trim,trimdac,xdacval)
		xdvals[i]=xdacval
		thdacv.append(trimdac)
		lines.append(TLine(xdacval,.1,xdacval,cloned.GetMaximum()))
		linearr[i].append(lines[iy1])
		linearr[i][iy1].SetLineColor(2)
	thdacvv.append(thdacv)
	print thdacv

ave = 0
for x in xdvals:
	ave+=x/48.
ave/=6.


offset = []
avearr = []
mpacorr = []
for i in range(0,no_mpa_light):
	thdacv = thdacvv[i]
	ave15 = 0
	for j in thdacvv[i]:
		ave15+=j
	ave15/=len(thdacvv[i])
	avearr.append(ave15)
	mpacorr.append(xdvals[i]/48.-ave)
	
#print 'average correction'
#print avearr
#print mpacorr
for i in range(0,no_mpa_light):
	thdacv = thdacvv[i]
	range1 = min(thdacv)	
	range2 = max(thdacv)	
	offset.append(15-int(round(avearr[i]+mpacorr[i])))
#print offset

thdacvvorg = []
cols = [[],[],[],[],[],[]]
for iy1 in range(0,len(yarrv[0][0,:])):
	thdacvvorg.append(np.array(thdacvv)[:,iy1])
	upldac = []
	for i in range(0,no_mpa_light):
		thdacv = thdacvv[i]
		upldac.append(thdacv[iy1]+offset[i])


	for u in range(0,len(upldac)):
		upldac[u] = max(0,upldac[u])
		upldac[u] = min(31,upldac[u])
		if upldac[u]==31:
			cols[u].append(2)
		elif upldac[u]==0:
			cols[u].append(4)
		else:
			cols[u].append(1)
	#print upldac

	if iy1%2==0:
		config.modifypixel((iy1)/2+1,'TRIMDACL',upldac)
	else:
		config.modifypixel((iy1+1)/2,'TRIMDACR',upldac)


c1.Print('plots/Scurve_Calibration'+options.string+'_pre.root', 'root')
c1.Print('plots/Scurve_Calibration'+options.string+'_pre.pdf', 'pdf')
c1.Print('plots/Scurve_Calibration'+options.string+'_pre.png', 'png')
config.modifyperiphery('THDAC',[100]*6)
#config.upload()
#config.write()
for i in range(0,no_mpa_light):
	xmlrootfile = config._confsxmltree[i]
	print xmlrootfile
	a = config._confsxmlroot[i]
	print "writing data/Conf_calibrated_MPA"+str(i+1)+"_config1.xml"
	xmlrootfile.write("data/Conf_calibrated_MPA"+str(i+1)+"_config1.xml")


print "Testing Calibration"


config1 = mapsa.config(Config=1,string='calibrated')
config1.upload()

config1.modifyperiphery('OM',[3]*6)
config1.modifyperiphery('RT',[0]*6)
config1.modifyperiphery('SCW',[0]*6)
config1.modifyperiphery('SH2',[0]*6)
config1.modifyperiphery('SH1',[0]*6)
config1.modifyperiphery('THDAC',[0]*6)
config1.modifyperiphery('CALDAC', [options.charge]*6)
for x in range(1,25):
	config1.modifypixel(x,'PML', [1]*6)
	config1.modifypixel(x,'ARL', [1]*6)
	config1.modifypixel(x,'CEL', [CE]*6)
	config1.modifypixel(x,'CW', [0]*6)
	config1.modifypixel(x,'PMR', [1]*6)
	config1.modifypixel(x,'ARR', [1]*6)
	config1.modifypixel(x,'CER', [CE]*6)
	config1.modifypixel(x,'SP',  [SP]*6) 
	config1.modifypixel(x,'SR',  [1]*6) 

config1.write()


x1 = array('d')
y1 = []
for x in range(0,256):
			if x%options.res!=0:
				continue
			if x%10==0:
				print "THDAC " + str(x)

			config1.modifyperiphery('THDAC',[x]*6)
			config1.upload()
			config1.write()
	





			mapsa.daq().Sequencer_init(smode,sdur)
			pix,mem = mapsa.daq().read_data(buffnum)
			ipix=0
			for p in pix:

				p.pop(0)
				p.pop(0)
				#print p
				y1.append([])
				y1[ipix].append(array('d',p))
				# print str(p)

				ipix+=1
			x1.append(x)
			
	


c2 = TCanvas('c2', '', 700, 900)
c2.Divide(2,3)

xvec =  np.array(x1)
yarrv = []
gr2arr = []
means = []
for i in range(0,no_mpa_light):
		backup=TFile("plots/backup_postCalibration_"+options.string+"_MPA"+str(i)+".root","recreate")
		
		c2.cd(i+1)
		yarr =  np.array(y1[i])
		gr2arr.append([])
		gr2 = []
		means.append(0.)
		yarrv.append(yarr)
		for iy1 in range(0,len(yarr[0,:])):
			yvec = yarr[:,iy1]

			gr2.append(TGraph(len(x1)-1,array('d',xvec),array('d',yvec)))
			
			if iy1==0:

				gr2[iy1].SetTitle(';DAC Value (1.456 mV);Counts (1/1.456)')
				gr2arr[i].append(gr2[iy1])
				gr2arr[i][iy1].SetLineColor(cols[i][iy1])
				gr2arr[i][iy1].Draw()
				gr2[iy1].Write(str(iy1))

			else:
				gr2arr[i].append(gr2[iy1])
				gr2arr[i][iy1].SetLineColor(cols[i][iy1])
				gr2arr[i][iy1].Draw('same')
				gr2[iy1].Write(str(iy1))
			if(iy1==len(yarr[0,:])-1):
				gPad.Update()
			means[i]+=gr2[iy1].GetMean(1)
print 'Means'
for m in means:
	print m/48.

c2.Print('plots/Scurve_Calibration'+options.string+'_post.root', 'root')
c2.Print('plots/Scurve_Calibration'+options.string+'_post.pdf', 'pdf')
c2.Print('plots/Scurve_Calibration'+options.string+'_post.png', 'png')
#c3 = TCanvas('c2', '', 700, 600)
#gr2[4].Draw()
#gPad.Update()
#c3.Print('plots/test.pdf', 'pdf')
print ""
print "Done"


