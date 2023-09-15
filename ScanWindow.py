import tkinter as tk
import random
import numpy as np
import time
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from datetime import datetime

class ScanWindow(tk.Toplevel):
    parent_app = None
    currently_scanning = False
    scan_data = None # 2D numpy data
    datastream = [] # Contains all the data in a flattened list, appended as the scan progresses. For internal use, like min/max.
    extent = [0, 0, 0, 0] # x range, y range
    x_data = None # X axis array
    y_data = None # Y axis array
    fig = None # Matplotlib figure for the scan
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
        self.extent = [x_start, x_end, y_start, y_end]

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
        ent_min.bind('<Return>', lambda e: self.changeMinMax(autoscale=False))
        ent_max.bind('<Return>', lambda e: self.changeMinMax(autoscale=False))
        self.widgets["user_min"] = ent_min
        self.widgets["user_max"] = ent_max
        ent_min.pack(padx=1, pady=1, side=tk.LEFT)
        ent_max.pack(padx=1, pady=1, side=tk.LEFT)
        lbl_colorbar_settings = tk.Label(master=frm_colorbar_settings, text="colorbar min/max:", padx=1, pady=1)
        btn_autoscale = tk.Button(master=frm_colorbar_settings, text="Autoscale", command=lambda: self.changeMinMax(autoscale=True))
        lbl_colorbar_settings.pack(padx=1, pady=1)
        frm_minmax.pack(padx=1, pady=1)
        btn_autoscale.pack(padx=1, pady=1)

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

        # Add to local grid (show).
        frm_side_info.columnconfigure(0, minsize=100)
        frm_side_info.rowconfigure([i for i in range(len(sideinfo_frames))], minsize=75)
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
        self.fig = plt.figure(figsize = (7, 7))
        canvas = FigureCanvasTkAgg(self.fig, master=frm_plot)
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

        # Disable cursor buttons while scan runs.
        self.widgets["cursor_move_button"].configure(state="disabled")
        self.widgets["cursor_center_button"].configure(state="disabled")

        self.currently_scanning = True
        ax = self.fig.add_subplot(111) # Plot that updates with the scan every iteration.

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
            
                ax = self.plotWithColorbar(self.autoscale)
        
        # Scan end.
        self.currently_scanning = False
        print("Scan done.")

        self.parent_app.interruptScanEvent()
        # Enable cursor buttons.
        self.widgets["cursor_move_button"].configure(state="normal")
        self.widgets["cursor_center_button"].configure(state="normal")
        # Place crosshairs in the middle of the plot (not clicking cursor) to prep for mouse event.
        self.placeCrosshair((self.extent[1]+self.extent[0])/2, (self.extent[3]+self.extent[2])/2, ax)
        # plot_clicker is the callback ID for the matplotlib mouse click event. Stored in widgets for future access to disconnect/reconnect.
        self.connectPlotClicker(ax, refresh=True)

    def plotWithColorbar(self, autoscale=True):
        # 
        # Refresh figure by clearing fig and remaking ax. Then plot.
        # 
        self.autoscale = autoscale
        self.fig.clear()
        ax = self.fig.add_subplot(111)
        plot = ax.imshow(self.scan_data,
                            extent=self.extent,
                            origin='lower',
                            cmap='gray',
                            vmin=self.counts_minmax[0],
                            vmax=self.counts_minmax[1])
        self.fig.colorbar(plot, ax=ax)
        self.widgets["canvas"].draw()
        self.widgets["canvas"].get_tk_widget().pack(expand=True)

        # Update the UI... tkinter made me do it :/
        self.update()
        self.update_idletasks()
        return ax
    
    def changeMinMax(self, autoscale):
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
            ax = self.plotWithColorbar()
            self.placeCrosshair(self.cursor_coordinates[0], self.cursor_coordinates[1], ax)
            self.connectPlotClicker(ax, refresh=True)

    def connectPlotClicker(self, ax, refresh=False):
        cid = self.widgets["plot_clicker"]
        if cid:
            self.widgets["canvas"].mpl_disconnect(cid)
        else:
            pass #if nothing to disconnect, do not disconnect anything
        self.widgets["plot_clicker"] = self.widgets["canvas"].mpl_connect('button_press_event', lambda e: self.placeCrosshair(e.xdata, e.ydata, ax, refresh))

    def moveCursor(self):
        print("cursor move")

    def placeCrosshair(self, x_coord, y_coord, ax, refresh=False):
        #
        # [Event Handler] Places a crosshair (marker + perpendiuclar lines) on the plot.
        # Removes the previous crosshair if refresh is True.
        #
        if x_coord is None or y_coord is None:
            # If clicked outside the plot:
            return
        if refresh:
            ax.lines.pop()
            ax.lines.pop()
            ax.lines.pop()
            
        x_coord = round(x_coord, 2)
        y_coord = round(y_coord, 2)
        ax.axhline(y = y_coord, color = 'r', linestyle = '-', linewidth=1)
        ax.axvline(x = x_coord, color = 'r', linestyle = '-', linewidth=1)
        ax.plot([x_coord], [y_coord], "s", markersize=5.5, markerfacecolor="None", markeredgewidth=1, markeredgecolor="cyan")
        self.widgets["canvas"].draw()
        self.cursor_coordinates = [x_coord, y_coord]
        self.widgets["cursor_coordinates"].config(text=f"({x_coord}, {y_coord})")

    def onClosing(self):
        ##
        ## [Event Handler] CLOSES SCAN WINDOW & AJUSTS UI.
        ##
        if self.parent_app.isScanRunning() is False:
            # Only reset the start button if no other scans are running.
            self.parent_app.widgets["start_button"].configure(state="active")
            self.destroy()
    