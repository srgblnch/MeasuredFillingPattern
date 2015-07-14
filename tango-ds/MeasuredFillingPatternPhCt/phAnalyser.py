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

from scipy import *
from numpy import *
from copy import copy, copy
from scipy import signal
import time
import taurus
import PyTango

class Analyser:
    def __init__(self,parent=None):
        self._parent = parent

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
    def subscribe_event(self,attrName):
        self._AttrEvent = self._PhCtDevProxy.subscribe_event(attrName,
                                                PyTango.EventType.CHANGE_EVENT,
                                                                          self)
    def unsubscribe_event(self,devName):
        self._PhCtDevProxy.unsubscribe_event(self._AttrEvent)
        self._parent.change_state(PyTango.DevState.OFF)
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


class PhCtAnalyzer(Analyser):
    def __init__(self,PhCtDevName,
                 histogram="histogram",resolution="resolution",
                 BucketLenght=2*1e-9,threshold=1,
                 parent=None):
        Analyser.__init__(self, parent)
        self._PhCtDevName = PhCtDevName
        self._PhCtDevProxy = PyTango.DeviceProxy(self._PhCtDevName)
        self._Histogram = PhCtDevName+"/"+histogram
        self._Resolution = PhCtDevName+"/"+resolution
        self._BucketLength = BucketLenght
        self._threshold = threshold
        #for the logging
        self._parent = parent
    
    @property
    def threshold(self):
        self.debug("Threshold = %d"%(self._threshold))
        return self._threshold
    
    @threshold.setter
    def threshold(self,value):
        self._threshold = value

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
                            bucket,fil_pat = self.Fil_Pat_Calc(\
                                                        event.attr_value.value)
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

    def emit_results(self,fillingPattern,quality=PyTango.AttrQuality.ATTR_VALID):
        if self._parent:
            self._parent.fireEventsList([['BunchIntensity',
                                          fillingPattern,quality]])
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
        #self.debug("Fil_Pat_Calc()")
        # Usefull variables
        self._secperbin = taurus.Attribute(self._Resolution).read().value*1e-12
        #Convert the resolution (ps) in second
        self._time_win = round(self._BucketLength/self._secperbin)
        self._Tot_Bucket = round(448*self._BucketLength/self._secperbin)
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
            if (Start + self._time_win < len(y_data)):
                for k in range(0, int(self._time_win)): 
                    time_win_ar.append(y_data[Start+k]) #create the bucket
                fil_pat.append(sum(time_win_ar)) #considering all the photons 
                                                 #in the bucket
            Start = Start + self._time_win #switch to the following bucket
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
        cur = taurus.Attribute('sr/di/dcct/AverageCurrent').read().value
        fil_pat = array(fil_pat)
        fil_pat.astype(float)
        fil_pat = fil_pat*cur/sum(fil_pat)
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
