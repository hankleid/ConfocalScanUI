import os
import json
import tkinter as tk
from tkinter import ttk, StringVar
from tkinter.filedialog import askdirectory
import random
import numpy as np
import time
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from datetime import datetime

class ScanWindow(tk.Toplevel):
    parent_app = None
    ID = ""
    currently_scanning = False
    scan_data = None # 2D numpy data
    datastream = [] # Contains all the data in a flattened list, appended as the scan progresses. For internal use, like min/max.
    xy_range = [0, 0, 0, 0] # x range, y range
    x_data = None # X axis array
    y_data = None # Y axis array
    fig = None # Matplotlib figure for the scan
    ax = None # The actual plot.
    widgets = {}
    cursor_coordinates = [0,0]
    counts_minmax = [0,0]
    autoscale = True # (for colorbar) True if autoscale; False if user input

    def __init__(self, app, *args, **kwargs):
        tk.Toplevel.__init__(self, *args, **kwargs)
        self.protocol("WM_DELETE_WINDOW", self.onClosing)
        self.ID = self.generateScanID()
        self.title("Scan "+str(len(app.subwindows)+1)+": "+self.ID)
        self.parent_app = app # Access control menu through this App object.

        self.columnconfigure([0, 1], minsize=200)
        self.rowconfigure(0, minsize=50)

        # Frame that holds the scan.
        frm_side_info = tk.Frame(
            master=self,
            relief=tk.RAISED,
            borderwidth=1
        )
        # Frame that holds the side info widgets.
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

        # Init scan params
        parent_widgets = self.parent_app.widgets
        x_start = float(parent_widgets["x_start"].get())
        x_end = float(parent_widgets["x_end"].get())
        x_step = float(parent_widgets["x_step"].get())
        y_start = float(parent_widgets["y_start"].get())
        y_end = float(parent_widgets["y_end"].get())
        y_step = float(parent_widgets["y_step"].get())
        self.xy_range = [x_start, x_end, y_start, y_end]

        # X and Y voltage axes.
        self.x_data = np.linspace(x_start, x_end, int((x_end - x_start) / x_step)+1)
        self.y_data = np.linspace(y_start, y_end, int((y_end - y_start) / y_step)+1)

        # Initialize data array.
        self.scan_data = np.zeros((len(self.x_data), len(self.y_data))) #  Data for plotting and saving.

        self.generateSideInfo()
        self.generatePlotHolder()

    def generateSideInfo(self):
        ##
        ## PLACES A GRID IN THE SIDE INFO FRAME; WIDGETS ORGANIZED INTO FRAMES THEN ADDED TO GRID.
        ##
        frm_side_info = self.widgets["side_info_frame"]
        sideinfo_frames = []
        
        # Colobar settings frame.
        frm_colorbar_settings = tk.Frame(
            master=frm_side_info,
            relief=tk.RAISED,
            borderwidth=0
        )
        sideinfo_frames.append(frm_colorbar_settings)
        frm_minmax = tk.Frame(master=frm_colorbar_settings, relief=tk.RAISED, borderwidth=0)
        ent_min = tk.Entry(master=frm_minmax, width=5)
        ent_max = tk.Entry(master=frm_minmax, width=5)
        ent_min.insert(0, "0")
        ent_max.insert(0, "5000")
        ent_min.bind('<Return>', lambda e: self.changeColorbar(autoscale=False))
        ent_max.bind('<Return>', lambda e: self.changeColorbar(autoscale=False))
        self.widgets["user_min"] = ent_min
        self.widgets["user_max"] = ent_max
        ent_min.pack(padx=1, pady=1, side=tk.LEFT)
        ent_max.pack(padx=1, pady=1, side=tk.LEFT)
        lbl_colorbar_settings = tk.Label(master=frm_colorbar_settings, text="colorbar min/max:", padx=1, pady=1)
        btn_autoscale = tk.Button(master=frm_colorbar_settings, text="Autoscale", command=lambda: self.changeColorbar(autoscale=True))
        self.widgets["colorbar_palette"] = StringVar()
        cbox_colors = ttk.Combobox(master=frm_colorbar_settings,
                                   textvariable=self.widgets["colorbar_palette"],
                                   values=["gray", "viridis", "plasma", "inferno", "magma", "cividis"],
                                   state="readonly",
                                   width=10)
        cbox_colors.current(0) # Set default dropdown value to the first value of ^ list.
        cbox_colors.bind("<<ComboboxSelected>>", lambda e: self.changeColorbar(self.autoscale))
        lbl_colorbar_settings.pack(padx=1, pady=1)
        frm_minmax.pack(padx=1, pady=1)
        btn_autoscale.pack(padx=1, pady=1)
        cbox_colors.pack(padx=1, pady=1, side=tk.BOTTOM)

        # Counts indicator frame.
        frm_counts = tk.Frame(
            master=frm_side_info,
            relief=tk.RAISED,
            borderwidth=0
        )
        sideinfo_frames.append(frm_counts)
        lbl_counts = tk.Label(master=frm_counts, text="counts:", padx=1, pady=1)
        lbl_counts_measure = tk.Label(
            master=frm_counts,
            text="0",
            fg="red",
            bg="white"
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
        btn_cursor_move = tk.Button(master=frm_cursor, text="Move to Cursor", command=self.moveCursor)
        btn_cursor_center = tk.Button(master=frm_cursor, text="Center", command=self.moveCursor)
        lbl_cursor_coordinates = tk.Label(
            master=frm_cursor,
            text="",
            fg="red"
        )
        self.widgets["cursor_move_button"] = btn_cursor_move
        self.widgets["cursor_center_button"] = btn_cursor_center
        self.widgets["cursor_coordinates"] = lbl_cursor_coordinates
        btn_cursor_move.pack(padx=1, pady=1)
        btn_cursor_center.pack(padx=1, pady=1)
        lbl_cursor_coordinates.pack(padx=1, pady=1, side=tk.BOTTOM)

        # Custom coordinates frame.
        frm_customcoords = tk.Frame(
            master=frm_side_info,
            relief=tk.RAISED,
            borderwidth=0
        )
        sideinfo_frames.append(frm_customcoords)
        lbl_customcoords = tk.Label(master=frm_customcoords, text="custom coordinates:", padx=1, pady=1)
        btn_uploadjson = tk.Button(master=frm_customcoords, text="Upload .json", command=self.uploadCustomCoords)
        btn_gocustom = tk.Button(master=frm_customcoords, text="Go", command=self.goCustomCoords)
        lbl_jsonfilename = tk.Label(master=frm_customcoords, text="", fg="blue", padx=1, pady=1)
        self.widgets["custom_go_button"] = btn_gocustom
        self.widgets["custom_coords_path"] = lbl_jsonfilename
        lbl_customcoords.pack(padx=1, pady=1)
        btn_uploadjson.pack(padx=1, pady=1)
        btn_gocustom.pack(padx=1, pady=1)
        lbl_jsonfilename.pack(padx=1, pady=1)

        # Save settings frame.
        frm_all_save_info = tk.Frame(
            master=frm_side_info,
            relief=tk.RAISED,
            borderwidth=0
        )
        sideinfo_frames.append(frm_all_save_info)
        frm_savename = tk.Frame(master=frm_all_save_info, relief=tk.RAISED, borderwidth=0)
        lbl_savename = tk.Label(master=frm_savename, text="savename:", padx=1, pady=1)
        ent_savename = tk.Entry(master=frm_savename, fg="blue", width=15)
        ent_savename.insert(0, "untitled")
        self.widgets["savename"] = ent_savename
        lbl_savename.pack(padx=1, pady=1, side=tk.LEFT)
        ent_savename.pack(padx=1, pady=1, side=tk.LEFT)
        frm_foldername = tk.Frame(master=frm_all_save_info, relief=tk.RAISED, borderwidth=0)
        lbl_foldername_indicator = tk.Label(master=frm_foldername, text="folder:", padx=1, pady=1)       
        lbl_foldername = tk.Label(master=frm_foldername, text=str(os.getcwd()), fg="blue", padx=1, pady=1)       
        lbl_foldername_indicator.pack(padx=1, pady=1, side=tk.LEFT)
        lbl_foldername.pack(padx=1, pady=1, side=tk.LEFT)
        self.widgets["folder"] = lbl_foldername
        frm_savebuttons = tk.Frame(master=frm_all_save_info, relief=tk.RAISED, borderwidth=0)
        btn_selectfolder = tk.Button(master=frm_savebuttons, text="Select Folder", command=self.selectSaveFolder)
        btn_save = tk.Button(master=frm_savebuttons, text="Save", command=self.saveScan)
        btn_selectfolder.pack(padx=1, pady=1, side=tk.LEFT)
        btn_save.pack(padx=1, pady=1, side=tk.LEFT)
        self.widgets["save_button"] = btn_save
        frm_savename.pack(padx=1, pady=1)
        frm_foldername.pack(padx=1, pady=1)
        frm_savebuttons.pack(padx=1, pady=1)

        # Add to local grid (show).
        frm_side_info.columnconfigure(0, minsize=250)
        frm_side_info.rowconfigure([i for i in range(len(sideinfo_frames))], minsize=120)
        for i in range(len(sideinfo_frames)):
            sideinfo_frames[i].grid(column=0, row=i)
    
    def generatePlotHolder(self):
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
            bg="black")
        frm_plot.grid(column=0, row=0)

        # Initialize matplotlib figure.
        aspectratio = (self.xy_range[3]-self.xy_range[2]) / (self.xy_range[1]-self.xy_range[0])
        dimx = 7
        dimy = 5.5
        if aspectratio >= 1: # Portrait
            dimx /= aspectratio
        else: # Landscape
            dimy *= aspectratio
        self.fig = plt.figure(figsize = (max(4, dimx), max(2, dimy)))
        canvas = FigureCanvasTkAgg(self.fig, master=frm_plot)
        self.ax = self.fig.add_subplot(111)
        self.widgets["canvas"] = canvas
        # Put canvas on the GUI.
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        self.widgets["plot_clicker"] = None

    def generateScanID(self):
        ##
        ## RETURNS A String IN THE FORM YYYY(M)M(D)D(H)H(M)M(S)S.
        ##
        now = datetime.now()
        return str(now.year)+str(now.month)+str(now.day)+str(now.hour)+str(now.minute)+str(now.second)

    def takeMeasurement(self, V_x, V_y):
        ##
        ## MOVES THE SCANNING MIRROR TO (x, y) THEN RETURNS A MEASUREMENT OF COUNTS.
        ##
        int_time = float(self.parent_app.widgets["int_time"].get())
        # move FSM
        move = V_x * V_y
        # Wait for the duration of integration time.
        time.sleep(int_time * 1e-3)
        # Take measurement from SPCM.
        measurement = random.random()*10000 * move
        # Adjust measurement to count/s.
        measurement /= int_time

        return abs(round(measurement, 2))

    def takeScan(self):
        ##
        ## TAKES A SCAN & VISUALIZES IT ON THE CANVAS.
        ##

        # Disable certain buttons while scan runs.
        self.widgets["cursor_move_button"].configure(state="disabled")
        self.widgets["cursor_center_button"].configure(state="disabled")
        self.widgets["save_button"].configure(state="disabled")
        self.widgets["custom_go_button"].config(state="disabled")

        self.currently_scanning = True

        # Scan start.
        for y_i in range(len(self.y_data)):
            for i in range(len(self.x_data)):
                if str(self.parent_app.widgets["interrupt_button"]["state"]) == "disabled":
                    # If 'Interrupt' button is pressed, stop scan.
                    break
                
                x_i = 0
                # Change direction every column.
                if y_i % 2 == 0: # Even: scan in the forward direction.
                    x_i = i
                else: # Odd: scan in the backward direction.
                    x_i = -(i+1)

                # Coordinates.
                x = self.x_data[x_i]
                y = self.y_data[y_i]
                
                # Take measurement & record data.
                current_counts = self.takeMeasurement(x, y)
                self.widgets["counts"].config(text=str(current_counts))
                self.scan_data[x_i][y_i] = current_counts
                self.datastream.append(current_counts)

                if self.autoscale:
                    self.counts_minmax[0] = min(self.datastream)
                    self.counts_minmax[1] = max(self.datastream)
            
                self.plotWithColorbar()
        
        # Scan end.
        self.currently_scanning = False
        print("Scan done.")

        self.parent_app.interruptScanEvent()
        # Enable cursor buttons.
        self.widgets["cursor_move_button"].configure(state="normal")
        self.widgets["cursor_center_button"].configure(state="normal")
        self.widgets["save_button"].configure(state="normal")
        # Place crosshairs in the middle of the plot (not clicking cursor) to prep for mouse event.
        self.placeCrosshair((self.xy_range[1]+self.xy_range[0])/2, (self.xy_range[3]+self.xy_range[2])/2)
        # plot_clicker is the callback ID for the matplotlib mouse click event. Stored in widgets for future access to disconnect/reconnect.
        self.connectPlotClicker()

    def plotWithColorbar(self):
        # 
        # Refresh figure by clearing fig and remaking ax. Then plot.
        # 
        self.fig.clear()
        self.ax = self.fig.add_subplot(111)
        plot = self.ax.imshow(self.scan_data,
                            extent=self.xy_range,
                            origin='lower',
                            cmap=self.widgets["colorbar_palette"].get(),
                            vmin=self.counts_minmax[0],
                            vmax=self.counts_minmax[1])
        self.fig.colorbar(plot, ax=self.ax)
        self.widgets["canvas"].draw()
        self.widgets["canvas"].get_tk_widget().pack(expand=True)

        # Update the UI... tkinter made me do it :/
        self.update()
        self.update_idletasks()
    
    def changeColorbar(self, autoscale):
        self.autoscale = autoscale
        if self.autoscale:
            # Autoscale.
            self.counts_minmax[0] = min(self.datastream)
            self.counts_minmax[1] = max(self.datastream)
            print(f"Min/max counts: {self.counts_minmax[0]}, {self.counts_minmax[1]}")
        else:
            # User min/max.
            self.counts_minmax[0] = float(self.widgets["user_min"].get())
            self.counts_minmax[1] = float(self.widgets["user_max"].get())
        if not self.currently_scanning:
            # Only update plot if scan is done. While scan is currently running, the plot gets refreshed often enough.
            self.plotWithColorbar()
            self.placeCrosshair(self.cursor_coordinates[0], self.cursor_coordinates[1])

    def onClicking(self, e):
        #
        # [Event Handler] Refreshes the crosshair placement at the location of the mouse click.
        # Does nothing if the user clicks outside of the plot.
        #
        outside_plot = e.xdata is None or e.ydata is None
        inside_colorbar = False
        if not outside_plot:
            inside_colorbar = e.ydata > self.xy_range[3] or e.xdata < self.xy_range[0]
        if outside_plot or inside_colorbar:
            # If clicked outside the plot (or inside the colorbar):
            print("out of bounds")
        else:
            self.removeCrosshair()
            self.placeCrosshair(e.xdata, e.ydata)

    def connectPlotClicker(self):
        #
        # Connects the mouse click event handling connection to the matplotlib plot.
        # Callback id (cid) global variable for keeping track of the current handler.
        #
        self.widgets["plot_clicker"] = self.widgets["canvas"].mpl_connect('button_press_event', lambda e: self.onClicking(e))

    def disconnectPlotClicker(self):
        #
        # Disconnects the mouse click event handling connection from the matplotlib plot.
        # Callback id (cid) global variable for keeping track of the current handler.
        #
        cid = self.widgets["plot_clicker"]
        self.widgets["canvas"].mpl_disconnect(cid)

    def moveCursor(self):
        print("cursor move")

    def placeCrosshair(self, x_coord, y_coord):
        #
        # Places a crosshair (marker + perpendiuclar lines) on the plot.
        #
        x_coord = round(x_coord, 2)
        y_coord = round(y_coord, 2)
        self.ax.axhline(y = y_coord, color = 'r', linestyle = '-', linewidth=1)
        self.ax.axvline(x = x_coord, color = 'r', linestyle = '-', linewidth=1)
        self.ax.plot([x_coord], [y_coord], "s", markersize=5.5, markerfacecolor="None", markeredgewidth=1, markeredgecolor="cyan")
        self.widgets["canvas"].draw()
        self.cursor_coordinates = [x_coord, y_coord]
        self.widgets["cursor_coordinates"].config(text=f"({x_coord}, {y_coord})")

    def removeCrosshair(self):
        #
        # Removes the crosshair from the plot. If no crosshair, does nothing.
        #
        if len(self.ax.lines) <= 1:
            print("error: there is no crosshair to remove.")
        else:
            self.ax.lines.pop()
            self.ax.lines.pop()
            self.ax.lines.pop()

    def uploadCustomCoords(self):
        self.widgets["custom_go_button"].config(state="normal")
    
    def goCustomCoords(self):
        #
        # [Event Handler] TOGGLES CUSTOM SCANNING.
        #
        self.currently_scanning = not self.currently_scanning # Toggle self.currently_scanning.
        # Refresh plot without crosshair.
        self.disconnectPlotClicker()
        ax = self.plotWithColorbar(self.autoscale)
        if self.currently_scanning: # Start scanning.
            self.widgets["custom_go_button"].config(text="Stop")
            i = 0
            while str(self.widgets["custom_go_button"]["state"]) != "disabled":
                #time.sleep(1)
                print("yah " + str(i))
                i += 1
        else: # Stop scanning.
            print("stopping")
            # Replace crosshair.
            self.placeCrosshair(self.cursor_coordinates[0], self.cursor_coordinates[1])
            self.connectPlotClicker(ax)
            self.widgets["custom_go_button"].config(text="Go")
    
    def selectSaveFolder(self):
        self.widgets["folder"].config(text=str(askdirectory()))

    def saveScan(self):
        file_name = self.ID + "_" + str(self.widgets["savename"].get())
        path = os.path.join(self.widgets["folder"].cget("text"),file_name)

        # Save data to .json file.
        datafile = {
            "integration_time": float(self.parent_app.widgets["int_time"].get()),
            "x": self.x_data.tolist(),
            "y": self.y_data.tolist(),
            "data": self.scan_data.tolist()
        }
        datafile_json = json.dumps(datafile, indent=4)
        with open(path+".json", "w") as file:   
            file.write(datafile_json)

        # Save the figure (without crosshair).
        self.plotWithColorbar() # refresh the image w/o cursors.
        self.fig.savefig(path, dpi='figure')
        # refresh crosshair.
        self.placeCrosshair(self.cursor_coordinates[0], self.cursor_coordinates[1])

        print("Data file & plot saved!")

    def onClosing(self):
        ##
        ## [Event Handler] CLOSES SCAN WINDOW & AJUSTS UI.
        ##
        if self.parent_app.isScanRunning() is False:
            # Only reset the start button if no other scans are running.
            self.parent_app.widgets["start_button"].configure(state="active")
            self.destroy()
    