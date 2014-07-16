#!/usr/bin/env python
# -*- coding:utf-8 -*- 


##############################################################################
## license :
##============================================================================
##
## File :        MeasuredFillingPatternPhCt.py
## 
## Project :     Measured Filling Pattern from a Photon Counter
##
## $Author :      sblanch$
##
## $Revision :    $
##
## $Date :        $
##
## $HeadUrl :     $
##============================================================================
##            This file is generated by POGO
##    (Program Obviously used to Generate tango Object)
##
##        (c) - Software Engineering Group - ESRF
##############################################################################

"""Device to ..."""

__all__ = ["MeasuredFillingPatternPhCt", "MeasuredFillingPatternPhCtClass", "main"]

__docformat__ = 'restructuredtext'

import PyTango
import sys
# Add additional import
#----- PROTECTED REGION ID(MeasuredFillingPatternPhCt.additionnal_import) ENABLED START -----#
import time
import threading
from phAnalyser import PhCtAnalyzer
import traceback

from types import StringType

META = u"""
    $URL: https://svn.code.sf.net/p/tango-ds/code/Servers/Calculation/MeasuredFillingPattern$
    $LastChangedBy: sergiblanch $
    License: GPL3+
    Author: Sergi Blanch
""".encode('latin1')


#----- PROTECTED REGION END -----#	//	MeasuredFillingPatternPhCt.additionnal_import

##############################################################################
## Device States Description
##
## ALARM : Check the status, something is not running as expected, but the calculations are still alive.
## OFF : The device is alive, but is not reading anything, neither doing any calculation
## ON : Device is doing the calculation normally
## STANDBY : The calculation have start, but not with the expected #samples in the cyclic buffer 
## FAULT : Something out of the specs, calculation stopped. Check the status.
## INIT : Just when the device is launched until its build procedure is done
##############################################################################

class MeasuredFillingPatternPhCt (PyTango.Device_4Impl):

#--------- Add you global variables here --------------------------
#----- PROTECTED REGION ID(MeasuredFillingPatternPhCt.global_variables) ENABLED START -----#
    def cleanAllImportantLogs(self):
        #@todo: clean the important logs when they loose importance.
        self.debug_stream("In %s::cleanAllImportantLogs()"%self.get_name())
        self._important_logs = []
        self.addStatusMsg("")

    def addStatusMsg(self,newMsg,isImportant=False):
        self.debug_stream("In %s::addStatusMsg('%s')"%(self.get_name(),newMsg))
        completeMsg = "The device is in %s state.\n"%(self.get_state())
        for ilog in self._important_logs:
            completeMsg = "%s%s\n"%(completeMsg,ilog)
        status = "%s%s\n"%(completeMsg,newMsg)
        self.set_status(status)
        self.push_change_event('Status',status)
        if isImportant and not newMsg in self._important_logs:
            self._important_logs.append(newMsg)

    def change_state(self,newstate):
        self.debug_stream("In %s::change_state(%s)"%(self.get_name(),str(newstate)))
        self.set_state(newstate)
        self.push_change_event('State',newstate)
        self.cleanAllImportantLogs()
        
    def createThread(self):
        self.debug_stream("In %s::createThread()"%self.get_name())
        #TODO: check if the thread can be created or if it is already created
        if not self.get_state() in [PyTango.DevState.OFF]:
            return False
        if hasattr(self,'_thread') and self._thread and self._thread.isAlive():
            self.debug_stream("In %s::createThread(): Trying to start threading when is already started."%self.get_name())
            self.change_state(PyTango.DevState.FAULT)
            self.addStatusMsg("Try to start the calculation thread when is already running.",isImportant=True)
            return False
        self.debug_stream("In %s::createThread(): Start calculation threading."%self.get_name())
        try:
            self._joinerEvent = threading.Event()#to communicate between threads
            self._joinerEvent.clear()
            self._startCmd = threading.Event()#Start command has been received
            self._startCmd.clear()
            if self.AutoStart:
                self._startCmd.set()
            self._stopCmd = threading.Event()#Stop command has been received
            self._stopCmd.clear()
            self._thread = threading.Thread(target=self.analyzerThread)
            self._thread.setDaemon(True)
            self._thread.start()
            self.debug_stream("In %s::createThread(): Thread created."%self.get_name())
        except Exception,e:
            self.warn_stream("In %s::createThread(): Exception creating thread: %s."%(self.get_name(),e))
            self.change_state(PyTango.DevState.FAULT)
            self.addStatusMsg("Exception creating calculation thread.",isImportant=True)
            return False
        return True
    def deleteThread(self):
        self.debug_stream("In %s::deleteThread(): Stoping acquisition threading."%self.get_name())
        if hasattr(self,'_joinerEvent'):
            self.debug_stream("In %s::deleteThread(): sending join event."%self.get_name())
            self._joinerEvent.set()
        if hasattr(self,'_thread'):
            self.debug_stream("In %s::deleteThread(): Thread joining."%self.get_name())
            self._thread.join(1)
            if self._thread.isAlive():
                self.debug_stream("In %s::deleteThread(): Thread joined."%self.get_name())
    
    def analyzerThread(self):
        self.debug_stream("In %s::analyzerThread(): Thread started."%self.get_name())
        if not hasattr(self,'_joinerEvent'):
            raise Exception("Not possible to start the loop because it have not end condition")
#        self.change_state(PyTango.DevState.STANDBY)#FIXME: change the state when it starts to work
#        self.cleanAllImportantLogs()
#        self.addStatusMsg("Starting buffer population")
        #Build the analyzer object
        try:
            time.sleep(1)
            self.debug_stream("Build PhCtAnalyzer instance")
            self._bunchAnalyzer = PhCtAnalyzer(self.PhCtDev,parent=self)
            self.debug_stream("Build PhCtAnalyzer made")
        except:
            self.change_state(PyTango.DevState.FAULT)
            self.addStatusMsg("Cannot build the analyzer",isImportant=True)
            return
        while not self._joinerEvent.isSet():
            #TODO: passive wait until no new data is available
            #FIXME: can this start with less samples in the buffer than the 
            #       number configured in the nAcquisitions attribute?
            #TODO: if a loop takes too long ALARM state and a message
            try:
                if self._startCmd.isSet():
                    self._startCmd.clear()
                    if not self.get_state() in [PyTango.DevState.STANDBY,
                                                PyTango.DevState.ON]:
                        try:
                            # Subscribe to events of the scope channel
                            #self._bunchAnalyzer.CyclicBuffer([])
                            self._bunchAnalyzer.subscribe_event("Histogram")
                        except Exception,e:
                            self.change_state(PyTango.DevState.FAULT)
                            self.addStatusMsg("Cannot subscribe to the PhCt",isImportant=True)
                            self.debug_stream("Cannot subscribe to the PhCt due to: %s"%(e))
                if self._stopCmd.isSet():
                    self._stopCmd.clear()
                    if not self.get_state() in [PyTango.DevState.OFF]:
                        try:
                            pass
                            self._bunchAnalyzer.unsubscribe_event()
                            eventList = []
                            #eventList.append(['nAcquisitions',0])#,PyTango.AttrQuality.ATTR_INVALID])
                            #eventList.append(['CyclicBuffer',[[0]]])#,PyTango.AttrQuality.ATTR_INVALID])
                            eventList.append(['BunchIntensity',[0]])#,PyTango.AttrQuality.ATTR_INVALID])
                            #eventList.append(['FilledBunches',0])#,PyTango.AttrQuality.ATTR_INVALID])
                            #eventList.append(['SpuriousBunches',0])#,PyTango.AttrQuality.ATTR_INVALID])
                            #eventList.append(['nBunches',0])#,PyTango.AttrQuality.ATTR_INVALID])
                            #eventList.append(['resultingFrequency',0])#,PyTango.AttrQuality.ATTR_INVALID])
                            self.fireEventsList(eventList)
                        except Exception,e:
                            self.change_state(PyTango.DevState.FAULT)
                            self.addStatusMsg("Cannot unsubscribe to the PhCt",isImportant=True)
                            self.debug_stream("Cannot unsubscribe to the PhCt due to: %s"%(e))
                time.sleep(1)
            except Exception,e:
                self.error_stream("In %s::analyzerThread(): Exception: %s"%(self.get_name(),e))
            
            
    def fireEventsList(self,eventsAttrList):
        #self.debug_stream("In %s::fireEventsList()"%self.get_name())
        #@todo: add the value on the push_event
        timestamp = time.time()
        for attrEvent in eventsAttrList:
            try:
                self.debug_stream("In %s::fireEventsList() attribute: %s"%(self.get_name(),attrEvent[0]))
                if attrEvent[0] in ['CyclicBuffer'] and not self.attr_emitCyclicBuffer_read:
                    self.debug_stream("In %s::fireEventsList() attribute: %s avoided to emit the event duo to flag."%(self.get_name(),attrEvent[0]))
                elif len(attrEvent) == 3:#specifies quality
                    self.push_change_event(attrEvent[0],attrEvent[1],timestamp,attrEvent[2])
                else:
                    self.push_change_event(attrEvent[0],attrEvent[1],timestamp,PyTango.AttrQuality.ATTR_VALID)
            except Exception,e:
                self.error_stream("In %s::fireEventsList() Exception with attribute %s"%(self.get_name(),attrEvent[0]))
                print e
#----- PROTECTED REGION END -----#	//	MeasuredFillingPatternPhCt.global_variables
#------------------------------------------------------------------
#    Device constructor
#------------------------------------------------------------------
    def __init__(self,cl, name):
        PyTango.Device_4Impl.__init__(self,cl,name)
        self.debug_stream("In " + self.get_name() + ".__init__()")
        MeasuredFillingPatternPhCt.init_device(self)

#------------------------------------------------------------------
#    Device destructor
#------------------------------------------------------------------
    def delete_device(self):
        self.debug_stream("In " + self.get_name() + ".delete_device()")
        #----- PROTECTED REGION ID(MeasuredFillingPatternPhCt.delete_device) ENABLED START -----#
        self.deleteThread()
        #----- PROTECTED REGION END -----#	//	MeasuredFillingPatternPhCt.delete_device

#------------------------------------------------------------------
#    Device initialization
#------------------------------------------------------------------
    def init_device(self):
        self.debug_stream("In " + self.get_name() + ".init_device()")
        self.get_device_properties(self.get_device_class())
        self.attr_BunchIntensity_read = [0.0]
        #----- PROTECTED REGION ID(MeasuredFillingPatternPhCt.init_device) ENABLED START -----#
        self._important_logs = []
        self._phCtAnalyzer = None
        #tools for the Exec() cmd
        DS_MODULE = __import__(self.__class__.__module__)
        kM = dir(DS_MODULE)
        vM = map(DS_MODULE.__getattribute__, kM)
        self.__globals = dict(zip(kM, vM))
        self.__globals['self'] = self
        self.__globals['module'] = DS_MODULE
        self.__locals = {}
        #prepare attributes that will have events
        self.set_change_event('State', True, False)
        self.set_change_event('Status', True, False)
        self.set_change_event('BunchIntensity', True, False)
        #prepare the analyzer thread
        self.change_state(PyTango.DevState.OFF)
        if self.createThread():
            self.addStatusMsg("Analyzer thread well created")
        else:
            self.change_state(PyTango.DevState.FAULT)
            self.cleanAllImportantLogs()
            self.addStatusMsg("Analyzer thread cannot be created")
        #----- PROTECTED REGION END -----#	//	MeasuredFillingPatternPhCt.init_device

#------------------------------------------------------------------
#    Always excuted hook method
#------------------------------------------------------------------
    def always_executed_hook(self):
        self.debug_stream("In " + self.get_name() + ".always_excuted_hook()")
        #----- PROTECTED REGION ID(MeasuredFillingPatternPhCt.always_executed_hook) ENABLED START -----#
        
        #----- PROTECTED REGION END -----#	//	MeasuredFillingPatternPhCt.always_executed_hook

#==================================================================
#
#    MeasuredFillingPatternPhCt read/write attribute methods
#
#==================================================================

#------------------------------------------------------------------
#    Read BunchIntensity attribute
#------------------------------------------------------------------
    def read_BunchIntensity(self, attr):
        self.debug_stream("In " + self.get_name() + ".read_BunchIntensity()")
        #----- PROTECTED REGION ID(MeasuredFillingPatternPhCt.BunchIntensity_read) ENABLED START -----#
        
        #----- PROTECTED REGION END -----#	//	MeasuredFillingPatternPhCt.BunchIntensity_read
        attr.set_value(self.attr_BunchIntensity_read)
        



#------------------------------------------------------------------
#    Read Attribute Hardware
#------------------------------------------------------------------
    def read_attr_hardware(self, data):
        self.debug_stream("In " + self.get_name() + ".read_attr_hardware()")
        #----- PROTECTED REGION ID(MeasuredFillingPatternPhCt.read_attr_hardware) ENABLED START -----#
        
        #----- PROTECTED REGION END -----#	//	MeasuredFillingPatternPhCt.read_attr_hardware


#==================================================================
#
#    MeasuredFillingPatternPhCt command methods
#
#==================================================================

#------------------------------------------------------------------
#    Start command:
#------------------------------------------------------------------
    def Start(self):
        """ 
        
        :param : 
        :type: PyTango.DevVoid
        :return: 
        :rtype: PyTango.DevVoid """
        self.debug_stream("In " + self.get_name() +  ".Start()")
        #----- PROTECTED REGION ID(MeasuredFillingPatternPhCt.Start) ENABLED START -----#
        self._startCmd.set()
        #----- PROTECTED REGION END -----#	//	MeasuredFillingPatternPhCt.Start
        
#------------------------------------------------------------------
#    Stop command:
#------------------------------------------------------------------
    def Stop(self):
        """ 
        
        :param : 
        :type: PyTango.DevVoid
        :return: 
        :rtype: PyTango.DevVoid """
        self.debug_stream("In " + self.get_name() +  ".Stop()")
        #----- PROTECTED REGION ID(MeasuredFillingPatternPhCt.Stop) ENABLED START -----#
        self._stopCmd.set()
        #----- PROTECTED REGION END -----#	//	MeasuredFillingPatternPhCt.Stop
        
#------------------------------------------------------------------
#    Exec command:
#------------------------------------------------------------------
    def Exec(self, argin):
        """ 
        
        :param argin: statement to executed
        :type: PyTango.DevString
        :return: result
        :rtype: PyTango.DevString """
        self.debug_stream("In " + self.get_name() +  ".Exec()")
        argout = ''
        #----- PROTECTED REGION ID(MeasuredFillingPatternPhCt.Exec) ENABLED START -----#
        try:
            try:
                # interpretation as expression
                argout = eval(argin,self.__globals,self.__locals)
            except SyntaxError:
                # interpretation as statement
                exec argin in self.__globals, self.__locals
                argout = self.__locals.get("y")

        except Exception, exc:
            # handles errors on both eval and exec level
            argout = traceback.format_exc()

        if type(argout)==StringType:
            return argout
        elif isinstance(argout, BaseException):
            return "%s!\n%s" % (argout.__class__.__name__, str(argout))
        else:
            try:
                return pprint.pformat(argout)
            except Exception:
                return str(argout)
        #----- PROTECTED REGION END -----#	//	MeasuredFillingPatternPhCt.Exec
        return argout
        

#==================================================================
#
#    MeasuredFillingPatternPhCtClass class definition
#
#==================================================================
class MeasuredFillingPatternPhCtClass(PyTango.DeviceClass):

    #    Class Properties
    class_property_list = {
        }


    #    Device Properties
    device_property_list = {
        'PhCtDev':
            [PyTango.DevString,
            "Photon Counter device name",
            [] ],
        'AutoStart':
            [PyTango.DevBoolean,
            "Configure if the device must start the calculation by default when it is launched",
            [True]],
        }


    #    Command definitions
    cmd_list = {
        'Start':
            [[PyTango.DevVoid, "none"],
            [PyTango.DevVoid, "none"]],
        'Stop':
            [[PyTango.DevVoid, "none"],
            [PyTango.DevVoid, "none"]],
        'Exec':
            [[PyTango.DevString, "statement to executed"],
            [PyTango.DevString, "result"],
            {
                'Display level': PyTango.DispLevel.EXPERT,
            } ],
        }


    #    Attribute definitions
    attr_list = {
        'BunchIntensity':
            [[PyTango.DevDouble,
            PyTango.SPECTRUM,
            PyTango.READ, 5000]],
        }


#------------------------------------------------------------------
#    MeasuredFillingPatternPhCtClass Constructor
#------------------------------------------------------------------
    def __init__(self, name):
        PyTango.DeviceClass.__init__(self, name)
        self.set_type(name);
        print "In MeasuredFillingPatternPhCt Class  constructor"

#==================================================================
#
#    MeasuredFillingPatternPhCt class main method
#
#==================================================================
def main():
    try:
        py = PyTango.Util(sys.argv)
        py.add_class(MeasuredFillingPatternPhCtClass,MeasuredFillingPatternPhCt,'MeasuredFillingPatternPhCt')

        U = PyTango.Util.instance()
        U.server_init()
        U.server_run()

    except PyTango.DevFailed,e:
        print '-------> Received a DevFailed exception:',e
    except Exception,e:
        print '-------> An unforeseen exception occured....',e

if __name__ == '__main__':
    main()
