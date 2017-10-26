# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 3
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, see <http://www.gnu.org/licenses/>
#
# ##### END GPL LICENSE BLOCK #####

from .MeasuredFillingPatternComponents import Component
import sys
from taurus.core.util import argparse
from taurus.external.qt import Qt, QtGui
from taurus import Logger
from taurus.qt.qtgui.application import TaurusApplication
from taurus.qt.qtgui.taurusgui import TaurusGui
from .widgets import *

__author__ = "Sergi Blanch-Torne"
__copyright__ = "Copyright 2014, CELLS / ALBA Synchrotron"
__license__ = "GPLv3+"

# The version is updated automatically with bumpversion
# Do not update manually
__version = '1.0.0'

BUNCHINTENSITY = 'BunchIntensity'
INPUTSIGNAL = 'InputSignal'
MEASURES = 'Measures'
CONFIGURATION = 'configuration'
EXPERT = 'expert'
COMMANDS = 'Commands'
STATE = 'State'

MODELS = 'models'
TYPE = 'type'

DEVICESERVERNAME = 'MeasuredFillingPattern'
CLASSFCT = 'MeasuredFillingPatternFCT'
CLASSPHCT = 'MeasuredFillingPatternPhCt'
DEVICECLASSES = [CLASSFCT, CLASSPHCT]

specificAttrs = {MEASURES: {CLASSFCT: ['FilledBunches',
                                       'SpuriousBunches',
                                       'nBunches',
                                       'resultingFrequency',
                                       'CurrentSampleRate'],
                            CLASSPHCT: ['FilledBunches',
                                        'SpuriousBunches',
                                        'nBunches',
                                        'resultingFrequency']},
                 CONFIGURATION: {CLASSFCT: ['nAcquisitions',
                                            'StartingPoint',
                                            'Threshold',
                                            'ScaleH',
                                            'OffsetH',
                                            'TimingTrigger'],
                                 CLASSPHCT: ['nAcquisitions', 'Threshold']},
                 EXPERT: {CLASSFCT: ['nAcquisitions',
                                     'StartingPoint_expert',
                                     'Threshold_expert',
                                     'ScaleH_expert',
                                     'OffsetH_expert',
                                     'TimingTrigger_expert'],
                          CLASSPHCT: ['nAcquisitions', 'Threshold_expert']},
                 STATE: {CLASSFCT: ['State', 'Status'],
                         CLASSPHCT: ['State', 'Status']}
                 }


class MainWindow(TaurusGui):
    def __init__(self, parent=None):
        TaurusGui.__init__(self)
        self._components = None
        self._lastPerspective = None
        self.initComponents()
        self.prepareJorgsBar()
        self.loadDeviceClassPerspective()
        self.splashScreen().finish(self)

    panels = {BUNCHINTENSITY: {MODELS: [BUNCHINTENSITY],
                               TYPE: BunchIntensityPlot},
              INPUTSIGNAL: {MODELS: [INPUTSIGNAL],
                            TYPE: InputSignalPlot},
              MEASURES: {MODELS: [],
                         TYPE: AttributePanel},
              CONFIGURATION: {MODELS: [],
                              TYPE: AttributePanel},
              EXPERT: {MODELS: [],
                       TYPE: AttributePanel},
              COMMANDS: {TYPE: CommandPannel},
              STATE: {MODELS: [],
                      TYPE: AttributePanel}}

    def initComponents(self):
        self._components = {}
        for panel in self.panels:
            self.splashScreen().showMessage("Building %s panel" % (panel))
            if MODELS in self.panels[panel]:
                attrNames = self.panels[panel][MODELS]
                haveCommands = False
            else:
                attrNames = None
                haveCommands = True
            if TYPE in self.panels[panel]:
                widget = self.panels[panel][TYPE]
            else:
                widget = None  # FIXME
            self._components[panel] = Component(self, name=panel,
                                                widget=widget,
                                                attrNames=attrNames,
                                                haveCommands=haveCommands)
        self._selectorComponent()

    def prepareJorgsBar(self):
        # Eliminate one of the two taurus icons
        self.jorgsBar.removeAction(self.jorgsBar.actions()[0])
        # hide also the console panel
        if 'Console' in self.getPanelNames():
            self.getPanel('Console').hide()

    def loadDefaultPerspective(self, popup=True):
        try:
            default = 'default'
            if default in self.getPerspectivesList():
                self.loadPerspective(name=default)
                self._lastPerspective = default
            raise Exception("no default")
        except:
            if popup:
                QtGui.QMessageBox.\
                    warning(self, "No default perspective",
                            "Please, save a perspective with the name "
                            "'default' to be used when launch")

    def loadDeviceClassPerspective(self):
        try:
            devClassName = self._selector.getSelectedDeviceClass()
            self.debug("Perspective to load '%s'" % (devClassName))
        except:
            QtGui.QMessageBox.\
                warning(self, "Unknown Device Class",
                        "The device class can not be known to load the"
                        "apropiate perspective.")
            self.loadDefaultPerspective(popup=False)
        else:
            try:
                if devClassName in self.getPerspectivesList():
                    if devClassName != self._lastPerspective:
                        self.loadPerspective(name=devClassName)
                        self._lastPerspective = devClassName
                else:
                    raise Exception("no class perspective")
            except:
                self.warning("There is no perspective for this specific "
                             "device class. Trying with the 'default'...")
                try:
                    self.loadDefaultPerspective(popup=False)
                except:
                    QtGui.QMessageBox.\
                        warning(self, "No class perspective",
                                "Please, save a perspective with the "
                                "name of the device class or 'default' "
                                "to be used when launch")
        self.debug("perspective loaded %s" % (self._lastPerspective))

    def _selectorComponent(self):
        self.splashScreen().showMessage("Building device selector")
        # create a TaurusDevCombo
        self._selector = TaurusDevCombo(self)
        # populate the combo
        self.splashScreen().showMessage("Searching for %s device servers"
                                        % (DEVICESERVERNAME))
        self._selector.setModel(DEVICESERVERNAME)
        self.splashScreen().\
            showMessage("Found %s device servers"
                        % (self._selector.getSelectedDeviceName()))
        # attach it to the toolbar
        self.selectorToolBar = self.addToolBar("Model:")
        self.selectorToolBar.setObjectName("selectorToolBar")
        self.viewToolBarsMenu.\
            addAction(self.selectorToolBar.toggleViewAction())
        self.selectorToolBar.addWidget(self._selector)
        # subscribe model change
        self._modelChange()
        self._selector.modelChosen.connect(self._modelChange)

    def _modelChange(self):
        newModel = self._selector.getSelectedDeviceName()
        if newModel != self.getModel():
            self.debug("Model has changed from %r to %r"
                       % (self.getModel(), newModel))
            self.setModel(newModel)
            for component in self._components.keys():
                if component in [MEASURES, CONFIGURATION, EXPERT, STATE]:
                    className = self._selector.getSelectedDeviceClass()
                    attrNames = specificAttrs[component][className]
                    self._components[component].attrNames = attrNames
                self._components[component].devName = newModel
            self.loadDeviceClassPerspective()
        else:
            self.debug("modelChange called but with the same value %r"
                       % (newModel))


def main():
    parser = argparse.get_taurus_parser()
    parser.add_option("--model")
    app = TaurusApplication(sys.argv, cmd_line_parser=parser,
                            app_name='ctdiMeasuredFillingPattern',
                            app_version=__version, org_domain='ALBA',
                            org_name='ALBA')
    options = app.get_command_line_options()
    ui = MainWindow()
    if options.model is not None:
        ui.setModel(options.model)
    ui.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
