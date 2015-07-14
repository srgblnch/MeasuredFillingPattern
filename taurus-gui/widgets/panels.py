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

from taurus.qt.qtgui.panel import TaurusForm

class AttributePanel(TaurusForm):
    def __init__(self, parent = None,
                 formWidget = None,
                 buttons = None,
                 withButtons = True, 
                 designMode = False):
        TaurusForm.__init__(self,parent,formWidget,buttons,
                            withButtons,designMode)
        self._devModel = ""
        
    def getModel(self):
        return self._devModel
    def setModel(self,model):
        attrList = ["%s/%s"%(model,attrName) for attrName in self._attributes]
        TaurusForm.setModel(attrList)
        self._devModel = model

#TODO: attribute panels

from taurus.qt.qtgui.plot import TaurusPlot

class StreamingPlot(TaurusPlot):
    def __init__(self, parent=None, designMode=False):
        TaurusPlot.__init__(self, parent, designMode)

    #TODO: overload the event management to avoid pile-up.

#    def replot(self):
#        self.debug("<<<Replot>>>")
#        TaurusPlot.replot()

class BunchIntensityPlot(StreamingPlot):
    def __init__(self, parent=None, designMode=False):
        StreamingPlot.__init__(self, parent, designMode)

    #TODO: events in streaming mode

    def getmodel(self):
        #TODO: robusteness
        superClassModel = TaurusPlot.getModel(self)
        if type(superClassModel) == list and len(superClassModel) == 1:
            attrName = superClassModel[0]
            devName = attrName.rsplit('/',1)[0]
            return devName
        return ""

    def setModel(self,model):
        self.debug("BunchIntensity model change")
        self._devModel = model
        TaurusPlot.setModel(self, model+"/bunchIntensity")

#TODO: plots of the FCT and the PhCt (with event streaming mode)

class InputSignalPlot(StreamingPlot):
    pass
