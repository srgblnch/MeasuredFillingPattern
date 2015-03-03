#!/usr/bin/env python
# -*- coding:utf-8 -*- 

##############################################################################
## license : GPLv3+
##============================================================================
##
## File :        widgets/TaurusDevCombo.py
## 
## Project :     Widget to select one device from the given device server name
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

#?__docformat__ = 'restructuredtext'

import sys
from taurus.external.qt import Qt,QtCore
from taurus.qt.qtgui.util.ui import UILoadable
from taurus.qt.qtgui.panel import TaurusWidget
import taurus

@UILoadable(with_ui='_ui')
class TaurusDevCombo(TaurusWidget):
    modelChosen = QtCore.pyqtSignal()
    def __init__(self, parent=None, designMode=False):
        TaurusWidget.__init__(self, parent, designMode=designMode)
        self.loadUi()
        self._ui.selectorCombo.currentIndexChanged.connect(self.selection)

    @classmethod
    def getQtDesignerPluginInfo(cls):
        ret = TaurusWidget.getQtDesignerPluginInfo()
        ret['module'] = 'widgets.TaurusDevCombo'
        ret['group'] = 'Taurus Views'
        ret['container'] = ':/designer/frame.png'
        ret['container'] = False
        return ret

    def setModel(self,model):
        TaurusWidget.setModel(self, model)
        self.getDeviceListByDeviceServerName(model)
        self._ui.selectorCombo.addItems(self._deviceNames)

    def getDeviceListByDeviceServerName(self,deviceServerName):
        db = taurus.Database()
        instances = db.getServerNameInstances(deviceServerName)
        self.debug("by %s found %d instances: %s."
                   %(deviceServerName,len(instances),
                     ','.join("%s"%instance.name() for instance in instances)))
        self._deviceNames = []
        for instance in instances:
            for devName in instance.getDeviceNames():
                if not devName.startswith('dserver'):
                    self._deviceNames.append(devName)
        return self._deviceNames
    
    def selection(self,devName):
        if type(devName) == int:
            devName = self._ui.selectorCombo.currentText()
        self.debug("selected %s"%(devName))
        self._selectedDevice = devName
        self.modelChosen.emit()
    
    def givenSelectedDevice(self):
        #self.debug("Requested which device was selected")
        return self._selectedDevice

def main():
    app = Qt.QApplication(sys.argv)
    w = TaurusDevCombo()
    w.setModel("MeasuredFillingPattern")
    w.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
