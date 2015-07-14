#!/usr/bin/env python
# -*- coding:utf-8 -*- 


##############################################################################
## license : GPLv3+
##============================================================================
##
## File :        MeasuredFillingPatternGui.py
## 
## Project :     Measure Filling Pattern Graphical interface based in Taurus
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

import sys
from taurus.core.util import argparse
from taurus.qt.qtgui.application import TaurusApplication
from taurus.qt.qtgui.taurusgui import TaurusGui
from widgets import *
from taurus.external.qt import Qt
import taurus

DEVICESERVERNAME = 'MeasuredFillingPattern'

DEVNAMEPROP = 'deviceNameProp'
ATTRNAMEPROP = 'attrNameProp'
InputSignals = {'MeasuredFillingPatternFCT': {DEVNAMEPROP: 'scoDev',
                                              ATTRNAMEPROP:'FCTAttribute'},
                'MeasuredFillingPatternPhCt':{DEVNAMEPROP: 'PhCtDev',
                                              ATTRNAMEPROP:'PhCtAttr'}}

class MainWindow(TaurusGui):
    def __init__(self, parent=None):
        TaurusGui.__init__(self)
        self.initComponents()
        self.splashScreen().finish(self)

    def initComponents(self):
        self._bunchIntensityComponent()
        self._inputSignalComponent()
        self._selectorComponent()

    def _bunchIntensityComponent(self):
        self._bunchIntensity = BunchIntensityPlot()
        self.createPanel(self._bunchIntensity,name="Bunch Intensity",
                         permanent=True)

    def _inputSignalComponent(self):
        self._inputSignal = InputSignalPlot()
        self.createPanel(self._inputSignal,name="Input signal",
                         permanent=True)

    def _selectorComponent(self):
        #create a TaurusDevCombo
        self._selector = TaurusDevCombo(self)
        #populate the combo
        self._selector.setModel(DEVICESERVERNAME)
        self._modelChange()
        #attach it to the toolbar
        self.selectorToolBar = self.addToolBar("Model:")
        self.selectorToolBar.setObjectName("selectorToolBar")
        self.viewToolBarsMenu.addAction(self.selectorToolBar.toggleViewAction())
        self.selectorToolBar.addWidget(self._selector)
        #subscribe model change
        self._selector.modelChosen.connect(self._modelChange)

    def _modelChange(self):
        newModel = self._selector.getSelectedDeviceName()
        if newModel != self.getModel():
            self.debug("Model has changed from %s to %s"
                       %(self.getModel(),newModel))
            self.setModel(newModel)
            self._bunchIntensitySetModel()
            self._inputSignalSetModel()

    def _bunchIntensitySetModel(self):
        self._bunchIntensity.setModel(self.getModel())

    def _inputSignalSetModel(self):
        inputSignalModel = self._getInputSignal()
        self.debug("input signal shall be %s"%(inputSignalModel))
        self._inputSignal.setModel(inputSignalModel)
        #TODO: tune the curve appearance properties
    
    def _getInputSignal(self):
        '''Given the device model, based on its device class, find the 
           properties that describes from where the signal is provided.
        '''
        modelClass = self._selector.getSelectedDeviceClass()
        modelHWObj = taurus.Device(self.getModel()).getHWObj()
        if not modelClass in InputSignals.keys():
            return ""#FIXME: uou this should never happen!
        propDev = InputSignals[modelClass][DEVNAMEPROP]
        iDevName = modelHWObj.get_property(propDev)[propDev][0]
        propAttr = InputSignals[modelClass][ATTRNAMEPROP]
        iAttrName = modelHWObj.get_property(propAttr)[propAttr][0]
        return iDevName+"/"+iAttrName

def main():
    parser = argparse.get_taurus_parser()
    parser.add_option("--model")
    app = TaurusApplication(sys.argv, cmd_line_parser=parser,
                      app_name='ctdimfp', app_version='0.1',
                      org_domain='ALBA', org_name='ALBA')
    options = app.get_command_line_options()
    ui = MainWindow()
    if options.model != None:
        ui.setModel(options.model)
    ui.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()