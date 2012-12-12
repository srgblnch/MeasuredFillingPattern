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
    $Date: 2012-11-12 13:12:28 +0100 (Mon, 12 Nov 2012) $
    $Rev: 5766 $
    License: GPL3+
    Author: Laura Torino
""".encode('latin1')

from scipy import *
from numpy import *
from pylab import *
from matplotlib.pyplot import draw, figure, show
from copy import copy, copy
from scipy import signal
import time
import taurus
import PyTango
import datetime 
import os, getopt

class BunchAnalyzer:
    def __init__(self):
        self._timingProxy = PyTango.DeviceProxy("SR02/TI/EVR-CDI0203-A")
        self._timingoutput = 0
        self._delayTick = 18281216
        self._threshold = 1

    def delay(self):
        '''TODO: document this method'''
        #backup pulse params
        pulse_params = self._timingProxy.command_inout("GetPulseParams", self._timingoutput)
        pulse_params = [int(i) for i in pulse_params]
    
        if (pulse_params[1] != self._delayTick):
            pulse_params = self._timingProxy.command_inout("GetPulseParams", output)
            pulse_params = [int(i) for i in pulse_params] #command returns numpy array
            pulse_params[1] = self._delayTick
            pulse_params = [self._timingoutput] + pulse_params
            self._timingProxy.command_inout("SetPulseParams",pulse_params)
        return pulse_params[1]

    def lowPassFilter(self,Samp_Rate, Time_Windows,Start, Cut_Off_Freq, 
                             x_data, y_data, Secperbin):
        '''TODO: document this method'''
        #FIXME: parameters would be in side the class?
        #cutoff frequency at 0.05 Hz normalized at the Niquist frequency (1/2 samp rate)
        CutOffFreqNq = Cut_Off_Freq*10**6/(Samp_Rate*0.5)
        LowFreq = 499*10**6/(Samp_Rate*0.5)
        HighFreq = 501*10**6/(Samp_Rate*0.5)
        filterorder = 3            # filter order = amount of additional attenuation for frequencies higher than the cutoff fr.
        b,a = signal.filter_design.butter(filterorder,[LowFreq,HighFreq])

        y_Fil = copy(y_data)
        y_Fil = signal.lfilter(b,a,y_data)

        i = 0
        for i in range(0, Start):
            y_Fil[i] = sum(y_Fil)/len(y_Fil)#FIXME: this would be improved using numpy
        return y_Fil[Start:len(y_Fil)-1]

    def peakToPeak(self,Time_Window, x_data, y_Fil):
        '''TODO: document this method'''
        #FIXME: parameters would be in side the class?
        p_to_p = [] 
        k = 0 
        Start = 0
        Av = sum(y_Fil)/len(y_Fil)
        #Analysis
        print "Data analysis"
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

def main():
    bunchAnalyzer = BunchAnalyzer()

    # Setting Offset and scale
    taurus.Attribute('SR02/DI/sco-01/OffsetH').write(2e-07)
    taurus.Attribute('SR02/DI/sco-01/ScaleH').write(1e-07)
    TimeDel = bunchAnalyzer.delay()
    print "Offset: ", taurus.Attribute('SR02/DI/sco-01/OffsetH').read().value*1e9, " ns"
    print "Scale: ", taurus.Attribute('SR02/DI/sco-01/ScaleH').read().value*1e9, " ns"
    print "Time delay: ", TimeDel
    


    # Usefull variables
    
    SampRate = taurus.Attribute('SR02/DI/sco-01/CurrentSampleRate').read().value
    secperbin = 1./SampRate 
    CutOffFreq = 500
    freq = taurus.Attribute('SR09/rf/sgn-01/Frequency').read().value
    time_win = int((1/freq)/secperbin)   
    Tot_Bucket = int(448*2*10**(-9)/secperbin)
    start = 907 #Starting point ~ 907 bin = 22.675 ns when Timing = 146351002 ns, OffsetH = 200 ns, ScaleH = 100 ns NOT WORKING IF THE BEAM IS UNSTABLE 
    Ac_num = input('Number of acquisitions:  ')

    

    ################################################# Loading and averaging  data ########################################
    
    n = 0
    y = taurus.Attribute('sr02/di/sco-01/Channel1').read().value
    time1 = time.time()
    y = y[0:Tot_Bucket+start+1]
    print "Data Acquisition..."
    time.sleep(0.1)
    for n in range(1,Ac_num):
        y_temp = []
        y_temp =taurus.Attribute('sr02/di/sco-01/Channel1').read().value
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
    plot3(P_to_P)
    
    ################################################ Bunch Counting #########################################################
    
    Bunch = bunchAnalyzer.bunchCount(P_to_P)
    
    ################################################ Spurious Bunches #######################################################
    
    Sp_Bun = bunchAnalyzer.spuriousBunches(P_to_P)
    
    ################################################ Output #################################################################
    
 

    print "Total number of bucket: ", len(P_to_P)+1
    
    print "Number of filled bunches", Bunch
    
    print "Number of spurious bunches: ", Sp_Bun
    
    print "Max peak to peak amplitude: ", max(P_to_P)

    print "Average current: ", taurus.Attribute('SR/DI/DCCT/AverageCurrent').read().value, "mA"
    
    show()
    
if __name__ == "__main__":
    main()
