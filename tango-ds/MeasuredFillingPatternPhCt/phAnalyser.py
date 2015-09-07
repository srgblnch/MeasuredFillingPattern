#! /usr/bin/env python
# -*- coding:utf-8 -*- 

##############################################################################
## license : GPLv3+
##============================================================================
##
## File :        phAnalyser.py
## 
## Project :     Filling Pattern from the Photon Counter
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
#  /data/Diagnostics/Laura/PhotonCountingTopUp/phAnalyzer                     #
#                                                                             #
#  This program analyses data coming from a Photon Counting device server     #
#  - Data are uploaded                                                        #
#  - Read the resolution                                                      #
#  - Calculate the filling status of the different buckets                    #
###############################################################################

from copy import copy, copy
from numpy import *
import PyTango
from scipy import *
#from scipy import signal
import taurus
import time
import traceback


#class Analyser:
#    def __init__(self,parent=None):
#        self._parent = parent
#
#    ######
#    #----# auxiliary methods for logging
#    def info(self,msg):
#        try:
#            if self._parent:
#                self._parent.info_stream(msg)
#            else:
#                print("info: %s"%(msg))
#        except: print("cannot print in info stream (%s)"%msg)
#    def debug(self,msg):
#        try:
#            if self._parent:
#                self._parent.debug_stream(msg)
#            else:
#                print("debug: %s"%(msg))
#        except: print("cannot print in debug stream (%s)"%msg)
#    def warn(self,msg):
#        try:
#            if self._parent:
#                self._parent.warn_stream(msg)
#            else:
#                print("warn:  %s"%(msg))
#        except: print("cannot print in warn stream (%s)"%msg)
#    def error(self,msg):
#        try:
#            if self._parent:
#                self._parent.error_stream(msg)
#            else:
#                print("error: %s"%(msg))
#        except: print("cannot print in error stream (%s)"%msg)
#    # done logging section
#    ######
#    



class PhCtAnalyzer:#(Analyser):
    def __init__(self,PhCtDevName,
                 histogramAttr="histogram",resolutionAttr="resolution",
                 dcctDev='SR/DI/DCCT',dcctAttr='AverageCurrent',
                 BucketLenght=2*1e-9,threshold=1,
                 parent=None):
        self._parent = parent#for the logging
        #Analyser.__init__(self, parent)
        #super(PhCtAnalyzer,self).__init__(parent)
        self._PhCtDevName = None
        self._PhCtDevProxy = None
        self._HistogramAttr = None
        self._Histogram = []
        self._resolutionAttr = None
        self._dcctDev = None
        self._dcctAttr = None
        self._BucketLength = None
        self._threshold = None
        
        self._Tot_Bucket = None
        
        self.info("contructor setter for PhCt device name")
        self._PhCtDevName = PhCtDevName
        self.info("contructor has set PhCt device name %s"%(self.PhCtDevName))
        self.HistogramAttr = histogramAttr
        self._resolutionAttr = resolutionAttr
        self._dcctDev = dcctDev
        self._dcctAttr = dcctAttr
        self.BucketLength = BucketLenght
        self.threshold = threshold
        
        self._t0 = []
        self._tf = []
        self._resultingFrequency = 0.0

    @property
    def PhCtDevName(self):
        return self._PhCtDevName

    @PhCtDevName.setter
    def PhCtDevName(self,value):
        try:
            print(".")
            self.info("New PhCt device name %s"%(value))
            try:
                print("..")
                self._PhCtDevName = value
                print("...")
                self._PhCtDevProxy = PyTango.DeviceProxy(self._PhCtDevName)
            except Exception,e:
                print("!")
                self.error("Error making PhCt device proxy: %s"%(e))
                raise e
            else:
                print("+")
                self.info("PhCt device proxy made")
        except Exception,e:
            print("?")
            self.error("Agh! %s"%(e))

    @property
    def PhCtDevProxy(self):
        self.info("PhCt device proxy requested")
        if self._PhCtDevProxy == None:
            if self._PhCtDevName == None:
                self.error("Unknown device name to build a proxy")
                return None
            self.warn("Building proxy on the fly for %s"%(self._PhCtDevName))
            self._PhCtDevProxy = PyTango.DeviceProxy(self._PhCtDevName)
        self.info("Returning PhCt proxy")
        return self._PhCtDevProxy

    @property
    def HistogramAttr(self):
        return self._HistogramAttr
    
    @HistogramAttr.setter
    def HistogramAttr(self,value):
        self._HistogramAttr = value

    @property
    def Histogram(self):
#        fullAttrName = self._PhCtDevName+'/'+self._HistogramAttr
#        return taurus.Attribute(fullAttrName).read().value
        return self._Histogram
    
    @Histogram.setter
    def Histogram(self,value):
        self._Histogram = value
        
    @property
    def InputSignal(self):
        return self._Histogram
    
    @property
    def resolutionAttr(self):
        return self._resolutionAttr
    
    @resolutionAttr.setter
    def resolutionAttr(self,value):
        self._resolutionAttr = value

    @property
    def Resolution(self):
        fullAttrName = "%s/%s"%(self._PhCtDevName,self._resolutionAttr)
        return taurus.Attribute(fullAttrName).read().value

    @property
    def dcctDev(self):
        return self._dcctDev
    
    @dcctDev.setter
    def dcctDev(self,value):
        self._dcctDev = value
    
    @property
    def dcctAttr(self):
        return self._dcctAttr
    
    @dcctAttr.setter
    def dcctAttr(self,value):
        self._dcctAttr = value

    @property
    def Current(self):
        fullAttrName = self._dcctDev+'/'+self._dcctAttr
        return taurus.Attribute(fullAttrName).read().value

    @property
    def BucketLenght(self):
        return self._BucketLenght
    
    @BucketLenght.setter
    def BucketLenght(self,value):
        self._BucketLenght = value

    @property
    def threshold(self):
        self.debug("Threshold = %d"%(self._threshold))
        return self._threshold
    
    @threshold.setter
    def threshold(self,value):
        self._threshold = value

    @property
    def ResultingFrequency(self):
        return self._resultingFrequency

    @property
    def TotBucket(self):
        return self._Tot_Bucket

    #a callback method for the scope channel attribute
    def push_event(self,event):
        try:
            if event != None:
                if event.device.dev_name() == self._PhCtDevName:
                    if event.attr_value != None and \
                       event.attr_value.value != None:
                        if event.attr_value.quality in \
                                [PyTango.AttrQuality.ATTR_VALID,
                                 PyTango.AttrQuality.ATTR_CHANGING]:
                            if self.isStandby():
                                return
                            if not self.isRunning():
                                self.setRunning()
                            self.debug("Received valid data! (%d,%s)"
                                       %(len(event.attr_value.value),
                                             event.attr_value.quality))
                            self.Histogram = event.attr_value.value
                            bucket,fil_pat = self.Fil_Pat_Calc(self.Histogram)
                            self.calculateResultingFrequency()
                            self.emit_results(fil_pat,event.attr_value.quality)
                        else:
                            self.debug("Data is %s"%(event.attr_value.quality))
                    else:
                        self.debug("PushEvent() %s: value has None type"
                                   %(event.attr_name))
                else:
                    self.warn("Received an unexpected event from %s"
                              %(event.device.dev_name()))
            else:
                self.warn("Received a null event")
        except Exception,e:
            msg = "cannot process event due to: %s"%e
            self.error(msg)
            self.setFault(msg)
            traceback.print_exc()

    def calculateResultingFrequency(self):
        samples = len(self._tf)
        lapses = []
        for i in range(samples-1):
            lapses.append(self._tf[i+1]-self._tf[i])
        self._resultingFrequency = 1/average(lapses)

    def emit_results(self,fillingPattern,quality=PyTango.AttrQuality.ATTR_VALID):
        if self._parent:
            self._parent.fireEventsList([['BunchIntensity',
                                          fillingPattern,quality],
                                         ['InputSignal',
                                          self.Histogram,quality],
                                         ['resultingFrequency',
                                          self._resultingFrequency]])
            self._parent.attr_BunchIntensity_read = fillingPattern

    ####
    # original methods of the ph analysis
    def mov_av(self,data):
        data_fil = []
        for i in range(len(data)-1):
            data_fil.append((data[i]+data[i+1])/2)
        data_fil.append(0)
        return array(data_fil)
    def Fil_Pat_Calc(self,y_data):
        '''Calculation of the filling status of the 448 buckets'''
        t0 = time.time()
        #self.debug("Fil_Pat_Calc()")
        # Usefull variables
        secperbin = self.Resolution*1e-12
        #Convert the resolution (ps) in second
        time_win = round(self.BucketLength/secperbin)
        self._Tot_Bucket = round(448*self.BucketLength/secperbin)
        #prepare arrays
        y_data = y_data[0:self._Tot_Bucket+1]
        x_data = range(len(y_data))
        fil_pat = [] 
        k = 0 
        Start = 0
        i=0
        #Analysis
        #self.debug("Data analysis")
        while (Start < len(y_data)):
            k = 0
            time_win_ar = [] #Array representing the time of a bucket
            if (Start + time_win < len(y_data)):
                for k in range(0, int(time_win)): 
                    time_win_ar.append(y_data[Start+k]) #create the bucket
                fil_pat.append(max(time_win_ar)) #considering all the photons 
                                                 #in the bucket
            Start = Start + time_win #switch to the following bucket
        #Impose a threshold (Not sure if needed)
        i = 0
        Max = max(fil_pat)
        #thr = 1 #input('Threshold (%): ')
        thr = self.threshold*0.01
        #generate the array with the bucket number
        bucket = []
        fil_pat_thr = array(fil_pat>Max*thr)
        fil_pat = fil_pat*fil_pat_thr.astype(int)
        #fil_pat = self.mov_av(fil_pat)
        cur = self.Current
        fil_pat = array(fil_pat)
        fil_pat.astype(float)
        fil_pat = fil_pat*cur/sum(fil_pat)
        tf = time.time()
        self._t0.append(t0)
        self._tf.append(tf)
        self.debug("current calculation in %f"%(tf-t0))
        while len(self._tf) > 10*3:#self.NAcquisitions:
            self._t0.pop(0)
            self._tf.pop(0)
        return (bucket,fil_pat)
    # done original methods of the ph analysis
    ####
    
    ######
    #----# auxiliary methods for logging
    def info(self,msg):
        try:
            if self._parent:
                self._parent.info_stream(msg)
            else:
                print("info: %s"%(msg))
        except: print("cannot print in info stream (%s)"%msg)
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
    # done logging section
    ######
    
    ######
    #----# auxiliary methods to manage events
    def subscribeHistogram(self):
        try:
            self._HistogramEvent = self.PhCtDevProxy.subscribe_event(\
                                    self.HistogramAttr,
                                    PyTango.EventType.CHANGE_EVENT,self)
        except Exception,e:
            self.error("Cannot subscribe to Histogram due to: %s"%(e))
            self.info("PhCt proxy type: %s"%(type(self.PhCtDevProxy)))
        
    def unsubscribeHistogram(self):
        self.PhCtDevProxy.unsubscribe_event(self._HistogramEvent)
        self._parent.change_state(PyTango.DevState.OFF)
    
#    def subscribe_event(self,attrName):
#        self._AttrEvent = self.PhCtDevProxy.subscribe_event(attrName,
#                                                PyTango.EventType.CHANGE_EVENT,
#                                                                          self)
#    def unsubscribe_event(self,devName):
#        self.PhCtDevProxy.unsubscribe_event(self._AttrEvent)
#        self._parent.change_state(PyTango.DevState.OFF)
    #---- auxiliary methods to manage events
    ######
    
    ######
    #----# auxiliary methods to manage states
    def isStandby(self):
        if self._parent:
            return self._parent.get_state() == PyTango.DevState.STANDBY
        return False
    
    def isRunning(self):
        if self._parent:
            return self._parent.get_state() == PyTango.DevState.RUNNING
        return False

    def setRunning(self):
        if self._parent:
            self._parent.change_state(PyTango.DevState.RUNNING)
            self._parent.addStatusMsg("Receiving events")

    def setFault(self,msg):
        if self._parent:
            self._parent.change_state(PyTango.DevState.FAULT)
            self._parent.addStatusMsg(msg)

    #---- auxiliary methods to manage states
    ######
    
# Done PhCtBunchAnalyser Class
####

####
# plot methods used when this is called by command line

def plotPhCt(bucket,fil_pat):
    from pylab import *
    from matplotlib.pyplot import draw, figure, show
    f1 = figure()
    af1 = f1.add_subplot(111)
    af1.plot(bucket, fil_pat)
    xlabel('Bucket Number')
    ylabel('Current (mA)')
    plt.title("Filling Pattern")

# end plot methods
####

def main():
    ################################# Analysis ################################
    FP = PhCtAnalyzer('bl34/di/phct-01')
    y = taurus.Attribute('bl34/di/phct-01/Histogram').read().value
    bucket,fil_pat = FP.Fil_Pat_Calc(y) #Final output
    plotPhCt(bucket,fil_pat)
    
    ################################# Output ##################################
    show()
    
if __name__ == "__main__":
    main()    
