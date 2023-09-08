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
    widgets = {}
    img = None
    size = 500

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

        self.generateSideInfo()
        self.generatePlotHolder()

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

        # Add to local grid (show).
        frm_side_info.columnconfigure(0, minsize=100)
        frm_side_info.rowconfigure([i for i in range(len(sideinfo_frames))], minsize=5)
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
            width=500,
            height=500,
            relief=tk.RAISED,
            bg="black")
        self.widgets["plot_holder"] = frm_plot
        frm_plot.grid(column=0, row=0)

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
        print(len(x_data))
        print(len(y_data))
        self.currently_scanning = True

        # Initialize data array.
        self.scan_data = np.zeros((len(x_data), len(y_data)))

        # Initialize matplotlib figure.
        fig = plt.figure(figsize = (7, 7))
        ax = fig.add_subplot(111)
        #plt.ion()
        canvas = FigureCanvasTkAgg(fig, master=self.widgets["plot_holder"])
        canvas.draw()
        canvas.get_tk_widget().pack(expand=True)

        # Scan start.
        for y_i in range(len(y_data)):
            for i in range(len(x_data)):
                if str(self.parent_app.widgets["interrupt_button"]['state']) == "disabled":
                    # If 'Interrupt' button is pressed, stop scan.
                    break
                
                x_i = 0
                # Change direction every column.
                if y_i % 2 == 0: # Even: scan in the forward direction.
                    x_i = i
                else: # Odd: scan in the backward direction.
                    x_i = -(i+1)

                # Coordinates.
                x = x_data[x_i]
                y = y_data[y_i]
                
                # Take measurement & record data.
                current_counts = self.takeMeasurement(x, y)
                self.widgets["counts"].config(text=str(current_counts))
                self.scan_data[x_i][y_i] = current_counts

                # Plot
                ax.clear()
                ax.imshow(self.scan_data, extent=[x_start, x_end, y_start, y_end], origin='lower', cmap='gray')
                canvas.get_tk_widget().delete()
                canvas.draw()
                canvas.get_tk_widget().pack(expand=True)
                
                # Update the UI... tkinter made me do it :/
                self.update()
                self.update_idletasks()

        print(self.scan_data)
        
        # Scan end.
        self.parent_app.interruptScanEvent()
        self.currently_scanning = False

    def onClosing(self):
        ##
        ## [Event Handler] CLOSES SCAN WINDOW & AJUSTS UI.
        ##
        if self.parent_app.isScanRunning() is False:
            # Only reset the start button if no other scans are running.
            self.parent_app.widgets["start_button"].configure(state="active")
            self.destroy()
    