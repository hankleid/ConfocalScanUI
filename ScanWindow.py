##############################################################
##############################################################
###                                                        ###
###                                                        ###
###   Author: Hannah Kleidermacher                         ###
###   To report bugs, questions, comments, please email:   ###
###   kleid@stanford.edu                                   ###
###                                                        ###
###                                                        ###
##############################################################
##############################################################


import os
import json
import tkinter as tk
from tkinter import ttk, StringVar
from tkinter.filedialog import askdirectory
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from datetime import datetime
from skimage.feature import peak_local_max

class ScanWindow(tk.Toplevel):
    controlmenu = None # Main App from which this object is instantiated.
    ID = "" # Unique ID for this scan.
    currently_scanning = False
    scan_data = None # 2D numpy data.
    datastream = [] # Contains all the data in a flattened list, appended as the scan progresses. For internal use, like min/max.
    xy_range = [0, 0, 0, 0] # x range, y range.
    x_axis = None # X axis array.
    y_axis = None # Y axis array.
    DAQ = None # DAQ dictionary that hosts the hardware.
    photon_counter = None # from the DAQ
    scanning_mirror = None # from the DAQ
    save_data = {} # Dictionary that records scan & other data.
    fig = None # Matplotlib figure for the scan.
    ax = None # The actual plot.
    widgets = {} # Buttons, labels, entries, etc. relevant to the window.
    cursor_coordinates = [0,0] # Coordinates for the current placement of the clicked cursor.
    colorbar_minmax = [0,0] # Min and max values for the plotting colorbar.
    autoscale = True # True if autoscale; False if user input. For colorbar.
    aspectratio = 1.0
    crosshair = False # True if there is supposed to be a crosshair (i.e. if a crosshair has ever been placed).

    def __init__(self, app, DAQ, x_screen, y_screen, *args, **kwargs):
        tk.Toplevel.__init__(self, *args, **kwargs)
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self.onClosing)
        self.ID = self.generateScanID() # Timestamp (not currently used)
        self.title("Scan "+self.ID)
        self.controlmenu = app # Access control menu through this App object.
        self.DAQ = DAQ # DAQ dictionary that hosts the hardware.DAQ dcitionary that hosts the hardware.DAQ dcitionary that hosts the hardware.
        self.photon_counter = self.DAQ["Photon Counter"]
        self.scanning_mirror = self.DAQ["Scanning Mirror"]

        self.columnconfigure([0, 1], minsize=200)
        self.rowconfigure(0, minsize=50)

        # Frame that holds the side info widgets.
        frm_side_info = tk.Frame(
            master=self,
            relief=tk.RAISED,
            borderwidth=0
        )
        # Frame that holds the scan.
        frm_scan = tk.Frame(
            master=self,
            relief=tk.RAISED,
            borderwidth=1,
        )

        # Grid to hold the scan frame and info frame.
        frm_side_info.grid(column=1, row=0)
        frm_scan.grid(column=0, row=0)
        self.widgets["scan_frame"] = frm_scan
        self.widgets["side_info_frame"] = frm_side_info

        # Init scan params.
        parent_widgets = self.controlmenu.widgets
        x_start = float(parent_widgets["x_start"].get())
        x_end = float(parent_widgets["x_end"].get())
        x_step = float(parent_widgets["x_step"].get())
        y_start = float(parent_widgets["y_start"].get())
        y_end = float(parent_widgets["y_end"].get())
        y_step = float(parent_widgets["y_step"].get())
        self.xy_range = [x_start, x_end, y_start, y_end]
        # Default cursor placement is in the center of the plot.
        self.cursor_coordinates = [(self.xy_range[1]+self.xy_range[0])/2, (self.xy_range[3]+self.xy_range[2])/2]

        # X and Y voltage axes.
        self.x_axis = np.linspace(x_start, x_end, int((x_end - x_start) / x_step)+1)
        self.y_axis = np.linspace(y_start, y_end, int((y_end - y_start) / y_step)+1)

        # Initialize data array.
        self.scan_data = np.zeros((len(self.x_axis), len(self.y_axis))) #  Data for plotting and saving.
        self.save_data = {
            "integration_time": float(self.controlmenu.widgets["int_time"].get()),
            "x_axis": self.x_axis.tolist(),
            "y_axis": self.y_axis.tolist(),
            "x_step": x_step,
            "y_step": y_step
        }

        self.geometry(f"+{x_screen}+{y_screen}") # Place the scanwindow at the specified coordinates on the screen.
        self.generateSideInfo()
        aspectratio = (self.xy_range[3]-self.xy_range[2]) / (self.xy_range[1]-self.xy_range[0])
        self.generatePlotHolder(aspectratio)

    def generateSideInfo(self):
        ##
        ## PLACES A GRID IN THE SIDE INFO FRAME; WIDGETS ORGANIZED INTO FRAMES THEN ADDED TO GRID.
        ##
        frm_side_info = self.widgets["side_info_frame"]
        sideinfo_frames = []
        
        # Plot settings frame.
        frm_plot_settings = tk.Frame(
            master=frm_side_info,
            relief=tk.RAISED,
            borderwidth=0
        )
        sideinfo_frames.append(frm_plot_settings)
        frm_minmax = tk.Frame(master=frm_plot_settings, relief=tk.RAISED, borderwidth=0)
        ent_min = tk.Entry(master=frm_minmax, width=8)
        ent_max = tk.Entry(master=frm_minmax, width=8)
        ent_min.insert(0, "0")
        ent_max.insert(0, "5000")
        ent_min.bind('<Return>', lambda e: self.changePlotSettings(autoscale=False))
        ent_max.bind('<Return>', lambda e: self.changePlotSettings(autoscale=False))
        self.widgets["user_min"] = ent_min
        self.widgets["user_max"] = ent_max
        ent_min.pack(padx=1, pady=1, side=tk.LEFT)
        ent_max.pack(padx=1, pady=1, side=tk.LEFT)
        lbl_colorbar_settings = tk.Label(master=frm_plot_settings, text="colorbar min/max:", padx=1, pady=1)
        btn_autoscale = tk.Button(master=frm_plot_settings, text="Autoscale", command=lambda: self.changePlotSettings(autoscale=True))
        self.widgets["colorbar_palette"] = StringVar()
        cbox_colors = ttk.Combobox(master=frm_plot_settings,
                                   textvariable=self.widgets["colorbar_palette"],
                                   values=["gray", "viridis", "plasma", "inferno", "magma", "cividis"],
                                   state="readonly",
                                   width=10)
        cbox_colors.current(4) # Set default dropdown value to the first value of ^ list.
        cbox_colors.bind("<<ComboboxSelected>>", lambda e: self.changePlotSettings())
        btn_replot = tk.Button(master=frm_plot_settings, text="Re-plot", command=self.onRePlot)
        frm_aspect = tk.Frame(master=frm_plot_settings, relief=tk.RAISED, borderwidth=0)
        lbl_aspect = tk.Label(master=frm_aspect, text="aspect ratio:", padx=1, pady=1)
        ent_aspect = tk.Entry(master=frm_aspect, width=8)
        ent_aspect.insert(0, "1.0") # Set to max X value; this means the ratio is default.
        ent_aspect.bind('<Return>', lambda e: self.changePlotSettings(aspectratio=float(ent_aspect.get())))
        self.widgets["aspectratio_entry"] = ent_aspect # Not currently used in the rest of the code, but storing just in case.
        btn_aspect = tk.Button(master=frm_aspect, text="Reset", command=lambda: self.changePlotSettings(aspectratio=1.0))
        self.widgets["aspectratio_button"] = btn_aspect # Not currently used in the rest of the code, but storing just in case.
        lbl_aspect.pack(padx=1, pady=1, side=tk.LEFT)
        ent_aspect.pack(padx=1, pady=1, side=tk.LEFT)
        btn_aspect.pack(padx=1, pady=1, side=tk.LEFT)

        lbl_colorbar_settings.pack(padx=1, pady=1)
        frm_minmax.pack(padx=1, pady=1)
        btn_autoscale.pack(padx=1, pady=1)
        cbox_colors.pack(padx=1, pady=1)
        btn_replot.pack(padx=1, pady=1)
        frm_aspect.pack(padx=1, pady=1, side=tk.BOTTOM)

        # Counts indicator frame.
        frm_counts = tk.Frame(
            master=frm_side_info,
            relief=tk.RAISED,
            borderwidth=0
        )
        sideinfo_frames.append(frm_counts)
        lbl_counts = tk.Label(master=frm_counts, text="counts/s:", padx=1, pady=1)
        lbl_counts_measure = tk.Label(
            master=frm_counts,
            text="0",
            fg="red",
            bg="white",
            font = ('TkDefaultFont', 20)
        )
        self.widgets["counts"] = lbl_counts_measure
        lbl_counts.pack(padx=1, pady=1)
        lbl_counts_measure.pack(padx=1, pady=1, side=tk.BOTTOM)

        # Cursor widgets frame.
        frm_cursor = tk.Frame(
            master=frm_side_info,
            relief=tk.RAISED,
            borderwidth=0
        )
        sideinfo_frames.append(frm_cursor)
        lbl_cursor_controls = tk.Label(master=frm_cursor, text="cursor controls:")
        frm_cursor_custom = tk.Frame(master=frm_cursor, relief=tk.RAISED, borderwidth=0)
        ent_cursor_x = tk.Entry(master=frm_cursor_custom, fg="blue", width=8)
        ent_cursor_x.insert(0, "0")
        ent_cursor_x.bind('<Return>', lambda e: self.onEnterCrosshairCoords())
        self.widgets["cursor_custom_x"] = ent_cursor_x
        ent_cursor_y = tk.Entry(master=frm_cursor_custom, fg="blue", width=8)
        ent_cursor_y.insert(0, "0")
        ent_cursor_y.bind('<Return>', lambda e: self.onEnterCrosshairCoords())
        self.widgets["cursor_custom_y"] = ent_cursor_y
        ent_cursor_x.pack(padx=1, pady=1, side=tk.LEFT)
        ent_cursor_y.pack(padx=1, pady=1, side=tk.LEFT)
        btn_cursor_move = tk.Button(master=frm_cursor, text="Move to Cursor", command=self.moveToCrosshair)
        btn_cursor_center = tk.Button(master=frm_cursor, text="Center", command=self.moveToCenter)
        self.widgets["cursor_move_button"] = btn_cursor_move
        self.widgets["cursor_center_button"] = btn_cursor_center
        lbl_cursor_controls.pack(padx=1, pady=1)
        frm_cursor_custom.pack(padx=1, pady=1)
        btn_cursor_move.pack(padx=1, pady=1)
        btn_cursor_center.pack(padx=1, pady=1, side=tk.BOTTOM)

        # Peak finding frame.
        frm_peakfind = tk.Frame(
            master=frm_side_info,
            relief=tk.RAISED,
            borderwidth=0
        )
        sideinfo_frames.append(frm_peakfind)
        lbl_peakfind = tk.Label(master=frm_peakfind, text="peak finding:", padx=1, pady=1)
        frm_peaksep = tk.Frame(master=frm_peakfind, relief=tk.RAISED, borderwidth=0)
        lbl_peaksep = tk.Label(master=frm_peaksep, text="min. separation:", padx=1, pady=1)
        ent_peaksep = tk.Entry(master=frm_peaksep, width=5)
        ent_peaksep.insert(0, "3")
        self.widgets["peak_min_sep"] = ent_peaksep
        lbl_peaksep.pack(padx=1, pady=1, side=tk.LEFT)
        ent_peaksep.pack(padx=1, pady=1, side=tk.LEFT)
        frm_thresh = tk.Frame(master=frm_peakfind, relief=tk.RAISED, borderwidth=0)
        lbl_thresh = tk.Label(master=frm_thresh, text="intensity threshold:", padx=1, pady=1)
        ent_thresh = tk.Entry(master=frm_thresh, width=7)
        ent_thresh.insert(0, "0.7")
        self.widgets["peak_threshold"] = ent_thresh
        lbl_thresh.pack(padx=1, pady=1, side=tk.LEFT)
        ent_thresh.pack(padx=1, pady=1, side=tk.LEFT)
        frm_peakbtns = tk.Frame(master=frm_peakfind, relief=tk.RAISED, borderwidth=0)
        btn_findpeaks = tk.Button(master=frm_peakbtns, text="Find Peaks", command=self.plotPeaks)
        btn_savepeaks = tk.Button(master=frm_peakbtns, text="Save Peaks", command=self.onSavePeaks)
        self.widgets["find_peaks"] = btn_findpeaks
        self.widgets["save_peaks"] = btn_savepeaks
        btn_findpeaks.pack(padx=1, pady=1, side=tk.LEFT)
        btn_savepeaks.pack(padx=1, pady=1, side=tk.LEFT)
        frm_gopeak = tk.Frame(master=frm_peakfind, relief=tk.RAISED, borderwidth=0)
        lbl_gopeak = tk.Label(master=frm_gopeak, text="go to peak #:", padx=1, pady=1)
        btn_backpeak = tk.Button(master=frm_gopeak, text="Back", command=lambda: self.goToNextPeak(-1))
        btn_gopeak = tk.Button(master=frm_gopeak, text="Next", command=lambda: self.goToNextPeak(1))
        self.widgets["next_peak"] = btn_gopeak
        ent_gopeak = tk.Entry(master=frm_gopeak, width=5)
        ent_gopeak.insert(0, "0")
        ent_gopeak.bind('<Return>', lambda e: self.goToIndexPeak(int(self.widgets["peak_index"].get())))
        self.widgets["peak_index"] = ent_gopeak
        lbl_gopeak.pack(padx=1, pady=1, side=tk.LEFT)
        btn_backpeak.pack(padx=1, pady=1, side=tk.LEFT)
        ent_gopeak.pack(padx=1, pady=1, side=tk.LEFT)
        btn_gopeak.pack(padx=1, pady=1, side=tk.LEFT)

        lbl_peakfind.pack(padx=1, pady=1)
        frm_peaksep.pack(padx=1, pady=1)
        frm_thresh.pack(padx=1, pady=1)
        frm_peakbtns.pack(padx=1, pady=1)
        frm_gopeak.pack(padx=1, pady=1, side=tk.BOTTOM)

        # Save settings frame.
        frm_all_save_info = tk.Frame(
            master=frm_side_info,
            relief=tk.RAISED,
            borderwidth=0
        )
        sideinfo_frames.append(frm_all_save_info)
        frm_savename = tk.Frame(master=frm_all_save_info, relief=tk.RAISED, borderwidth=0)
        lbl_savename = tk.Label(master=frm_savename, text="savename:", padx=1, pady=1)
        ent_savename = tk.Entry(master=frm_savename, fg="blue", width=30)
        ent_savename.insert(0, "untitled")
        self.widgets["savename"] = ent_savename
        lbl_savename.pack(padx=1, pady=1, side=tk.LEFT)
        ent_savename.pack(padx=1, pady=1, side=tk.LEFT)
        frm_savebuttons = tk.Frame(master=frm_all_save_info, relief=tk.RAISED, borderwidth=0)
        btn_save = tk.Button(master=frm_savebuttons, text="Save", command=self.onSaveScan)
        btn_save.pack(padx=1, pady=1, side=tk.LEFT)
        self.widgets["save_button"] = btn_save
        frm_savename.pack(padx=1, pady=1)
        frm_savebuttons.pack(padx=1, pady=1)

        # Add to local grid (show).
        frm_side_info.columnconfigure(0, minsize=250)
        frm_side_info.rowconfigure([i for i in range(len(sideinfo_frames))], minsize=120)
        for i in range(len(sideinfo_frames)):
            sideinfo_frames[i].grid(column=0, row=i)
    
    def generatePlotHolder(self, aspectratio):
        ##
        ## ADDS A CANVAS (FOR VISUALIZING DATA) TO A 1X1 GRID ON THE SCAN FRAME.
        ##
        frm_scan = self.widgets["scan_frame"]
        frm_scan.columnconfigure(0)
        frm_scan.rowconfigure(0)
        frm_plot = tk.Frame(
            master=frm_scan,
            width=50,
            height=50,
            relief=tk.RAISED,
            bg="white")
        frm_plot.grid(column=0, row=0)

        # Initialize matplotlib figure.
        dimx = 9
        dimy = 7.5

        if aspectratio >= 1: # Portrait.
            dimx /= aspectratio
        else: # Landscape.
            dimy *= aspectratio
        self.fig = plt.figure(figsize = (max(4, dimx), max(2, dimy)))
        canvas = FigureCanvasTkAgg(self.fig, master=frm_plot)
        self.ax = self.fig.add_subplot(111)
        self.canvas = canvas
        # Put canvas on the GUI.
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.widgets["plot_clicker"] = None # Callback ID for the mouse clicking matplotlib event.
        self.plotWithColorbar()

    def generateScanID(self):
        ##
        ## RETURNS A String IN THE FORM YYYY(M)M(D)D(H)H(M)M(S)S.
        ##
        now = datetime.now()
        return str(now.year)+str(now.month)+str(now.day)+str(now.hour)+str(now.minute)+str(now.second)

    def takeScan(self):
        ##
        ## TAKES A SCAN & VISUALIZES IT ON THE CANVAS.
        ##

        # Disable certain buttons while scan runs.
        self.widgets["cursor_move_button"].configure(state="disabled")
        self.widgets["cursor_center_button"].configure(state="disabled")
        self.widgets["cursor_custom_x"].configure(state="disabled")
        self.widgets["cursor_custom_y"].configure(state="disabled")
        self.widgets["save_button"].configure(state="disabled")
        self.disablePeakFindingWidgets()

        self.currently_scanning = True
        self.datastream = []
        fast_scan = self.controlmenu.widgets["fast_scan_int"].get() # 1 or 0

        # Scan start.
        for x_i in range(len(self.x_axis)):
            for i in range(len(self.y_axis)):
                if str(self.controlmenu.widgets["interrupt_button"]["state"]) == "disabled":
                    # If 'Interrupt' button is pressed, stop scan.
                    break
                y_i = 0
                # Change direction every column.
                if x_i % 2 == 0: # Even: scan in the forward direction.
                    y_i = i
                else: # Odd: scan in the backward direction.
                    y_i = -(i+1)

                # Coordinates.
                x = self.x_axis[x_i]
                y = self.y_axis[y_i]
                
                # Take measurement & record data.
                self.moveScanningMirror(x, y)
                measurement = self.takeMeasurement()

                self.scan_data[x_i][y_i] = measurement
                self.datastream.append(measurement)

                # Update UI (i.e. check for mouse activity) only every 3 pixels, to save computation.
                if y_i % 3 == 0:
                    if self.autoscale:
                        self.colorbar_minmax[0] = min(self.datastream)
                        self.colorbar_minmax[1] = max(self.datastream)

                    self.update()
                    self.update_idletasks()
            else:
                # The following block does not execute if the inner loop was broken with 'break'.
                if fast_scan == 0: # Not a fast scan. Plot after every column.
                    self.plotWithColorbar() 
                continue
            break
        
        # Scan end.
        if fast_scan == 1: # Fast scan. Only plot at the end.
            self.plotWithColorbar()
            
        print("Scan done.")
        self.moveScanningMirror(0, 0)
        if self.currently_scanning == True: # Scan has ended without pressing the interrupt button.
            self.controlmenu.interruptScanEvent()
            # Now self.currently_scanning is also False.
        self.save_data["scan_data"] = self.scan_data.tolist()
        # Enable buttons.
        self.widgets["cursor_center_button"].configure(state="normal")
        self.widgets["cursor_custom_x"].configure(state="normal")
        self.widgets["cursor_custom_y"].configure(state="normal")
        self.widgets["save_button"].configure(state="normal")
        self.enablePeakFindingWidgets()
        # Enable clicking the plot for placing cursor.
        self.connectPlotClicker()

    def plotWithColorbar(self):
        ## 
        ## REFRESH FIGURE BY CLEARING fig AND REMAKING ax. THEN PLOT.
        ## 
        self.fig.clear()
        self.ax = self.fig.add_subplot(111)
        plot = self.ax.imshow(self.scan_data.T,
                            extent=self.xy_range,
                            aspect=self.aspectratio,
                            origin='lower',
                            cmap=self.widgets["colorbar_palette"].get(),
                            vmin=self.colorbar_minmax[0],
                            vmax=self.colorbar_minmax[1])
        self.fig.colorbar(plot, ax=self.ax)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(expand=True)

        # Update the UI... tkinter made me do it :/
        self.update()
        self.update_idletasks()

    def onRePlot(self):
        ##
        ## [Event Handler] REMAKES THE PLOT, RESETTING ANNOTATIONS ETC. IF SCAN IS COMPLETE.
        ##
        self.plotWithColorbar()
        if not self.currently_scanning: # Scan is done; refresh annotations & relevant buttons.
            self.crosshair = False
            # Re-run peaks and re-upload custom coords to do anything with them on this fresh plot.
            self.widgets["save_peaks"].configure(state="disabled")
            self.controlmenu.widgets["custom_loop_button"].configure(state="disabled")
    
    def changePlotSettings(self, autoscale=None, aspectratio=None):
        ##
        ## [Event Handler] MAKES CHANGES TO COLORBAR SETTINGS (MIN/MAX) & REFRESHES PLOT IF NECESSARY.
        ##
        print(self.currently_scanning)
        if autoscale != None:
            self.autoscale = autoscale
        if aspectratio != None:
            self.aspectratio = aspectratio
            self.canvas.get_tk_widget().destroy()
            # self.canvas.get_tk_widget().delete("all")
            if self.currently_scanning:
                self.generatePlotHolder((self.xy_range[3]-self.xy_range[2]) / (self.xy_range[1]-self.xy_range[0]) * self.aspectratio)

        if self.autoscale:
            # Autoscale.
            self.colorbar_minmax[0] = min(self.datastream)
            self.colorbar_minmax[1] = max(self.datastream)
            print(f"Min/max counts: {self.colorbar_minmax[0]}, {self.colorbar_minmax[1]}")
        else:
            # User min/max.
            self.colorbar_minmax[0] = float(self.widgets["user_min"].get())
            self.colorbar_minmax[1] = float(self.widgets["user_max"].get())
            
        if not self.currently_scanning:
            # Only update plot if scan is done. While scan is currently running, the plot gets refreshed often enough.
            # Replot with new settings and replace crosshairs/annotations if they exist.
            if self.crosshair:
                self.removeCrosshair()
            lines = self.clearAnnotations()
            if aspectratio != None: # Need to remake figure if user has changed the aspect ratio.
                self.generatePlotHolder((self.xy_range[3]-self.xy_range[2]) / (self.xy_range[1]-self.xy_range[0]) * self.aspectratio)
                self.connectPlotClicker()
            self.plotWithColorbar()
            self.replotAnnotations(lines)
            if self.crosshair:
                self.placeCrosshair(self.cursor_coordinates[0], self.cursor_coordinates[1])

    def connectPlotClicker(self):
        ##
        ## CONNECTS THE MOUSE CLICK EVENT HANDLING CONNECTION TO THE MATPLOTLIB PLOT.
        ## CALLBACK ID (cid) STORED IN WIDGETS FOR KEEPING TRACK OF THE HANDLER.
        ##
        self.widgets["plot_clicker"] = self.canvas.mpl_connect('button_press_event', lambda e: self.onClickingPlot(e))

    def disconnectPlotClicker(self):
        ##
        ## DISCONNECTS THE MOUSE CLICK EVENT HANDLING CONNECTION TO THE MATPLOTLIB PLOT.
        ## CALLBACK ID (cid) STORED IN WIDGETS FOR KEEPING TRACK OF THE HANDLER.
        ##
        cid = self.widgets["plot_clicker"]
        self.canvas.mpl_disconnect(cid)
        
    def onClickingPlot(self, e):
        ##
        ## [Event Handler] Refreshes the crosshair placement at the location of the mouse click.
        ## Does nothing if the user clicks outside of the plot.
        ##
        xlim = self.ax.get_xlim()
        ylim = self.ax.get_ylim()
        outofbounds = False
        undefined = e.xdata is None or e.ydata is None
        if undefined is False:
            outofbounds = e.xdata < min(xlim) or e.xdata > max(xlim) or e.ydata < min(ylim) or e.ydata > max(ylim)
        if undefined or outofbounds:
            # Out of bounds.
            return
        else:
            self.removeCrosshair()
            # Remove previous crosshair (if exists) then place the crosshair at the mouse click location.
            self.placeCrosshair(e.xdata, e.ydata)
            if str(self.widgets["cursor_move_button"]["state"]) == "disabled":
                self.widgets["cursor_move_button"].configure(state="normal")

    def placeCrosshair(self, x_coord, y_coord):
        ##
        ## PLACES A CROSSHAIR (MARKER + PREPENDICULAR LINES) ON THE PLOT AT (x_coord, y_coord).
        ##
        x_coord = round(x_coord, 3)
        y_coord = round(y_coord, 3)
        self.ax.axhline(y = y_coord, color = 'r', linestyle = '-', linewidth=1)
        self.ax.axvline(x = x_coord, color = 'r', linestyle = '-', linewidth=1)
        self.ax.plot([x_coord], [y_coord], "s", markersize=5.5, markerfacecolor="None", markeredgewidth=1, markeredgecolor="cyan")
        self.canvas.draw()
        # Update cursor coordinates indicator on the UI.
        self.widgets["cursor_custom_x"].delete(0, tk.END)
        self.widgets["cursor_custom_y"].delete(0, tk.END)
        self.widgets["cursor_custom_x"].insert(0, str(x_coord))
        self.widgets["cursor_custom_y"].insert(0, str(y_coord))
        self.cursor_coordinates = [x_coord, y_coord]
        self.crosshair = True

    def onEnterCrosshairCoords(self):
        ##
        ## [Event Handler] PLACES THE CROSSHAIR AT THE x_coord, y_coord DEFINED IN THE UI FIELDS.
        ##
        print("entered custom cursor coords.")
        x_coord = float(self.widgets["cursor_custom_x"].get())
        y_coord = float(self.widgets["cursor_custom_y"].get())
        print(x_coord, y_coord)
        self.removeCrosshair()
        self.placeCrosshair(x_coord, y_coord)
        self.resetAxes() # Makes things neat again if user enters coordinate outside of data range.

    def takeMeasurement(self):
        ##
        ## TAKES A MEASUREMENT FROM THE PHOTON COUNTER THEN DISPLAYS THE COUNTS.
        ##
        int_time = float(self.controlmenu.widgets["int_time"].get()) / 1000
        measurement = self.photon_counter.readCounts(integration_time=int_time)
        self.widgets["counts"].config(text=str(measurement))
        return measurement
    
    def moveScanningMirror(self, x_coord, y_coord):
        self.scanning_mirror.moveTo(x_coord, y_coord)
    
    def moveToCrosshair(self):
        ##
        ## [Event Handler] MOVE THE SCANNING MIRROR TO WHERE THE CURSOR IS.
        ##
        x_coord = self.cursor_coordinates[0]
        y_coord = self.cursor_coordinates[1]
        self.moveScanningMirror(x_coord, y_coord)
        self.takeMeasurement()

    def moveToCenter(self):
        ##
        ## [Event Handler] MOVE THE SCANNING MIRROR TO (0, 0).
        ##
        self.widgets["cursor_custom_x"].delete(0, tk.END)
        self.widgets["cursor_custom_y"].delete(0, tk.END)
        self.widgets["cursor_custom_x"].insert(0, "0")
        self.widgets["cursor_custom_y"].insert(0, "0")
        self.moveScanningMirror(0, 0)
        self.takeMeasurement()

    def removeCrosshair(self):
        ##
        ## REMOVES THE CROSSHAIR FROM THE PLOT. IF NO CROSSHAIR, DOES NOTHING.
        ##
        if self.crosshair:
            self.ax.lines[-1].remove()
            self.ax.lines[-1].remove()
            self.ax.lines[-1].remove()

    def clearAnnotations(self):
        ##
        ## REMOVES PLOTTED LINES (BELOW CURSOR) AND RETURNS THEM IN A LIST.
        ##
        lines = []
        for line in self.ax.lines:
            lines.append(line)
        # Remove lines AFTER saving them all in 'lines' to avoid List displacement.
        for i in range(len(self.ax.lines)):
            self.ax.lines[-i].remove()
        self.canvas.draw()
        return list(reversed(lines))

    def replotAnnotations(self, lines):
        ##
        ## PLOTS ALL THE LINES IN lines. 
        ## lines IS A 1D ARRAY OF matplotlib 2DLine objects.
        ##
        if lines != None:
            for l in lines:
                self.ax.plot(l.get_xdata(),
                                l.get_ydata(),
                                color=l.get_color(),
                                marker=l.get_marker(),
                                markersize=l.get_markersize(),
                                markerfacecolor=l.get_markerfacecolor(),
                                markeredgewidth=l.get_markeredgewidth(),
                                markeredgecolor=l.get_markeredgecolor(),
                                linestyle=l.get_linestyle())
            self.canvas.draw()

    def plotCustomCoords(self, x_coords, y_coords):
        ##
        ## OVERLAYS x_coords AND y_coords ONTO THE SCAN.
        ##
        self.ax.plot(x_coords, y_coords, "o", markersize=3, markerfacecolor="None", markeredgewidth=1, markeredgecolor='cyan', linestyle = 'None')
        # Refresh the axes so that the plot doesn't stretch to accommodate the new line.
        self.resetAxes()
        self.canvas.draw()
        # Update the UI... tkinter made me do it :/
        self.update()
        self.update_idletasks()

    def plotPeaks(self):
        ##
        ## [Event Handler] FINDS PEAKS IN THE DATA AND PLOTS THEM. Code adapted from Hope Lee.
        ##
        self.removeCrosshair()
        self.clearAnnotations()
        detected_peaks = peak_local_max(self.scan_data,
                                        min_distance=int(self.widgets["peak_min_sep"].get()),
                                        threshold_abs=float(self.widgets["peak_threshold"].get())*np.mean(self.scan_data))
        peak_x, peak_y = detected_peaks.T # Indices.
        x_coords = [self.x_axis[i] for i in peak_x]
        y_coords = [self.y_axis[i] for i in peak_y]
        # Swap x and y (since imshow plot is transposed).
        self.ax.plot(x_coords, y_coords, "*", markersize=5.5, markerfacecolor="None", markeredgewidth=1, markeredgecolor="cyan")
        if self.crosshair:
            self.placeCrosshair(self.cursor_coordinates[0], self.cursor_coordinates[1])
        self.canvas.draw()

        peak_data = {'peaks_x_coords': x_coords, 'peaks_y_coords': y_coords}
        self.save_data["peak_finding"] = peak_data
        self.widgets["peak_index"].configure(state="normal")
        self.widgets["next_peak"].configure(state="normal")
        self.widgets["save_peaks"].configure(state="normal")
    
    def resetAxes(self):
        ##
        ## SETS THE PLOT AXES TO THE MIN AND MAX OF THE DATA RANGE
        ## TO PREVENT CUSTOM POINTS PLOTTING FROM STRETCHING THE AXES.
        ##
        self.ax.set_xlim((self.xy_range[0], self.xy_range[1]))
        self.ax.set_ylim((self.xy_range[2], self.xy_range[3]))
        self.canvas.draw()
        # Update the UI... tkinter made me do it :/
        self.update()
        self.update_idletasks()

    def disablePeakFindingWidgets(self):
        ##
        ## DISABLES ALL PEAK FINDING UI ELEMENTS.
        ##
        self.widgets["peak_min_sep"].configure(state="readonly")
        self.widgets["peak_threshold"].configure(state="readonly")
        self.widgets["find_peaks"].configure(state="disabled")
        self.widgets["save_peaks"].configure(state="disabled")
        self.widgets["next_peak"].configure(state="disabled")
        self.widgets["peak_index"].configure(state="disabled")

    def enablePeakFindingWidgets(self):
        ##
        ## ENABLES THE APPROPRIATE PEAK FINDING UI ELEMENTS.
        ##
        self.widgets["peak_min_sep"].configure(state="normal")
        self.widgets["peak_threshold"].configure(state="normal")
        self.widgets["find_peaks"].configure(state="normal")
        if "peak_finding" in self.save_data: # If the user has already saved peak data:
            self.widgets["save_peaks"].configure(state="normal")
            self.widgets["next_peak"].configure(state="normal")
            self.widgets["peak_index"].configure(state="normal")

    def goToIndexPeak(self, index):
        ##
        ## [Event Handler] MOVES THE SCANNING MIRROR TO THE PEAK CORRESPONDING TO INDEX. 
        ##
        peaks_x_coords = self.save_data["peak_finding"]["peaks_x_coords"]
        peaks_y_coords = self.save_data["peak_finding"]["peaks_y_coords"]
        real_index = index % len(peaks_x_coords) # Wrap around list if user enters an index out of bounds.
        x_coord = round(peaks_x_coords[real_index], 3)
        y_coord = round(peaks_y_coords[real_index], 3)
        if index != real_index:
            self.widgets["peak_index"].delete(0, tk.END)
            self.widgets["peak_index"].insert(0, str(real_index))
        self.widgets["cursor_custom_x"].delete(0, tk.END)
        self.widgets["cursor_custom_y"].delete(0, tk.END)
        self.widgets["cursor_custom_x"].insert(0, str(x_coord))
        self.widgets["cursor_custom_y"].insert(0, str(y_coord))
        self.removeCrosshair()
        self.placeCrosshair(x_coord, y_coord)
        self.moveScanningMirror(x_coord, y_coord)
        print(f"({x_coord, y_coord})")
    
    def goToNextPeak(self, inc):
        ##
        ## [Event Handler] INCREMEMNTS THE PEAK # IN THE UI THEN POINTS THE SCANNING
        ## MIRROR AT THAT NEXT PEAK.
        ##
        peaks_x_coords = self.save_data["peak_finding"]["peaks_x_coords"] # x or y arbitrary since the lists are the same length....
        current_index = int(self.widgets["peak_index"].get())
        # Wrap around list if necessary to get the next index.
        next_index = (current_index + inc) % len(peaks_x_coords)
        # Update the peak index entry widget with the new index.
        self.widgets["peak_index"].delete(0, tk.END)
        self.widgets["peak_index"].insert(0, str(next_index))
        # Move the scanning mirror correspondingly.
        self.goToIndexPeak(next_index)

    def getName(self):
        ##
        ## RETURNS THE USER-INPUTTED FILENAME.
        ##
        # return self.ID + "_" + str(self.widgets["savename"].get())
        return str(self.widgets["savename"].get())
    
    def getFolder(self):
        ##
        ## RETURNS THE USER-SELECTED PATH AS A STRING.
        ##
        return self.controlmenu.widgets["folder"].cget("text")
    
    def getPath(self, suffix=None):
        ##
        ## GENERATES PATH FOR SAVING.
        ##
        file_name = self.getName()
        if suffix != None:
            file_name += suffix
        path = os.path.join(self.getFolder(),file_name)
        return path

    def saveJson(self, path):
        ##
        ## SAVES SCAN DATA IN JSON FILE.
        ##
        datafile_json = json.dumps(self.save_data, indent=4)
        with open(path+".json", "w") as file:   
            file.write(datafile_json)
        print("Data file saved!")
    
    def savePlot(self, path, annotations=False):
        ##
        ## SAVES PLOT AS PNG. IF annotations IS FALSE, SAVE A CLEAR PLOT.
        ##
        lines = []
        if self.crosshair:
            self.removeCrosshair()
        if annotations == False:
            # Remove all annotations.
            lines = self.clearAnnotations()

        self.fig.savefig(path, dpi='figure')
        print("Data plot saved!")

        if annotations == False:
            # Replace annotations.
            self.replotAnnotations(lines)
        if self.crosshair:
            # Replace crosshair.
            self.placeCrosshair(self.cursor_coordinates[0], self.cursor_coordinates[1])

    def onSaveScan(self):
        ##
        ## [Event Handler] SAVES THE DATA AND PLOT FOR THE SCAN (NO ANNOTATIONS).
        ##
        path = self.getPath()
        self.saveJson(path)
        self.savePlot(path)
    
    def onSavePeaks(self):
        ##
        ## [Event Handler] SAVES THE PEAKS DATA AND PLOT WITH ANNOTATIONS.
        ##
        data_path = self.getPath()
        plot_path = self.getPath(suffix="_peakfinding")
        self.saveJson(data_path)
        self.savePlot(plot_path, annotations=True)

    def onClosing(self):
        ##
        ## [Event Handler] CLOSES SCAN WINDOW & AJUSTS UI.
        ##
        if self.currently_scanning:
            print("quit while scanning!")
            self.controlmenu.interruptScanEvent()
        self.controlmenu.widgets["custom_json_button"].configure(state="disabled")
        self.controlmenu.scanwindow = None
        self.destroy()
        self.update()
    
