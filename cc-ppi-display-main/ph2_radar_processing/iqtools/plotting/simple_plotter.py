
from abc import abstractmethod
from pathlib import Path
from matplotlib import pyplot, figure, ticker, animation
# from plotly import express, graph_objects

import pandas as pd
import numpy as np

class PyPlotter():
    def __init__(self):
        pass

    @abstractmethod
    def simple_plot(self, title, x, y, x_axis, y_axis, file):
        pass

    @abstractmethod
    def intensity_plot(self):
        pass

    @abstractmethod
    def animation(self, title, data, x_axis, y_axis, file, pow_min, pow_max):
        pass

class MplPlotter(PyPlotter):
    def __init__(self):
        pass

    def simple_plot(self, title, x, y, x_axis, y_axis, file):
        pyplot.clf()
        for data in y:
            pyplot.plot(x, data)
        pyplot.ylabel(y_axis)
        pyplot.xlabel(x_axis)
        pyplot.title(title)
        pyplot.tight_layout()
        pyplot.savefig(file)

    def intensity_plot(self, title, data, x_axis, y_axis, z_axis, file, pow_min, pow_max):

        fig = figure.Figure(figsize=(10, 8), dpi=100)
        fig.suptitle(title)
        axes = fig.add_subplot(111)
        axes.set_xlabel(x_axis)
        axes.set_ylabel(y_axis)
        
        # Format ticks to SI units
        formatter = ticker.EngFormatter(places=1, sep="\N{THIN SPACE}")
        axes.yaxis.set_major_formatter(formatter)
        axes.xaxis.set_major_formatter(formatter)

        # Define the ylims (long-time/analysis duration axis)
        ylow = float(data.columns[0])
        yhigh = float(data.columns[-1])

        # Define the xlims (short-time/sweep window axis)
        xlow = float(data.index[0])
        xhigh = float(data.index[-1])

        osc_image = axes.imshow(
            np.array(data.transpose().values),
            interpolation="gaussian",
            cmap="plasma",
            origin="upper",
            extent=[xlow, xhigh, yhigh, ylow],
            aspect="auto",
            vmin = pow_min,
            vmax = pow_max
        )

        # Add a colorbar
        cb = fig.colorbar(
            osc_image,
            orientation="horizontal",
            use_gridspec=True,
            pad=0.15,
            label=z_axis
        )

        # Set autoscale parameters and the enable the grid
        axes.autoscale(False)
        axes.grid(True)

        fig.canvas.draw()
        fig.savefig(file)

    def animation(self, title, data, x_axis, y_axis, file, pow_min, pow_max):
        
        self.data = data
        fig =  pyplot.figure()
        fig.suptitle(title)

        # Define the xlims (short-time/sweep window axis)
        xlow = float(data.index[0])
        xhigh = float(data.index[-1])

        axes = pyplot.axes(xlim=(xlow, xhigh), ylim=(pow_min, pow_max))
        axes.set_xlabel(x_axis)
        axes.set_ylabel(y_axis)
        self.line, = axes.plot([], [], lw=3)

        frames_per_second = 30
        frame_interval = 1000 * 1 / frames_per_second
        time_anim_fig = animation.FuncAnimation(
            fig,
            self.animate,
            frames=len(data.columns),
            init_func = self.anim_init,
            interval=frame_interval,
        )
        file = str(file) + ".gif" 
        time_anim_fig.save(file)

    def anim_init(self):
        self.line.set_data([],[])
        return self.line,

    def animate(self, i):
        x = [float(i) for i in self.data.index.tolist()]
        y = self.data.iloc[:,[i]]
        self.line.set_data(x,y)
        return self.line,

class PlotlyPlotter(PyPlotter):
    def __init__(self):
        pass

    def simple_plot(self, title, x, y, x_axis, y_axis, file):
        '''
        data = pd.DataFrame()
        data[x_axis] = x
        data[y_axis] = y[0]
        figure = express.line(
            data,
            x = x_axis,
            y = y_axis,
            title = title
        )
        figure.write_html(Path(file).with_suffix(".html"))

    def intensity_plot(self, title, data, x_axis, y_axis, z_axis, file, pow_min, pow_max):
        # Setup layout and figure to house the plot
        layout = graph_objects.Layout(
            title=title,
            xaxis=dict(title=x_axis),
            yaxis=dict(title=y_axis)
        )

        # Flip columns and rows and transpose the dataframe to fit plotting structure
        data = data[data.columns[::-1]]
        data = data.transpose()
        
        # Define the hover text details
        hovertemplate =  ""
        hovertemplate += x_axis + ': %{x}<br>'
        hovertemplate += y_axis + ': %{y}<br>'
        hovertemplate += z_axis + ': %{z}<br>'

        # Create the plot heatmap
        heatmap = graph_objects.Heatmap(
                name = title,
                x = data.columns,
                y = data.index,
                z = data,
                zmin = pow_min,
                zmax = pow_max,
                colorbar = {"title": z_axis},
                colorscale = "magma",
                hovertemplate = hovertemplate
            )

        figure = graph_objects.Figure(layout=layout, data=heatmap)
        figure.update_layout(title_font_size = 24)
        figure.write_html(Path(file).with_suffix(".html"))
        '''

    def animation(self, title, data, x_axis, y_axis, file, pow_min, pow_max):
        '''
        print("Animations are not supported by the HTML plotter.")
        '''