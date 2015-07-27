#!/usr/bin/env python
# -*- coding:utf-8 -*- 


##############################################################################
## license : GPLv3+
##============================================================================
##
## File :        widgets/panels.py
## 
## Project :     Measure Filling Pattern set of Taurus specialised panels
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


from taurus.external.qt import Qt
from taurus.qt.qtgui.panel import TaurusForm,TaurusCommandsForm
from taurus.qt.qtgui.plot import TaurusPlot,TaurusCurve


class AttributePanel(TaurusForm):
    def __init__(self, parent = None,
                 formWidget = None,
                 buttons = None,
                 withButtons = False, 
                 designMode = False):
        super(AttributePanel,self).__init__(parent,formWidget,buttons,
                                            withButtons,designMode)


class CommandPannel(TaurusCommandsForm):
    def __init__(self, parent = None, designMode = False):
        super(CommandPannel,self).__init__(parent, designMode)
        commandsFilterList = [lambda x: x.cmd_name in ['Init','Start','Stop']]
        self.setViewFilters(commandsFilterList)
        self._splitter.setSizes([1,0])


class StreamingPlot(TaurusPlot):
    def __init__(self, parent=None, designMode=False):
        TaurusPlot.__init__(self, parent, designMode)
        self.setObjectName("StreamingPlot")

    def setModel(self,modelNames):
        '''Each of the curves needs its own queue of events, the pile up 
        scenario may happen with one curve and not with another then one shall
        not affect the plotting of the other.
        '''
        TaurusPlot.setModel(self,modelNames)
        filters = [self.pileUpcheck]
        self.setEventFilters(filters,preqt=True)

    def setEventFilters(self, filters=None, preqt=False, curvenames=None):
        '''Combines the set event filters from the TaurusPlot superclass with 
        the TaurusBaseComponent preqt filter lost in the inheritance.
        '''
        if curvenames is None: curvenames=self.curves.keys()
        self.curves_lock.acquire()
        try:
            for name in curvenames: self.curves[name].\
            setEventFilters(filters,preqt)
        finally:
            self.curves_lock.release()

    def pileUpcheck(self,evt_src,evt_type,evt_value):
        self.info("Execution of pileUpCheck(%s)"%(evt_src.name))
        try:
            if evt_src.name in self.curves.keys() and \
            time.time() - evt_value.time > 1.0:
                self.info("Event for %s older than a seconds, dropping"
                          %(evt_src.name))
                return
        except Exception,e:
            self.error("evt_src exception: %s"%(e))
            return
        #return None stops the filterEvent execution and 
        #avoids the call to handleEvent
        return evt_src,evt_type,evt_value

class BunchIntensityPlot(StreamingPlot):
    def __init__(self, parent=None, designMode=False):
        StreamingPlot.__init__(self, parent, designMode)
        self.setObjectName("BunchIntensityPlot")


class InputSignalPlot(StreamingPlot):
    def __init__(self, parent=None, designMode=False):
        StreamingPlot.__init__(self, parent, designMode)
        self.setObjectName("InputSignalPlot")

