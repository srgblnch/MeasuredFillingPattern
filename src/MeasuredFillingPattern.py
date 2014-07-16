#!/usr/bin/env python
# -*- coding:utf-8 -*- 


##############################################################################
## license : GPLv3+
##============================================================================
##
## File :        MeasuredFillingPattern.py
## 
## Project :     Measure Filling Pattern device server with two Tango classes.
##               One that gets the input from an scope (and other auxiliar
##               devices) and another from a Photon Counter.
##
## $Author :      sblanch$
##
## $Revision :    $
##
## $Date :        $
##
## $HeadUrl :     $
##============================================================================
##
##        (c) - Controls Software Section - Alba synchrotron (cells)
##############################################################################

import PyTango
import sys

from MeasuredFillingPatternFCT import MeasuredFillingPatternFCT,\
                                      MeasuredFillingPatternFCTClass
from MeasuredFillingPatternPhCt import MeasuredFillingPatternPhCt,\
                                       MeasuredFillingPatternPhCtClass

#==================================================================
#
#    MeasuredFillingPattern class main method
#
#==================================================================
def main():
    try:
        py = PyTango.Util(sys.argv)
        py.add_class(MeasuredFillingPatternFCTClass,
                     MeasuredFillingPatternFCT,
                     'MeasuredFillingPatternFCT')
        py.add_class(MeasuredFillingPatternPhCtClass,
                     MeasuredFillingPatternPhCt,
                     'MeasuredFillingPatternPhCt')

        U = PyTango.Util.instance()
        U.server_init()
        U.server_run()

    except PyTango.DevFailed,e:
        print '-------> Received a DevFailed exception:',e
    except Exception,e:
        print '-------> An unforeseen exception occurred....',e

if __name__ == '__main__':
    main()
