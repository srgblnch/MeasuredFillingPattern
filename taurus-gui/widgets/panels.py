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

    #TODO: overload the event management to avoid pile-up. Streaming mode like

#    def replot(self):
#        self.debug("<<<Replot>>>")
#        TaurusPlot.replot()

class BunchIntensityPlot(StreamingPlot):
    def __init__(self, parent=None, designMode=False):
        StreamingPlot.__init__(self, parent, designMode)
        self.setObjectName("BunchIntensityPlot")

#    def getmodel(self):
#        #TODO: robusteness
#        superClassModel = TaurusPlot.getModel(self)
#        if type(superClassModel) == list and len(superClassModel) == 1:
#            attrName = superClassModel[0]
#            devName = attrName.rsplit('/',1)[0]
#            return devName
#        return ""
#
#    def setModel(self,model):
#        self.debug("BunchIntensity model change")
#        self._devModel = model
#        TaurusPlot.setModel(self, model+"/bunchIntensity")


class InputSignalPlot(StreamingPlot):
    def __init__(self, parent=None, designMode=False):
        StreamingPlot.__init__(self, parent, designMode)
        self.setObjectName("InputSignalPlot")
