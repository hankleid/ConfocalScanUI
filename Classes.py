import os
import tkinter as tk
import tkinter.ttk as ttk
from tkinter.filedialog import askopenfilename, asksaveasfilename
#import images as im
from PIL import Image, ImageTk
import random
import numpy as np
import time

class App(tk.Tk):
    widgets = {} # Grid --> frames --> widgets
    subwindows = []

    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)
        self.title("Control Menu")
        self.generateControlMenu() # Grid is generated in this method

    def startScanEvent(self):
        ##
        ## [Event handler] STARTS SCAN.
        ##
        self.widgets["start_button"].config(state="disabled")
        self.widgets["interrupt_button"].config(state="active")

        print("start")
        subwindow = ScanWindow(self)
        self.subwindows.append(subwindow)
        subwindow.takeScan()
        return
    
    def interruptScanEvent(self):
        ##
        ## [Event handler] INTERRUPTS SCAN.
        ##
        self.widgets["start_button"].config(state='active')
        self.widgets["interrupt_button"].config(state='disabled')

        print("interrupt")
        return

    def generateControlMenu(self):
        ##
        ## PLACES FEATURES INTO A GRID ON THE CONTROL MENU.
        ##

        widget_frames = []

        # X voltage selection frame.
        frm_x = tk.Frame(
            master=self,
            relief=tk.RAISED,
            borderwidth=0
        )
        widget_frames.append(frm_x)
        lbl_x = tk.Label(master=frm_x, text="x:", padx=1, pady=1)
        ent_x_start = tk.Entry(master=frm_x, width=3)
        ent_x_end = tk.Entry(master=frm_x, width=3)
        ent_x_start.insert(0, "-1")
        ent_x_end.insert(0, "1")
        lbl_x_step = tk.Label(master=frm_x, text="step:", padx=1, pady=1)
        ent_x_step= tk.Entry(master=frm_x, width=5)
        ent_x_step.insert(0, "0.01")
        self.widgets["x_start"] = ent_x_start
        self.widgets["x_end"] = ent_x_end
        self.widgets["x_step"] = ent_x_step
        lbl_x.pack(padx=1, pady=1, side=tk.LEFT)
        ent_x_start.pack(padx=1, pady=1, side=tk.LEFT)
        ent_x_end.pack(padx=1, pady=1, side=tk.LEFT)
        lbl_x_step.pack(padx=1, pady=1, side=tk.LEFT)
        ent_x_step.pack(padx=1, pady=1, side=tk.LEFT)

        # Y voltage selection frame.
        frm_y = tk.Frame(
            master=self,
            relief=tk.RAISED,
            borderwidth=0
        )
        widget_frames.append(frm_y)
        lbl_y = tk.Label(master=frm_y, text="y:", padx=1, pady=1)
        ent_y_start = tk.Entry(master=frm_y, width=3)
        ent_y_end = tk.Entry(master=frm_y, width=3)
        ent_y_start.insert(0, "-1")
        ent_y_end.insert(0, "1")
        lbl_y_step = tk.Label(master=frm_y, text="step:", padx=1, pady=1)
        ent_y_step= tk.Entry(master=frm_y, width=5)
        ent_y_step.insert(0, "0.01")
        self.widgets["y_start"] = ent_y_start
        self.widgets["y_end"] = ent_y_end
        self.widgets["y_step"] = ent_y_step
        lbl_y.pack(padx=1, pady=1, side=tk.LEFT)
        ent_y_start.pack(padx=1, pady=1, side=tk.LEFT)
        ent_y_end.pack(padx=1, pady=1, side=tk.LEFT)
        lbl_y_step.pack(padx=1, pady=1, side=tk.LEFT)
        ent_y_step.pack(padx=1, pady=1, side=tk.LEFT)

        # Integration time frame.
        frm_int = tk.Frame(
            master=self,
            relief=tk.RAISED,
            borderwidth=0
        )
        widget_frames.append(frm_int)
        lbl_int = tk.Label(master=frm_int, text="integration time:", padx=1, pady=1)
        ent_int = tk.Entry(master=frm_int, width=3)
        ent_int.insert(0, "5")
        self.widgets["int_time"] = ent_int
        lbl_int.pack(padx=1, pady=5, side=tk.LEFT)
        ent_int.pack(padx=1, pady=5, side=tk.LEFT)

        # Start/Interrupt scan buttons frame.
        frm_buttons = tk.Frame(
            master=self,
            relief=tk.RAISED,
            borderwidth=0
        )
        widget_frames.append(frm_buttons)
        btn_start = tk.Button(master=frm_buttons, text="Start Scan", command=self.startScanEvent)
        btn_interrupt = tk.Button(master=frm_buttons, text="Interrupt", command=self.interruptScanEvent)
        self.widgets["start_button"] = btn_start
        self.widgets["interrupt_button"] = btn_interrupt
        btn_start.pack(padx=5, pady=5, side=tk.LEFT)
        btn_interrupt.pack(padx=5, pady=5, side=tk.LEFT)

        # Add to grid (show).
        self.columnconfigure(0, minsize=300)
        self.rowconfigure([i for i in range(len(widget_frames))], minsize=5)
        for i in range(len(widget_frames)):
            widget_frames[i].grid(column=0, row=i)

    def isScanRunning(self):
        for subwindow in self.subwindows:
            if subwindow.currently_scanning:
                return True
        return False

class ScanWindow(tk.Toplevel):
    parent_app = None
    currently_scanning = False
    scan = None # 2D numpy data
    widgets = {}
    img = None
    size = 500

    def __init__(self, app, *args, **kwargs):
        tk.Toplevel.__init__(self, *args, **kwargs)
        self.protocol("WM_DELETE_WINDOW", self.onClosing)
        self.title("Scan")
        self.parent_app = app # Access control menu through this App object.

        self.columnconfigure([0, 1], minsize=100)
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

        self.generateSideInfo()
        self.generateScanCanvas()

    def generateSideInfo(self):
        ##
        ## PLACES A GRID IN THE SIDE INFO FRAME; WIDGETS ORGANIZED INTO FRAMES THEN ADDED TO GRID.
        ##

        frm_side_info = self.widgets["side_info_frame"]
        sideinfo_frames = []

        # Counts indicator frame.
        frm_counts = tk.Frame(
            master=frm_side_info,
            relief=tk.RAISED,
            borderwidth=1
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

        # Add to local grid (show).
        frm_side_info.columnconfigure(0, minsize=50)
        frm_side_info.rowconfigure([i for i in range(len(sideinfo_frames))], minsize=5)
        for i in range(len(sideinfo_frames)):
            sideinfo_frames[i].grid(column=0, row=i)
    
    def generateScanCanvas(self):
        ##
        ## ADDS A CANVAS (FOR VISUALIZING DATA) TO A 1X1 GRID ON THE SCAN FRAME.
        ##

        frm_scan = self.widgets["scan_frame"]
        frm_scan.columnconfigure(0)
        frm_scan.rowconfigure(0)
        canvas = tk.Canvas(frm_scan, width=500, height=500, bg="black")
        self.widgets["canvas"] = canvas
        canvas.grid(column=0, row=0)

    def measureCounts(self, V_x, V_y):
        ##
        ## RETURNS A MEASUREMENT OF COUNTS.
        ##

        time.sleep(float(self.parent_app.widgets["int_time"].get()) * 1e-3)
        counts = random.random()*10000 * V_x * V_y
        return round(counts, 2)

    def takeScan(self):
        ##
        ## TAKES A SCAN & VISUALIZES IT ON THE CANVAS.
        ##
        
        parent_widgets = self.parent_app.widgets
        x_start = float(parent_widgets["x_start"].get())
        x_end = float(parent_widgets["x_end"].get())
        x_step = float(parent_widgets["x_step"].get())
        y_start = float(parent_widgets["y_start"].get())
        y_end = float(parent_widgets["y_end"].get())
        y_step = float(parent_widgets["y_step"].get())
        
        # X and Y voltage axes.
        x_data = np.linspace(x_start, x_end, int((x_end - x_start) / x_step)+1)
        y_data = np.linspace(y_start, y_end, int((y_end - y_start) / y_step)+1)

        self.currently_scanning = True

        self.scan = np.zeros((len(x_data), len(y_data)))
        scan_BW = np.zeros((len(x_data), len(y_data)))
        for x_i in range(len(y_data)):
            for y_i in range(len(x_data)):
                if str(self.parent_app.widgets["interrupt_button"]['state']) == "disabled":
                    # If 'Interrupt' button is pressed, stop scan.
                    break

                x = x_data[x_i]
                y = y_data[y_i]
                current_counts = self.measureCounts(x, y)
                self.widgets["counts"].config(text=str(current_counts))
                max_counts = max(map(max, self.scan)) # Maximum value of the 2D data array.

                self.scan[x_i][y_i] = current_counts
                # Adjust display data to dim previous data if current data is bright (contrast).
                if current_counts >= max_counts:
                    scan_BW = self.scan / current_counts
                    scan_BW[x_i][y_i] = 1
                else:
                    scan_BW[x_i][y_i] = current_counts / max_counts

                # Update the UI... tkinter made me do it :/
                self.update()
                self.update_idletasks()

        print(self.scan)
        print(scan_BW)
        self.currently_scanning = False

    def onClosing(self):
        ##
        ## [Event Handler] CLOSES SCAN WINDOW & AJUSTS UI.
        ##

        if self.parent_app.isScanRunning() is False:
            # Only reset the start button if no other scans are running.
            self.parent_app.widgets["start_button"].configure(state="active")
            self.destroy()
    