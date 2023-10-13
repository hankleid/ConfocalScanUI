import tkinter as tk
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import os

class PopoutPlot(tk.Toplevel):
    pixels = None # 2D numpy data.
    x_coords = [] # X coordinates of points to plot.
    y_coords = [] # Y coordinates of points to plot.
    scan_data = None # Z-data, list same length and dimension as x_coord and y_coords.
    scanwindow = None # ScanWindow object associated with the PopoutPlot.
    controlwindow = None # MainApp
    scan_num = 0 # Number of repetitions of the scan (for watching it over time).
    save_data = {} # Dictionary that records the scan. Appended to the controlwindow save_data.

    def __init__(self, controlmenu, scanwindow, x_coords, y_coords, *args, **kwargs):
        tk.Toplevel.__init__(self, *args, **kwargs)
        self.resizable(False, False)
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

    def takeScan(self):
        ##
        ## TAKES A SCAN.
        ##
        self.scan_num += 1
        self.scanwindow.disablePeakFindingWidgets()

        # Scan start.
        self.fig.clear()
        self.scan_data = np.zeros(len(self.x_coords))
        for i, x, y in zip(range(len(self.scan_data)), self.x_coords, self.y_coords):
            if str(self.controlmenu.widgets["interrupt_button"]["state"]) == "disabled":
                    # If 'Interrupt' button is pressed, stop scan.
                    break
            self.scanwindow.moveScanningMirror(x, y)
            self.scan_data[i] = self.scanwindow.measureCounts(x, y)
            self.fig.clear()
            ax = self.fig.add_subplot(111)
            ax.scatter(self.x_coords,
                       self.y_coords, 
                       s=100,
                       marker='H',
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

        self.scanwindow.enablePeakFindingWidgets()

    def saveScan(self):
        ##
        ## SAVES A SCAN. IF IT'S THE FIRST SCAN, MAKES A NEW FOLDER FOR IT.
        ## IF NOT THE FIRST SCAN, ADDS TO THE EXISTING FOLDER.
        ##
        s = self.scanwindow
        data_path = s.getPath()
        
        i = 1
        custom_slices_folder = s.getFolder() + "/" + s.getName() + "_custom_" + str(i)
        while os.path.exists(custom_slices_folder):
            i += 1
            custom_slices_folder = s.getFolder() + "/" + s.getName() + "_custom_" + str(i)
        if self.scan_num > 1: 
            # Place scan in the same folder as its bretheren.
            i -= 1
            custom_slices_folder = s.getFolder() + "/" + s.getName() + "_custom_" + str(max(1, i))
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
        ##
        ## [Event Handler] CLOSES THIS WINDOW AND ADJUSTS.
        ##
        s = self.scanwindow
        s.removeCrosshair()
        s.clearAnnotations()
        if s.crosshair:
            s.placeCrosshair(s.cursor_coordinates[0], s.cursor_coordinates[1])
        
        self.controlmenu.miniplot = None
        self.controlmenu.widgets["custom_loop_button"].config(state="normal")
        self.controlmenu.interruptScanEvent()

        self.destroy()
        self.update()