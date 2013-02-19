#! /usr/bin/env python
# -*- coding:utf-8 -*- 

##############################################################################
## license : GPLv3+
##============================================================================
##
## File :        BunchAnalyzer.py
## 
## Project :     Filling Pattern from the FCT
##
## description : Python source with the class that has the appropriate methods
##               to...
##
## This file is part of Tango device class.
## 
## Tango is free software: you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation, either version 3 of the License, or
## (at your option) any later version.
## 
## Tango is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
## 
## You should have received a copy of the GNU General Public License
## along with Tango.  If not, see <http://www.gnu.org/licenses/>.
##
## $Author :      Laura Torino$ (first developer)
##
## $Revision :    $
##
## $Date :        $
##
## $HeadUrl :     $
##
## copyleft :    Cells / Alba Synchrotron
##               Cerdanyola/Bellaterra
##               Spain
##############################################################################

###############################################################################
#  This program analyses data coming from a FCT:
#  - Data are uploaded
#  - Low band filter is applied (500 MHz-1 GHz...)
#  - Cutoff frequency as input(later to be fixed, probably 700 MHz)
#  - Starting analyzing point fixed at 127 bins = 6.2497 ns
#  - Consecutive peaks are considered only if one is positive and the other 
#    is above the negative threshold of 0.05*minimum of the filtered signal
#  - Frequency and the Delta t (time window) as input (from the machine)
#    DONE, to uncoment
#  - Number of bucket  
#  - Number of filled bucket 
#  - Number of spuorious bunches
#  - Maximum peak to peak amplitude
###############################################################################

META = u"""
    $URL: https://svn.code.sf.net/p/tango-ds/code/Servers/Calculation/FillingPatternFCT/src/BunchAnalyzer.py $
    $LastChangedBy: sergiblanch $
    $Date: 2012-12-12 11:33:48 +0100 (Wed, 12 Dec 2012)$
    $Rev: 5901 $
    License: GPL3+
    Author: Laura Torino
""".encode('latin1')

import time
from numpy import *
from copy import copy,deepcopy
from scipy import signal
import PyTango

class BunchAnalyzer:
    def __init__(self,parent=None,timingDevName=None,scopeDevName=None,
                  timingoutput=0,delayTick=18281216,threashold=1,
                  nAcquisitions=30,cyclicBuffer=None,
                  startingPoint=906,scopeSampleRate=4.0e9,
                  max_cyclicBuf=250,alarm_cyclicBuf=50):
        self._parent=parent
        try:
            self._timingDevName = timingDevName
            self._timingProxy = PyTango.DeviceProxy(self._timingDevName)
        except Exception,e:
            self._timingProxy = None
        try:
            self._scopeDevName = scopeDevName
            self._scopeProxy = PyTango.DeviceProxy(self._scopeDevName)
        except Exception,e:
            self._scopeProxy = None
        self._timingoutput = timingoutput
        self._delayTick = delayTick
        self._threshold = threashold
        self._nAcquisitions = nAcquisitions
        self._cyclicBuffer = cyclicBuffer
        self._t0 = []
        self._tf = []
        self._startingPoint = startingPoint
        self._scopeSampleRate = scopeSampleRate
        self._rfFrequency = 499650374.85
        self.__max_cyclicBuf = max_cyclicBuf
        self.__alarm_cyclicBuf = alarm_cyclicBuf
        #outputs
        self._filledBunches = 0
        self._spuriousBunches = 0
        self._yFiltered = []
        self._bunchIntensity = []
        self._resultingFrequency = 0

    ####
    # Auxiliary setters and getters to modify the behaviour from the device server
    def getTimingDevName(self):
        return self._timingDevName
    def getTimingDevice(self):
        return self._timingProxy
    def setTimingDevName(self,name):
        self._timingDevName = name
        self._timingProxy = PyTango.DeviceProxy(self._timingDevName)
    def getScopeDevName(self):
        return self._scopeDevName
    def getScopeDevice(self):
        return self._scopeProxy
    def setScopeDevName(self,name):
        self._scopeDevName = name
        self._scopeProxy = PyTango.DeviceProxy(self._scopeDevName)
    def getTimingoutput(self):
        return self._timingoutput
    def setTimingoutput(self,value):
        self._timingoutput = value
    def getDelayTick(self):
        return self._delayTick
    def setDelayTick(self,value):
        self._delayTick = value
    def getThreshold(self):
        return self._threshold
    def setThreshold(self,value):
        self._threshold = value
    def getNAcquisitions(self):
        return self._nAcquisitions
    def setNAcquisitions(self,value):
        self._nAcquisitions = value
    def getCyclicBuffer(self):
        return self._cyclicBuffer
    def setCyclicBuffer(self,buffer):
        self._cyclicBuffer = buffer
    def getStartingPoint(self):
        return self._startingPoint
    def setStartingPoint(self,value):
        self._startingPoint = value
    def getScopeSampleRate(self):
        return self._scopeSampleRate
    def setScopeSampleRate(self,value):
        self._scopeSampleRate = value
    def getRfFrequency(self):
        return self._rfFrequency
    def setRfFrequency(self,value):
        self._rfFrequency = value
    def getFilledBunches(self):
        return self._filledBunches
    def getSpuriousBunches(self):
        return self._spuriousBunches
    def getBunchIntensity(self):
        return self._bunchIntensity
    def getResultingFrequency(self):
        return self._resultingFrequency
    # done auxiliary setters and getters to modify the behaviour from the device server
    ####

    ####
    # auxiliary methods to manage events
    def debug(self,msg):
        try:
            if self._parent:
                self._parent.debug_stream(msg)
            else:
                print("debug: %s"%(msg))
        except: print("cannot print in debug stream (%s)"%msg)
    def warn(self,msg):
        try:
            if self._parent:
                self._parent.warn_stream(msg)
            else:
                print("warn:  %s"%(msg))
        except: print("cannot print in warn stream (%s)"%msg)
    def error(self,msg):
        try:
            if self._parent:
                self._parent.error_stream(msg)
            else:
                print("error: %s"%(msg))
        except: print("cannot print in error stream (%s)"%msg)
    def subscribe_event(self,attrName):
        self._scopeChAttrEvent = self._scopeProxy.subscribe_event(attrName,
                                                                  PyTango.EventType.CHANGE_EVENT,
                                                                  self)
    def unsubscribe_event(self):
        self._scopeProxy.unsubscribe_event(self._scopeChAttrEvent)
        self._parent.change_state(PyTango.DevState.OFF)

    #a callback method for the scope channel attribute
    def push_event(self,event):
        try:
            if event != None:
                if event.attr_value != None and event.attr_value.value != None:
                    self.debug("PushEvent() %s: array of %d elements"%(event.attr_name,event.attr_value.value.size))
                else:
                    self.debug("PushEvent() %s: value has None type"%(event.attr_name))
        except Exception,e:
            self.error("PushEvent() exception %s:"%(e))
        #timestamps when this starts
        t0 = time.time()
        eventList = []
        #populate the cyclicBuffer
        self._cyclicBuffer.append(event.attr_value.value)
        #state changes between STANDBY<->ON when the len(cyclicBuffer)<nAcquitions
        bufLen = len(self._cyclicBuffer)
        if bufLen < self._nAcquisitions:
            if not self._parent.get_state() in [PyTango.DevState.STANDBY,
                                                PyTango.DevState.ALARM]:
                self._parent.change_state(PyTango.DevState.STANDBY)
            if bufLen >= self.__alarm_cyclicBuf:
                eventList.append(['nAcquisitions',len(self._cyclicBuffer),PyTango.AttrQuality.ATTR_ALARM])
            else:
                eventList.append(['nAcquisitions',len(self._cyclicBuffer),PyTango.AttrQuality.ATTR_CHANGING])
        else:
            while len(self._cyclicBuffer) > self._nAcquisitions:
                self._cyclicBuffer.pop(0)
            if not self._parent.get_state() in [PyTango.DevState.ON,
                                                PyTango.DevState.ALARM]:
                self._parent.change_state(PyTango.DevState.ON)
            if len(self._cyclicBuffer) >= self.__alarm_cyclicBuf:
                eventList.append(['nAcquisitions',len(self._cyclicBuffer),PyTango.AttrQuality.ATTR_ALARM])
            else:
                eventList.append(['nAcquisitions',len(self._cyclicBuffer),PyTango.AttrQuality.ATTR_VALID])
        eventList.append(['CyclicBuffer',self._cyclicBuffer,PyTango.AttrQuality.ATTR_CHANGING])
        self._parent.fireEventsList(eventList)
        #TODO: are there any scope attribute to reread when a new waveform is received?
        #      or any that must be reread after N waveforms received
        #with the current values on the cyclic buffer, analyze it.
        #FIXME: why call delay when we are maintaining the delayTick
        self.debug("Time delay: %d (DelayTick: %d)"%(self.delay(),self.getDelayTick()))
        #Usefull variables
        SampRate = self._scopeSampleRate
        self.debug("SampRate = %f"%(SampRate))
        secperbin = 1./SampRate
        self.debug("secperbin = %f"%(secperbin))
        CutOffFreq = 500#FIXME: would be this variable?
        freq = self._rfFrequency
        time_win = int((1/freq)/secperbin)
        self.debug("time_win = %d"%(time_win))
        Tot_Bucket = int(448*2*10**(-9)/secperbin)
        self.debug("Tot_Bucket = %d"%(Tot_Bucket))
        #Starting point ~ 907 bin = 22.675 ns when 
        #    Timing = 146351002 ns,
        #    OffsetH = 200 ns,
        #    ScaleH = 100 ns
        start = self.getStartingPoint()
        #NOT WORKING IF THE BEAM IS UNSTABLE
        #if len(self._cyclicBuffer)==0: return
        self.debug("cyclic buffer size: %d"%(len(self._cyclicBuffer)))
        if len(self._cyclicBuffer) == 0:
            self.warn("empty buffer")
            return
        y = array(self._cyclicBuffer[0][0:Tot_Bucket+start+1])
        for i in range(1,len(self._cyclicBuffer)):
            y += array(self._cyclicBuffer[i][0:Tot_Bucket+start+1])
        y = y/(len(self._cyclicBuffer))
        x = range(len(y))
        #the calculation itself
        try:
#            self.debug("input to lowPassFilter = %s"%(y.tolist()))
            self._yFiltered = self.lowPassFilter(SampRate, time_win, start,
                                                      CutOffFreq, x, y, secperbin)
            self.debug("len(BunchIntensity) = %d"%(len(self._yFiltered)))
            p_to_p = self.peakToPeak(time_win, x)
            self._bunchIntensity = p_to_p/max(p_to_p)
            self._filledBunches = self.bunchCount(self._bunchIntensity)
            self.debug("FilledBunches = %d"%self._filledBunches)
            self._spuriousBunches = self.spuriousBunches(self._bunchIntensity)
            self.debug("SpuriousBunches = %d"%self._spuriousBunches)
            #emit output events
            eventList = []
            eventList.append(['BunchIntensity',self._bunchIntensity])
            eventList.append(['FilledBunches',self._filledBunches])
            eventList.append(['SpuriousBunches',self._spuriousBunches])
            #self._parent.fireEventsList(eventList)
            #time stamps when this finish to know: how long it has take,
            tf = time.time()
            self._t0.append(t0)
            self._tf.append(tf)
            self.debug("current calculation in %f"%(tf-t0))
            while len(self._tf) > self._nAcquisitions:
                self._t0.pop(0)
                self._tf.pop(0)
            #use the time to calculate the output frequency
            self.calculateResultingFrequency()
            eventList.append(['resultingFrequency',self._resultingFrequency])
            self._parent.fireEventsList(eventList)
        except Exception,e:
            self.error("Exception during calculation: %s"%(e))
            #FIXME: should be set the status to fault?
            
    def calculateResultingFrequency(self):
        samples = len(self._tf)
        lapses = []
        for i in range(samples-1):
            lapses.append(self._tf[i+1]-self._tf[i])
        self._resultingFrequency = 1/average(lapses)
    # done auxiliary methods to manage events
    ####

    ####
    # original methods of the bunch analysis
    def delay(self):
        '''TODO: document this method'''
        #backup pulse params
        if self._timingProxy == None:
            self.warn("BuncherAnalyzer.delay() not callable if Event Receiver property not configured")
            return self._delayTick #FIXME: return this is meaningless
        pulse_params = self._timingProxy.command_inout("GetPulseParams", self._timingoutput)
        pulse_params = [int(i) for i in pulse_params]
        if (pulse_params[1] != self._delayTick):
            pulse_params = self._timingProxy.command_inout("GetPulseParams", self._timingoutput)
            pulse_params = [int(i) for i in pulse_params] #command returns numpy array
            pulse_params[1] = self._delayTick
            pulse_params = [self._timingoutput] + pulse_params
            self._timingProxy.command_inout("SetPulseParams",pulse_params)
        return pulse_params[1]

    def lowPassFilter(self,Samp_Rate, Time_Windows,Start, Cut_Off_Freq, 
                             x_data, y_data, Secperbin):
        '''TODO: document this method'''
#        self.debug("SampleRate %6.3f"%(Samp_Rate))
#        self.debug("Time window %d"%(Time_Windows))
#        self.debug("Start %d"%(Start))
#        self.debug("Cut off frequency %6.3f"%(Cut_Off_Freq))
#        self.debug("x %s"%x_data)
#        self.debug("y %s"%y_data)
#        self.debug("Secperbin %6.3f"%(Secperbin))
        try:
            #FIXME: parameters would be in side the class?
            #cutoff frequency at 0.05 Hz normalized at the Niquist frequency (1/2 samp rate)
            CutOffFreqNq = Cut_Off_Freq*10**6/(Samp_Rate*0.5)
            LowFreq = 499*10**6/(Samp_Rate*0.5)
            HighFreq = 501*10**6/(Samp_Rate*0.5)
            filterorder = 3            # filter order = amount of additional attenuation for frequencies higher than the cutoff fr.
            b,a = signal.filter_design.butter(filterorder,[LowFreq,HighFreq])

            y_Fil = copy(y_data)#FIXME: why this assignment if it will be reassigned before use it.
            try:
                y_Fil = signal.lfilter(b,a,y_data)
            except Exception,e:
                if self._parent and self._parent.get_state() != PyTango.DevState.ALARM:
                    self._parent.change_state(PyTango.DevState.ALARM)
                self.error("Exception in signal filter: %s"%(e))
                self._parent.addStatusMsg("Cannot apply a low pass filter.")
                raise Exception(e)
            if Start > len(y_Fil):
                if self._parent and self._parent.get_state() != PyTango.DevState.ALARM:
                    self._parent.change_state(PyTango.DevState.ALARM)
                self._parent.addStatusMsg("Starting point farther than input signal length.")
                raise BufferError("Starting point farther than input signal length.")
            else:
                if self._parent and self._parent.get_state() == PyTango.DevState.ALARM:
                    if len(self._cyclicBuffer) < self._nAcquisitions:
                        self._parent.change_state(PyTango.DevState.STANDBY)
                    else:
                        self._parent.change_state(PyTango.DevState.ON)
            i = 0
            for i in range(0, Start):
                y_Fil[i] = sum(y_Fil)/len(y_Fil)#FIXME: is this using numpy?
            return y_Fil[Start:len(y_Fil)-1]
        except BufferError,e:
            raise BufferError(e)
        except Exception,e:
            self.error("BunchAnalyzer.lowPassFilter() Exception: %s"%(e))

    def peakToPeak(self,Time_Window, x_data, y_Fil=None):
        '''TODO: document this method'''
        #FIXME: parameters would be in side the class?
        if y_Fil == None:
            y_Fil = self._yFiltered
        p_to_p = [] 
        k = 0 
        Start = 0
        Av = sum(y_Fil)/len(y_Fil)
        #Analysis
        self.debug("Data analysis")
        while (Start < len(y_Fil)-1):
            k = 0
            time_win_ar = [] #Array that leasts the considered time window
            if (Start + Time_Window < len(y_Fil)-1):
                for k in range(0, Time_Window):
                    time_win_ar.append(y_Fil[Start+k])
                if (max(time_win_ar) > Av and min(time_win_ar) > Av):
                    p_to_p.append(0)
                else:
                    p_to_p.append(max(time_win_ar)-min(time_win_ar))
            Start = Start + Time_Window
        i = 0
        Max = max(p_to_p)
        #thr = input('Threshold (%): ')
        thr = self._threshold
        thr = thr*0.01
        for i in range (0, len(p_to_p)-1):
            if (p_to_p[i] < thr*Max): #Threshold set at 1% of the maximum peak to peak amplitude
                p_to_p[i] = 0
        if (len(p_to_p) == 0):
            print "No Beam!"#FIXME: would be this a raise exception?
        return p_to_p

    def bunchCount(self,vec_p_to_p):
        '''TODO: document this method'''
        #FIXME: parameters would be in side the class?
        count = 0
        bunch = 0
        #TODO: document the loop
        for count in range(0, len(vec_p_to_p)-1):
            if(vec_p_to_p[count] > 0):
                bunch = bunch + 1
        return bunch

    def spuriousBunches(self,vec_p_to_p):
        '''TODO: document this method'''
        #FIXME: parameters would be in side the class?
        i = 0
        j = 0
        sp_bun = 0
        #TODO: document
        if (vec_p_to_p [i] != 0 and vec_p_to_p[i+1] == 0):
            sp_bun = sp_bun + 1
        i = i + 1 
        #TODO: document the loop
        while (i < len(vec_p_to_p)-1):
            if (i < len(vec_p_to_p)-10 and vec_p_to_p[i-1] == 0 and vec_p_to_p[i] != 0 and vec_p_to_p[i+10] == 0):
                while (j < 10):
                    if (vec_p_to_p[i+j] != 0):
                        sp_bun = sp_bun +1
                    j = j + 1
            elif (i < len(vec_p_to_p)-9 and vec_p_to_p[i-1] == 0 and vec_p_to_p[i] != 0 and vec_p_to_p[i+9] == 0):
                while (j < 9):
                    if (vec_p_to_p[i+j] != 0):
                        sp_bun = sp_bun +1
                    j = j + 1
            elif (i < len(vec_p_to_p)-8 and vec_p_to_p[i-1] == 0 and vec_p_to_p[i] != 0 and vec_p_to_p[i+8] == 0):
                while (j < 8):
                    if (vec_p_to_p[i+j] != 0):
                        sp_bun = sp_bun +1
                    j = j + 1
            elif (i < len(vec_p_to_p)-7 and vec_p_to_p[i-1] == 0 and vec_p_to_p[i] != 0 and vec_p_to_p[i+7] == 0):
                while (j < 7):
                    if (vec_p_to_p[i+j] != 0):
                        sp_bun = sp_bun +1
                    j = j + 1
            elif (i < len(vec_p_to_p)-6 and vec_p_to_p[i-1] == 0 and vec_p_to_p[i] != 0 and vec_p_to_p[i+6] == 0):
                while (j < 6):
                    if (vec_p_to_p[i+j] != 0):
                        sp_bun = sp_bun +1
                    j = j + 1
            elif (i < len(vec_p_to_p)-5 and vec_p_to_p[i-1] == 0 and vec_p_to_p[i] != 0 and vec_p_to_p[i+5] == 0):
                while (j < 5):
                    if (vec_p_to_p[i+j] != 0):
                        sp_bun = sp_bun +1
                    j = j + 1
            elif (i < len(vec_p_to_p)-4 and vec_p_to_p[i-1] == 0 and vec_p_to_p[i] != 0 and vec_p_to_p[i+4] == 0):
                while (j < 4):
                    if (vec_p_to_p[i+j] != 0):
                        sp_bun = sp_bun +1
                    j = j + 1
            elif (i < len(vec_p_to_p)-3 and vec_p_to_p[i-1] == 0 and vec_p_to_p[i] != 0 and vec_p_to_p[i+3] == 0):
                while (j < 3):
                    if (vec_p_to_p[i+j] != 0):
                        sp_bun = sp_bun +1
                    j = j + 1
            elif (i < len(vec_p_to_p)-2 and vec_p_to_p[i-1] == 0 and vec_p_to_p[i] != 0 and vec_p_to_p[i+2] == 0):
                while (j < 2):
                    if (vec_p_to_p[i+j] != 0):
                        sp_bun = sp_bun +1
                    j = j + 1
            elif (i < len(vec_p_to_p)-1 and vec_p_to_p[i-1] == 0 and vec_p_to_p[i] != 0 and vec_p_to_p[i+1] == 0):
                sp_bun = sp_bun +1
                j = 1
            i = i + j + 1
            j = 0
        if (vec_p_to_p[len(vec_p_to_p)-1] != 0 and vec_p_to_p[len(vec_p_to_p)-2] == 0 ):
            sp_bun = sp_bun + 1
    
        return sp_bun
    # done original methods of the bunch analysis
    ####
# Done BunchAnalyser Class
####

#imports only used from the command line call
try:#The try is necessary by the Tango device
    from matplotlib.pyplot import figure, show
    from pylab import plt,savefig,xlabel,ylabel
except: pass

####
# plot methods used when this is called by command line

def plot1(x_data,y_data,y_Fil):
    #Plotting raw and filtered data
    f1 = figure()
    af1 = f1.add_subplot(111)
    #af1.plot(array(x_data)*2.5e-2,y_data)
    af1.plot(array(x_data),y_data)
    plt.title("Raw and Filtered Data")
    #af1.plot(array(x_data)*2.5e-2, y_Fil, 'r')
    af1.plot(array(x_data), y_Fil, 'r')
    savefig('scope_LowPassFil.png')
def plot2(x_data,y_Fil):
    f2 = figure()
    af2 = f2.add_subplot(111)
#    af2.plot(array(x_data)*2.5e-2, y_Fil, 'r')
    af2.plot(array(x_data), y_Fil, 'r')
    plt.title("Filtered Data")
    savefig('scope_FilSig.png')
def plot3(p_to_p):
    #Potting the peak to peak signal in function of the bunch number
    f3 = figure()
    af3 = f3.add_subplot(111)
    plt.bar(range(len(p_to_p)), p_to_p/max(p_to_p))
    xlabel('Bucket Number')
    ylabel('Normalized peak to peak amplitude')
    plt.title("Peak to Peak")
    savefig('scope_peakTOpeakTimeWin.png') 

# end plot methods
####

def main():
    bunchAnalyzer = BunchAnalyzer(timingDevName="SR02/TI/EVR-CDI0203-A",
                                  scopeDevName="SR02/DI/sco-01")

    # Setting Offset and scale
    PyTango.AttributeProxy('SR02/DI/sco-01/OffsetH').write(2e-07)
    PyTango.AttributeProxy('SR02/DI/sco-01/ScaleH').write(1e-07)
    TimeDel = bunchAnalyzer.delay()
    print "Offset: ", PyTango.AttributeProxy('SR02/DI/sco-01/OffsetH').read().value*1e9, " ns"
    print "Scale: ", PyTango.AttributeProxy('SR02/DI/sco-01/ScaleH').read().value*1e9, " ns"
    print "Time delay: ", TimeDel
    


    # Usefull variables
    
    SampRate = PyTango.AttributeProxy('SR02/DI/sco-01/CurrentSampleRate').read().value
    print("SampRate = %f"%(SampRate))
    secperbin = 1./SampRate
    print("secperbin = %f"%(secperbin))
    CutOffFreq = 500
    freq = PyTango.AttributeProxy('SR09/rf/sgn-01/Frequency').read().value
    time_win = int((1/freq)/secperbin)
    print("time_win = %d"%(time_win))
    Tot_Bucket = int(448*2*10**(-9)/secperbin)
    print("Tot_Bucket = %d"%(Tot_Bucket))
    start = 907 #Starting point ~ 907 bin = 22.675 ns when Timing = 146351002 ns, OffsetH = 200 ns, ScaleH = 100 ns NOT WORKING IF THE BEAM IS UNSTABLE 
    Ac_num = input('Number of acquisitions:  ')

    

    ################################################# Loading and averaging  data ########################################
    
    n = 0
    y = PyTango.AttributeProxy('sr02/di/sco-01/Channel1').read().value
    time1 = time.time()
    y = y[0:Tot_Bucket+start+1]
    print "Data Acquisition..."
    time.sleep(0.1)
    for n in range(1,Ac_num):
        y_temp = []
        y_temp =PyTango.AttributeProxy('sr02/di/sco-01/Channel1').read().value
        y_temp = y_temp[0:Tot_Bucket+start+1]
        y = y + y_temp
        time.sleep(0.1)
    
    y = y/(n+1)
    x = range(len(y))
    
    ################################################ Filtering Data #######################################################
        
    y_fil = bunchAnalyzer.lowPassFilter(SampRate, time_win, start, CutOffFreq, x, y, secperbin)
    plot1(x[:len(y_fil)],y[:len(y_fil)],y_fil)
    plot2(x[:len(y_fil)],y_fil)
    
    ################################################ Analysis ##############################################################
    
    bunchAnalyzer._threshold = input('Threshold (%): ')
    P_to_P = bunchAnalyzer.peakToPeak(time_win, x, y_fil)
    plot3(P_to_P/max(P_to_P))
    
    ################################################ Bunch Counting #########################################################
    
    Bunch = bunchAnalyzer.bunchCount(P_to_P)
    
    ################################################ Spurious Bunches #######################################################
    
    Sp_Bun = bunchAnalyzer.spuriousBunches(P_to_P)
    
    ################################################ Output #################################################################
    
 

    print "Total number of bucket: ", len(P_to_P)+1
    
    print "Number of filled bunches", Bunch
    
    print "Number of spurious bunches: ", Sp_Bun
    
    print "Max peak to peak amplitude: ", max(P_to_P)

    print "Average current: ", PyTango.AttributeProxy('SR/DI/DCCT/AverageCurrent').read().value, "mA"
    
    show()
    
if __name__ == "__main__":
    main()
