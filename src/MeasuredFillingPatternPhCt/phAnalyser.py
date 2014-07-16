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

###########################################################################################################################################
#  /data/Diagnostics/Laura//PhotonCountingTopUp/phAnalyzer                                                                                #
#                                                                                                       #
#  This program analyses data coming from a Photon Counting device server                                                                 #
#  - Data are uploaded                                                                                           #
#  - Read the resolution                                                                                                 #
#  - Calculate the filling status of the different buckets                                                                                #
###########################################################################################################################################


from scipy import *
from numpy import *
from pylab import *
from matplotlib.pyplot import draw, figure, show
from copy import copy, copy
from scipy import signal
import time
import taurus

class PhCtAnalyzer:
    def __init__(self):
        pass
    
    ####
    # original methods of the ph analysis
    def Fil_Pat_Calc(self,Time_Window, x_data, y_data, Secperbin):
        '''Calculation of the filling status of the 448 buckets'''
        fil_pat = [] 
        k = 0 
        Start = 0
        i=0
        #Analysis
        print "Data analysis"
        while (Start < len(y_data)):
            k = 0
            time_win_ar = [] #Array representing the time of a bucket
            if (Start + Time_Window < len(y_data)):
                for k in range(0, Time_Window): 
                    time_win_ar.append(y_data[Start+k]) #create the bucket
                fil_pat.append(sum(time_win_ar)) #considering all the photons in the bucket
            Start = Start + Time_Window #switch to the following bucket
        #Impose a threshold (Not sure if needed)
        i = 0
        Max = max(fil_pat)
        thr = 1 #input('Threshold (%): ')
        thr = thr*0.01
        #generate the array with the bucket number
        bucket = []
        for i in range (0, len(fil_pat)):
            bucket.append(i)
            if (fil_pat[i] < thr*Max): #Threshold set at 1% of the maximum peak to peak amplitude
                fil_pat[i] = 0
        #To be tested whith real beam
        #    fil_pat = fil_pat/sum(fil_pat)
        #    cur = taurus.Attribute('sr/di/dcct/AverageCurrent').read().value
        #    fil_pat = fil_pat/sum(fil_pat)*cur
        return (bucket,fil_pat)
    # done original methods of the ph analysis
    ####
# Done PhCtBunchAnalyser Class
####

#Functions definition

# 




####
# plot methods used when this is called by command line

def plotPhCt(bucket,fil_pat):
    f1 = figure()
    af1 = f1.add_subplot(111)
    af1.plot(bucket, fil_pat)
    xlabel('Bucket Number')
    ylabel('Current (mA)')
    plt.title("Filling Pattern")

# end plot methods
####

def main():

    # Usefull variables
    
    secperbin = taurus.Attribute('bl34/di/phct-01/Resolution').read().value
    secperbin = secperbin*1e-12   #Convert the resolution (ps) in second
    BucketLength = 2*1e-9 # seconds
    time_win = int(BucketLength/secperbin)   
    Tot_Bucket = int(448*BucketLength/secperbin)

    ################################################# Loading and averaging  data ########################################
    
    y = taurus.Attribute('bl34/di/phct-01/Histogram').read().value
    y = y[0:Tot_Bucket+1]
    x = range(len(y))
    
    ################################################ Analysis ##############################################################
    FP = PhCtAnalyzer()
    bucket,fil_pat = FP.Fil_Pat_Calc(time_win, x, y, secperbin) #Final output
    plotPhCt(bucket,fil_pat)
    
    ################################################ Output #################################################################
    show()
    
if __name__ == "__main__":
    main()    
