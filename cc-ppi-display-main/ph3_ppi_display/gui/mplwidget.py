from PyQt5 import QtCore, QtGui, QtWidgets
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from data.ppi_data_manager import PPIData
from .blit_manager import BlitManager

import matplotlib as mpl
mpl.use('Qt5Agg')

import matplotlib.pyplot as plt
import numpy as np


class MplCanvas(FigureCanvasQTAgg):

    def __init__(self, parent=None):
        self.fig = plt.figure(facecolor="silver")
        self.ppi_data = None
        self.powers = None
        self.ranges = None
        self.azimuths = None
        self.ax = None
        self.scan_beam = None
        self.contour = None
        self.vmin = -100
        self.vmax = 0

        super(MplCanvas, self).__init__(self.fig)

    def draw_canvas(self, ppi_data=None):
        self._get_initial_data(ppi_data)
        self._setup_plot()

        self.fig.canvas.draw()

    def _get_initial_data(self, ppi_data):
        if ppi_data:
            self.ppi_data = ppi_data
        self.powers = self.ppi_data.generate_data(0, 1)
        self.ranges = self.ppi_data.range_array
        self.azimuths = self.ppi_data.azimuth_array

    def _setup_plot(self):
        self.ax = self.fig.add_subplot(111, polar=True)
        self.ax.set_theta_zero_location("N")
        self.ax.set_theta_direction(-1)
        self.ax.tick_params(axis="both")
        self.ax.set_ylim([0.0, self.ppi_data.max_range])
        self.ax.set_rticks(np.linspace(0.0, self.ppi_data.max_range, 11))
        self.ax.set_xlim([0.0, 2 * np.pi])
        self.ax.set_thetagrids(np.linspace(0.0, 315.0, 8))

        (self.scan_beam,) = self.ax.plot([], color="k", linewidth=4.0)  # sweeping arm plot
        self.axbackground = self.fig.canvas.copy_from_bbox(self.ax.bbox)

    def update_canvas(self, beam_data, powers):
        self.fig.canvas.restore_region(self.axbackground)
        self._draw_beam(beam_data)
        self._draw_range_data(powers)
        self.fig.canvas.flush_events()
        self.fig.canvas.draw()

    def _draw_beam(self, beam_data):
        self.scan_beam.set_data(beam_data)

    def _draw_range_data(self, powers):
        self.powers = powers
        self.clear_contour_cache()
        self.contour = self.ax.contourf(self.azimuths, self.ranges, self.powers, vmin=self.vmin, vmax=self.vmax, levels=np.linspace(self.vmin, self.vmax, 100), extend="both")

    def update_vlims(self, vmin, vmax):
        self.vmin = vmin
        self.vmax = vmax

    def update_max_range(self, max_range):
        self.ax.set_ylim([0.0, max_range])
        self.ax.set_rticks(np.linspace(0.0, max_range, 11))

    def clear_contour_cache(self):
        # Safely remove existing contour plot if present.
        if self.contour:
            # QuadContourSet provides a remove() method to clear all collections.
            try:
                self.contour.remove()
            except Exception:
                # Fallback: manually remove collections if remove() is unavailable.
                for tp in getattr(self.contour, "collections", []):
                    try:
                        tp.remove()
                    except Exception:
                        pass
            self.contour = None


class MplWidget(QtWidgets.QWidget):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.ppi_canvas = MplCanvas(self)

        # Create toolbar, passing canvas as first parameter, parent (self, the MainWindow) as second.
        toolbar = NavigationToolbar(self.ppi_canvas, self)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(toolbar)
        layout.addWidget(self.ppi_canvas)
        layout.setContentsMargins(0,0,0,0)

        # Create a placeholder widget to hold our toolbar and canvas.
        self.setLayout(layout)
