import tkinter as tk
from tkinter import ttk
from tkinter.filedialog import askdirectory
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from math import gcd
import os

class PopoutPlot(tk.Toplevel):
    pixels = None # 2D numpy data.
    x_coords = []
    y_coords = []
    scan_data = None # z-data, list same length and dimension as x_coord and y_coords.
    ID = ""
    scanwindow = None
    controlwindow = None
    scan_num = 0
    save_data = {}

    def __init__(self, controlmenu, scanwindow, x_coords, y_coords, *args, **kwargs):
        tk.Toplevel.__init__(self, *args, **kwargs)
        self.protocol("WM_DELETE_WINDOW", self.onClosing)
        self.controlmenu = controlmenu
        self.scanwindow = scanwindow
        self.x_coords = [round(x, 3) for x in x_coords]
        self.y_coords = [round(y, 3) for y in y_coords]
        self.save_data = {"x_coords":self.x_coords, "y_coords":self.y_coords}
        self.scan_data = np.zeros(len(x_coords))

        # Frame that holds the scan.
        frm_plot = tk.Frame(
            master=self,
            relief=tk.RAISED,
            borderwidth=1
        )
        frm_plot.pack()
        # Initialize matplotlib figure.
        aspectratio = (min(self.x_coords)-max(self.x_coords)) / (min(self.y_coords)-max(self.y_coords))
        dimx = 7
        dimy = 5.5
        if aspectratio >= 1: # Portrait.
            dimx /= aspectratio
        else: # Landscape.
            dimy *= aspectratio
        # self.fig = plt.figure(figsize = (max(4, dimx), max(2, dimy)))
        self.fig = plt.figure()
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
        # Scatter plot 3D, marker size function of minimum distance between points.
        self.scan_num += 1
        self.ID = self.scanwindow.ID + "_custom_" + str(self.scan_num)
        # Scan start.
        self.fig.clear()
        self.scan_data = np.zeros(len(self.x_coords))
        for i, x, y in zip(range(len(self.scan_data)), self.x_coords, self.y_coords):
            self.scan_data[i] = self.scanwindow.takeMeasurement(x, y)
            self.fig.clear()
            ax = self.fig.add_subplot(111)
            ax.scatter(self.x_coords,
                       self.y_coords, 
                       s=50,
                       marker='s',
                       linewidths=0,
                       c=self.scan_data,
                       cmap="inferno")
            # Set axis lims to preserve aspect ratio & make buffer room for the markers.
            ax.set_xlim((min(self.x_coords)-0.02,max(self.x_coords)+0.02))
            ax.set_ylim((min(self.y_coords)-0.02,max(self.y_coords)+0.02))
            ax.set_facecolor("black")
            self.canvas.draw()
            self.canvas.get_tk_widget().pack(expand=True)

            # Update the UI... tkinter made me do it :/
            self.update()
            self.update_idletasks()
        self.save_data[self.scan_num] = self.scan_data.tolist()
        self.scanwindow.save_data["custom_points"] = self.save_data

    def saveScan(self):
        s = self.scanwindow
        data_path = s.getPath()
        
        i = 1
        custom_slices_folder = s.getFolder() + "/custom_slices_" + str(i)
        while os.path.exists(custom_slices_folder):
            i += 1
            custom_slices_folder = s.getFolder() + "/custom_slices_" + str(i)
        if self.scan_num > 1: 
            # Place scan in the same folder as its bretheren.
            i -= 1
            custom_slices_folder = s.getFolder() + "/custom_slices_" + str(max(1, i))
        else:
             # Create a new folder only if this is the first scan (of any new coords),
             # since scan_num resets to 1 after uploading a new file.
             os.makedirs(custom_slices_folder)

        self.scanwindow.save_data["custom_points_"+str(i)] = self.scanwindow.save_data.pop("custom_points")
        plot_path = s.getPath(suffix="_custom_"+str(i))  

        s.saveJson(data_path) # Add data from custom points to the overall datafile.
        s.savePlot(plot_path, annotations=True) # Plot the main scan with the custom points mask on the plot.
        slices_path = custom_slices_folder + "/" + s.getName() + "_custom_" + str(i) + "_" + str(self.scan_num)
        self.fig.savefig(slices_path, dpi='figure') # Save the slice plot itself.
    
    def onClosing(self):
        s = self.scanwindow
        s.removeCrosshair()
        s.clearAnnotations()
        if s.crosshair:
            s.placeCrosshair(s.cursor_coordinates[0], s.cursor_coordinates[1])
        self.controlmenu.miniplot = None

        self.controlmenu.widgets["custom_loop_button"].config(state="normal")

        self.destroy()
        self.update()