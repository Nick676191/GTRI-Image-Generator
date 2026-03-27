# ORIGINAL SOURCE PULLED FROM NuGIT GUI PROJECT BY R. COHEN

import time
import threading
import logging
import datetime
import time
import threading
import logging
import datetime
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui
import numpy as np


class PyQtGraphWidget(pg.GraphicsWindow):
    pg.setConfigOption('background', '#323232')
    pg.setConfigOption('foreground', 'w')
    ptr1 = 0

    def __init__(self, parent=None, **kargs):
        pg.GraphicsWindow.__init__(self, **kargs)
        self.setParent(parent)
        self.setWindowTitle('NuGIT Data Capture')
        #self.freq = []
        self.plot_history_X = []
        self.plot_history_Y = []
        self.HorizontalCursor = None
        self.VerticalCursor = None
        self.QTPlot = self.addPlot(
            title="Uninitialized", symbolBrush=(0, 0, 255), symbolPen='w')

    def SetTitle(self, title):
        self.QTPlot.setTitle(title)

    def SetSymbolBrush(self, brush):
        self.Ploy.setSymbolBrush(brush)

    def SetSymbolPen(self, pen):
        self.QTPlot.setSymbolPen(pen)

    def SetLogMode(self, logX, logY):
        self.QTPlot.setLogMode(x=logX, y=logY)

    def SetAxisLabels(self, left, leftUnits, bottom, bottomUnits):
        self.QTPlot.setLabel('left', left, units=leftUnits)
        self.QTPlot.setLabel('bottom', bottom, units=bottomUnits)

    def SetAxisRanges(self, x_low, x_high, y_low, y_high):
        self.QTPlot.setXRange(x_low, x_high, padding=0)
        self.QTPlot.setYRange(y_low, y_high)

    def SetHorizontalCursor(self, YLocation):
        self.HorizontalCursor = YLocation

    def ScatterPlotFromDict(self, data, persist_historical=False):
        # Input data is list of dicts. Each dict specifies parameters for a single spot: {‘pos’: (x,y), ‘size’, ‘pen’, ‘brush’, ‘symbol’}.
        # This is just an alternate method of passing in data for the corresponding arguments.
        # penColor=(255, 255, 255), symbol='o', hoverable=False,
        if persist_historical == False:
            self.Clear()
        s1 = pg.ScatterPlotItem(hoverable=True, hoverSize=15)

        s1.addPoints(data)
        self.QTPlot.addItem(s1)

    def ScatterPlot(self, x, y, penColor=(255, 255, 255), symbol='o', persist_historical=False):
        if persist_historical == False:
            self.Clear()
        s1 = pg.ScatterPlotItem(size=10, pen=pg.mkPen(None), symbol='h',
                                brush=pg.mkBrush(255, 255, 255, 255))
        s1.addPoints(x)
        # self.QTPlot.plot(s1)

    def Plot(self, x, y, penColor=(255, 255, 255), penWidth=0.5, penStyle=QtCore.Qt.SolidLine,
             persist_historical=False, numtoplot=5, clear=False):
        if persist_historical:
            self.Clear()
            self.plot_history_X.append(x)
            self.plot_history_Y.append(y)
            while len(self.plot_history_X) > numtoplot:
                self.plot_history_X.pop(0)
                self.plot_history_Y.pop(0)
            if len(self.plot_history_X) == 1:
                self.QTPlot.plot(x, y, pen=pg.mkPen(
                    color=penColor, width=penWidth, style=penStyle))
            else:
                for i in range(len(self.plot_history_X), 1, -1):
                    color = i*255/numtoplot
                    width = i*0.5/numtoplot
                    if i == len(self.plot_history_X):
                        self.QTPlot.plot(self.plot_history_X[i-1], self.plot_history_Y[i-1], pen=pg.mkPen(
                            color=penColor, width=width, style=penStyle))
                    else:
                        self.QTPlot.plot(self.plot_history_X[i-1], self.plot_history_Y[i-1], pen=pg.mkPen(
                            color=penColor, width=width, style=QtCore.Qt.DotLine))

        else:
            if clear:
                self.Clear()
            self.QTPlot.plot(x, y, pen=pg.mkPen(
                color=penColor, width=penWidth, style=penStyle))

        if self.HorizontalCursor != None:
            HorizCursorX = x
            HorizCursorY = self.HorizontalCursor * np.ones(len(x))
            self.QTPlot.plot(HorizCursorX, HorizCursorY, pen=pg.mkPen(
                color=(255, 0, 0), width=2.0, style=QtCore.Qt.DotLine))

    def Clear(self):
        self.QTPlot.clear()


if __name__ == '__main__':
    w = PyQtGraphWidget()
    w.show()
    QtGui.QApplication.instance().exec_()
