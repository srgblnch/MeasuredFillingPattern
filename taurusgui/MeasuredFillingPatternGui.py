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
from taurus.qt.qtgui.container import TaurusMainWindow
from widgets import TaurusDevCombo,HistogramPlot
from taurus.external.qt import Qt

DEVICESERVERNAME = 'MeasuredFillingPattern'

class MainWindow(TaurusMainWindow):
    def __init__(self, parent=None):
        TaurusMainWindow.__init__(self)
        self.initComponents()
        self.splashScreen().finish(self)

    def initComponents(self):
        self._bunchIntensityComponent()
        self._selectorComponent()

    def _bunchIntensityComponent(self):
        self._histogramDW = Qt.QDockWidget("Histogram",self)
        self._histogram = HistogramPlot()
        self._histogramDW.setWidget(self._histogram)
        self.addDockWidget(Qt.Qt.BottomDockWidgetArea, self._histogramDW)

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
        self.debug("Model has changed from %s to %s"
                   %(self.getModel(),self._selector.givenSelectedDevice()))
        self.setModel(self._selector.givenSelectedDevice())
        self._histogram.setModel(self._selector.givenSelectedDevice())

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