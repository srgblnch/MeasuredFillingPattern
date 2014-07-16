#! /usr/bin/env python

###########################################################################################################################################
#  /data/Diagnostics/Laura//PhotonCountingTopUp/phAnalyzer                                                                                #
# 									                                                                  #
#  This program analyses data coming from a Photon Counting device server                                                                 #
#  - Data are uploaded 								                                                          #
#  - Read the resolution                           				                                            		  #
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

#Functions definition

# Calculation of the filling status of the 448 buckets

def Fil_Pat_Calc(Time_Window, x_data, y_data, Secperbin):
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
	
	bucket = [] #generate the array with the bucket number

	for i in range (0, len(fil_pat)):
		bucket.append(i)
		if (fil_pat[i] < thr*Max): #Threshold set at 1% of the maximum peak to peak amplitude
			fil_pat[i] = 0
	
#To be tested whith real beam

#	fil_pat = fil_pat/sum(fil_pat)

#	cur = taurus.Attribute('sr/di/dcct/AverageCurrent').read().value
#	fil_pat = fil_pat/sum(fil_pat)*cur

	f1 = figure()
	af1 = f1.add_subplot(111)
	plot(bucket, fil_pat)
	xlabel('Bucket Number')
	ylabel('Current (mA)')
	plt.title("Filling Pattern")




	return fil_pat


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
	
	FP = Fil_Pat_Calc(time_win, x, y, secperbin) #Final output
	
	################################################ Output #################################################################
	

	
 	show()
	
if __name__ == "__main__":
	main()	
