# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 3
#  of the License, or (at your option) any later version.
#
#  Ths program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, see <http://www.gnu.org/licenses/>
#
# ##### END GPL LICENSE BLOCK #####


from Queue import LifoQueue
from taurus.qt.qtgui.base import TaurusBaseComponent
from taurus.qt.qtgui.panel import TaurusForm, TaurusCommandsForm
from taurus.qt.qtgui.plot import TaurusPlot, TaurusCurve
from threading import Thread, Event, RLock


__author__ = "Sergi Blanch-Torne"
__copyright__ = "Copyright 2014, CELLS / ALBA Synchrotron"
__license__ = "GPLv3+"


__all__ = ["AttributePanel", "CommandPannel", "StreamingPlot",
           "BunchIntensityPlot", "InputSignalPlot", "StreamingCurve"]


class AttributePanel(TaurusForm):
    def __init__(self, parent=None, formWidget=None, buttons=None,
                 withButtons=False, designMode=False):
        super(AttributePanel, self).__init__(parent, formWidget, buttons,
                                             withButtons, designMode)


class CommandPannel(TaurusCommandsForm):
    def __init__(self, parent=None, designMode=False):
        super(CommandPannel, self).__init__(parent, designMode)
        commandsFilterList = [lambda x: x.cmd_name in ['Init', 'Start',
                                                       'Stop']]
        self.setViewFilters(commandsFilterList)
        self._splitter.setSizes([1, 0])


class StreamingPlot(TaurusPlot):
    """
        This is an overtload of the TaurusPlot class to set up a filter
        to avoid pile up of events. To work like an streaming mode.

        When events are received, instead of follow the process to print it,
        it is pushed in a queue to free this thread to enqueue more and a
        second thread will continue with what the first was doing.

        This way the second thread have information about how the events are
        behaving, like the pile up situation and can take some measures.
    """
    def __init__(self, parent=None, designMode=False):
        super(StreamingPlot, self).__init__(parent, designMode)
        self.setObjectName("StreamingPlot")

    def setObjectName(self, name):
        if name is not None and isinstance(name, str):
            self.log_name = name
            self.log_full_name = self.log_name
            self.log_obj = self._getLogger(self.log_full_name)

    def updateCurves(self, names):
        '''
        The same than TaurusPlot method but changing a single line, where the
        curve object is created to, instead of a normal TaurusCurve, use a
        StreamCurve specialisation.

        Updates the TaurusCurves being plotted. It adds a new curve for each
        new curve model passed and removes curves if they are not in the names.

        :param names:   (sequence<str>) a sequence of curve models. One curve
                        will be created for each element of names.
                        Each  curve model can consist of a single attribute
                        name (which will be used for the Y values) or by two
                        attribute names separated by a '|' (in which case, the
                        left-hand attribute is used for the X values and the
                        right hand value for the Y values)
        '''
        self.curves_lock.acquire()
        try:
            xnames, ynames = [], []
            for name in names:
                name = name.lower()
                n = name.split("|")
                yname = n[-1]
                xname = None
                if len(n) > 1:
                    xname = n[0]
                xnames.append(xname)
                ynames.append(yname)

            del_curves = [name for name in self.curves.keys()
                          if name not in ynames]

            # if all curves were removed, reset the color palette
            if len(del_curves) == len(self.curves):
                self._curvePens.setCurrentIndex(0)

            for i, name in enumerate(ynames):
                xname = xnames[i]
                name = str(name)
                self.info('updating curve %s' % name)
                if name not in self.curves:
                    curve = \
                        StreamingCurve(name, xname, self,
                                       optimized=self.isOptimizationEnabled())
                    self.info("Build StreamingCurve for the model %s" % (name))
                    curve.attach(self)
                    self.curves[name] = curve
                    self.showCurve(curve, True)

                    if self._showMaxPeaks:
                        curve.attachMaxMarker(self)
                    if self._showMinPeaks:
                        curve.attachMinMarker(self)
                    curve.setPen(self._curvePens.next())
                    curve.setUseParentModel(self.getUseParentModel())
                    curve.setTitleText(self.getDefaultCurvesTitle())
                    curve.registerDataChanged(self, self.curveDataChanged)
                    self.curveDataChanged(name)

            # curves to be removed
            for name in del_curves:
                name = str(name)
                # curve = self.curves.pop(name)
                curve = self.curves.get(name)
                if not curve.isRawData:
                    # The rawdata curves should not be dettached by
                    # updateCurves. Call detachRawdata insted
                    curve.unregisterDataChanged(self, self.curveDataChanged)
                    curve.detach()
                    self.curves.pop(name)
            if del_curves:
                self.autoShowYAxes()

            # legend
            self.showLegend(len(self.curves) > 1, forever=False)
            self.replot()

        finally:
            self.curves_lock.release()


class BunchIntensityPlot(StreamingPlot):
    def __init__(self, parent=None, designMode=False):
        StreamingPlot.__init__(self, parent, designMode)
        self.setObjectName("BunchIntensityPlot")


class InputSignalPlot(StreamingPlot):
    def __init__(self, parent=None, designMode=False):
        StreamingPlot.__init__(self, parent, designMode)
        self.setObjectName("InputSignalPlot")


class StreamingCurve(TaurusCurve):
    def __init__(self, name, xname=None, parent=None, rawData=None,
                 optimized=False):
        super(StreamingCurve, self).__init__(name, xname, parent, rawData,
                                             optimized)
        self.setObjectName("StreamingCurve")
        self.buildStackThread()
        self.launchStackThread()

    def buildStackThread(self):
        '''
            For the streaming feature is needed to have a stack with the events
            received. Then newer events will be processed earlier (discarding
            older ones).

            For this task, apart of the stack itself, is needed a lock to
            deal with a critical section, together with a wait condition to
            notify new data stacked. Finally a threading Event is used to
            report the thread the join action.
        '''
        self._eventStack = LifoQueue()
        self._queueLock = RLock()
        self._queueManager = Thread(target=self.__streamingManager,
                                    name="StreamingManager")
        self._newDataAvailable = Event()
        self._endStreaming = Event()

    def launchStackThread(self):
        self._endStreaming.clear()
        self._newDataAvailable.clear()
        self._queueManager.start()

    def __del__(self):
        self._endStreaming.set()
        self._newDataAvailable.clear()

    def setObjectName(self, name):
        if name is not None and isinstance(name, str):
            self.log_name = name
            self.log_full_name = self.log_name
            self.log_obj = self._getLogger(self.log_full_name)

    def eventReceived(self, evt_src, evt_type, evt_value):
        '''
            Usually this call should need a short time to be finished before
            the next event is received. To ensure this is a short time consume,
            the event received is simply stored in a stack and a event
            processor awakened.

            When the processor is awakened or just finish the last processing,
            it proceeds with the latest arrived (discarting the others).

            It can be made without the stack, but we've set it to allow the
            widget to report, at least in the logs, when and how many events
            has been dropped.
        '''
        if hasattr(self, '_queueLock'):
            self.debug("%s receive an event" % (evt_src.name))
            with self._queueLock:
                self._eventStack.put([evt_src, evt_type, evt_value])
                self._newDataAvailable.set()
        else:
            self.warning("%s receive an event, but no locker, processing the "
                         "event without the streaming feature"
                         % (evt_src.name))
            TaurusCurve.eventReceived(self, evt_src, evt_type, evt_value)

    def __streamingManager(self):
        '''
            Main method of the background thread in charge of process stacked
            events and drop the ones that are too old in the stack.
        '''
        self.info("Streaming manager thread created")
        while not self._endStreaming.isSet():
            self.__processStreamingEvent()
            self.debug("Streaming manager %s go sleep!" % (self.modelName))
            self._newDataAvailable.wait()
            self.debug("Streaming manager %s wake up!" % (self.modelName))
        self.info("Queue process finish event...")

    def __processStreamingEvent(self):
        if not self._eventStack.empty():
            with self._queueLock:
                # as its a lifo queue, get returns the last received
                evt_src, evt_type, evt_value = self._eventStack.get()
                self.__cleanQueue()
            self._newDataAvailable.clear()
            TaurusCurve.eventReceived(self, evt_src, evt_type, evt_value)

    def __cleanQueue(self):
        if not self._eventStack.empty():
            self.warning("Dropping %d event(s) on the %s queue"
                         % (self._eventStack.qsize(), self.modelName))
            while not self._eventStack.empty():
                self._eventStack.get()
