#Functions related to data aquisition at the MAPSA level - starting calibration and data taking 
#as well as loops of MPA_daq readout objects for ease of use 

from MPA import *
from MPA_daq import *
from MAPSA_functions import *
class MAPSA_daq:
	
	def __init__(self, hw):
		self._hw     = hw

		self._Shutter   	= 	self._hw.getNode("Shutter")
		self._Control		=	self._hw.getNode("Control")
		self._Configuration 	=  	self._hw.getNode("Configuration")
		self._Readout 		=  	self._hw.getNode("Readout")
		self._Sequencer		=	self._Control.getNode("Sequencer") 

		self._puls_num   = self._Shutter.getNode("Strobe").getNode("number")
		self._puls_len   = self._Shutter.getNode("Strobe").getNode("length")
		self._puls_dist  = self._Shutter.getNode("Strobe").getNode("distance")
		self._puls_del   = self._Shutter.getNode("Strobe").getNode("delay")
		self._shuttertime	= self._Shutter.getNode("time")
		#self._shuttermode	= self._Shutter.getNode("mode")

		self._sequencerbusy  = self._Sequencer.getNode("busy")
		self._calib  = self._Control.getNode("calibration")
		self._read  = self._Control.getNode("readout")
	
		self._buffers  = self._Sequencer.getNode("buffers_index")
		self._data_continuous  = self._Sequencer.getNode("datataking_continuous")

		self._memory  = self._Readout.getNode("Memory")
		self._counter  = self._Readout.getNode("Counter")
		self._readmode  = self._Control.getNode("readout")
		#self._readbuff  = self._Readout.getNode("buffer_num")

    		self._clken = self._Control.getNode("MPA_clock_enable") 		  
    		self._testbeam = self._Control.getNode("testbeam_mode") 		
    		self._testbeamclock = self._Control.getNode("testbeam_clock") 		    

				

	def _waitsequencer(self):
		i=0
		busyseq = self._sequencerbusy.read()
		self._hw.dispatch()
		while busyseq:
			busyseq = self._sequencerbusy.read()
			self._hw.dispatch()

			time.sleep(0.001)
			i+=1
			if i>100:
				print "timeout"
				return 0
		
		return 1


#	def start_readout(self,buffer_num=1,mode=0x1):
#
#		self._readbuff.write(buffer_num-1)
#		self._readmode.write(mode)
#		self._hw.dispatch()



	def read_data(self,buffer_num=1,tb=0):
		counts = []  
		mems = []  
		for i in range(1,7):
			pix = []
			mem = []
			pix,mem = MPA(self._hw,i).daq().read_data(buffer_num,tb)

			counts.append(pix) 
			mems.append(mem)
		return counts,mems

	def read_trig(self,buffer_num=1):


		total_triggers = a._hw.getNode("Control").getNode('total_triggers').read()
		trigger_counter = a._hw.getNode("Control").getNode('trigger_counter').getNode('buffer_'+str(buffer_num)).read()
		Offset_BEAM = a._hw.getNode("Control").getNode('trigger_offset_BEAM').getNode('buffer_'+str(buffer_num)).readBlock(2048)
		Offset_MPA = a._hw.getNode("Control").getNode('trigger_offset_MPA').getNode('buffer_'+str(buffer_num)).readBlock(2048)
		a._hw.dispatch()

		return total_triggers,trigger_counter,Offset_BEAM,Offset_MPA

	def read_memory(self,mode,buffer_num=1):
		BXs = [] 
		datas = [] 
		counts = [] 

		for i in range(1,7):
			BX, data, count = MPA(self._hw,i).daq().read_memory(mode,buffer_num)
			BXs.append(BX) 
			datas.append(data) 
			counts.append(count) 

		return 	BXs,datas,counts



	def Strobe_settings(self,snum,sdel,slen,sdist,cal = 1):

		self._puls_num.write(snum)
		self._puls_del.write(sdel)
		self._puls_len.write(slen)
		self._puls_dist.write(sdist)

		self._calib.write(cal)
		self._hw.dispatch()
		#time.sleep(0.001)
	

	def Testbeam_init(self,clock='glib'):
		if clock=='glib':
			clkset=0x0
		if clock=='testbeam':
			clkset=0x1
		#self._hw.getNode("Control").getNode('testbeam_calibration').write(calib)
		self._hw.getNode("Control").getNode('testbeam_clock').write(clkset)
		self._hw.getNode("Control").getNode('testbeam_mode').write(0x1)
		self._hw.dispatch()

			
	def Shutter_open(self,smode,sdur,mem=1):
		self._shuttertime.write(sdur)	
		self._hw.getNode("Control").getNode('testbeam_mode').write(0x0)
		self._read.write(mem)
		self._hw.dispatch()		
		self._Sequencer.getNode('datataking_continuous').write(0x0)
		self._Sequencer.getNode('buffers_index').write(0x0)
		self._hw.dispatch()

		#self._waitsequencer()
