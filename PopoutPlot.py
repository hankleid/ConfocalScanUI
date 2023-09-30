import tkinter as tk
from tkinter import ttk
from tkinter.filedialog import askdirectory
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from math import gcd

class PopoutPlot(tk.Toplevel):
    pixels = None # 2D numpy data.
    x_axis = []
    y_axis = []
    x_coords = []
    y_coords = []
    ID = ""
    scanwindow = None
    loop_num = 0

    def __init__(self, scanwindow, x_coords, y_coords, *args, **kwargs):
        tk.Toplevel.__init__(self, *args, **kwargs)
        self.protocol("WM_DELETE_WINDOW", self.onClosing)
        self.scanwindow = scanwindow
        self.x_coords = [round(x, 3) for x in x_coords]
        self.y_coords = [round(y, 3) for y in y_coords]
        x_step = self.getPixelSize(self.x_coords)
        y_step = self.getPixelSize(self.y_coords)
        print(x_step, y_step)
        _x_axis = np.linspace(min(self.x_coords), max(self.x_coords), int((max(self.x_coords) - min(self.x_coords)) / x_step)+1).tolist()
        _y_axis = np.linspace(min(self.y_coords), max(self.y_coords), int((max(self.y_coords) - min(self.y_coords)) / y_step)+1).tolist()
        self.x_axis = [round(x, 3) for x in _x_axis]
        self.y_axis = [round(y, 3) for y in _y_axis]
        self.smoothList(self.x_axis, x_step)
        self.smoothList(self.y_axis, y_step)
        #print(self.y_axis)
        self.pixels = np.zeros((len(self.x_axis), len(self.y_axis)))

        # Frame that holds the scan.
        frm_plot = tk.Frame(
            master=self,
            relief=tk.RAISED,
            borderwidth=1
        )
        # Initialize matplotlib figure.
        aspectratio = (min(self.x_coords)-max(self.x_coords)) / (min(self.y_coords)-max(self.y_coords))
        dimx = 5
        dimy = 3.5
        if aspectratio >= 1: # Portrait.
            dimx /= aspectratio
        else: # Landscape.
            dimy *= aspectratio
        self.fig = plt.figure(figsize = (max(4, dimx), max(2, dimy)))
        self.canvas = FigureCanvasTkAgg(self.fig, master=frm_plot)
        # Put canvas on the GUI.
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def getPixelSize(self, arr):
        ##
        ## Returns greatest common denominator of all elements in the array.
        ##
        ints = [int(i*1e3) for i in arr]
        max_gcd = gcd(ints[1], ints[0])
        for i in range(2, len(ints)):
            max_gcd = gcd(max_gcd, ints[i])
        return abs(max_gcd/(1e3))
    
    def smoothList(self, arr, step):
        # make sure spacing is even between elements; if not, fill in the gaps.
        for i in range(1, len(arr)):
            if round(abs(arr[i]-arr[i-1]), 3) != step:
                newval = (arr[i]+arr[i-1])/2
                arr.insert(i, newval)

    def takeScan(self):
        self.loop_num += 1
        self.ID = self.scanwindow.ID + "_custom_"+str(self.loop_num)
        # Scan start.
        self.fig.clear()
        for x, y in zip(self.x_coords, self.y_coords):
            i, j = self.x_axis.index(x), self.y_axis.index(y)
            self.pixels[i][j] = self.scanwindow.takeMeasurement(x, y)

            self.fig.clear()
            ax = self.fig.add_subplot(111)
            plot = ax.imshow(self.pixels,
                                extent=[min(self.x_coords), max(self.x_coords), min(self.y_coords), max(self.y_coords)],
                                origin='lower',
                                cmap=self.scanwindow.widgets["colorbar_palette"].get())
            self.fig.colorbar(plot, ax=ax)
            self.canvas.draw()
            self.canvas.get_tk_widget().pack(expand=True)

            # Update the UI... tkinter made me do it :/
            self.update()
            self.update_idletasks()

        self.saveScan()

    def saveScan(self):
        return
    
    def onClosing(self):
        self.scanwindow.clearAnnotations()
        self.destroy()