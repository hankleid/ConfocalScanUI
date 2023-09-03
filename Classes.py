import os
import tkinter as tk
import tkinter.ttk as ttk
from tkinter.filedialog import askopenfilename, asksaveasfilename
#import images as im
from PIL import Image, ImageTk

class App(tk.Tk):
    widgets = {} # Grid --> frames --> widgets
    subwindows = []

    def __init__(self, title, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)
        self.title(title)
        self.generateControlMenu()

    def startScanEvent(self):
        ##
        ## [Event handler] STARTS SCAN.
        ##
        self.widgets["start_button"].config(state='disabled')
        self.widgets["interrupt_button"].config(state='active')

        print("start")
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

        frames = []

        # X voltage selection frame.
        frm_x = tk.Frame(
            master=self,
            relief=tk.RAISED,
            borderwidth=1
        )
        frames.append(frm_x)
        lbl_x = tk.Label(master=frm_x, text="x:", padx=5, pady=5)
        ent_x_start = tk.Entry(master=frm_x, width=5)
        ent_x_end = tk.Entry(master=frm_x, width=5)
        ent_x_start.insert(0, "-1")
        ent_x_end.insert(0, "1")
        self.widgets["x_start"] = ent_x_start
        self.widgets["x_end"] = ent_x_end
        lbl_x.pack(padx=5, pady=5, side=tk.LEFT)
        ent_x_start.pack(padx=5, pady=5, side=tk.LEFT)
        ent_x_end.pack(padx=5, pady=5, side=tk.LEFT)

        # Y voltage selection frame.
        frm_y = tk.Frame(
            master=self,
            relief=tk.RAISED,
            borderwidth=1
        )
        frames.append(frm_y)
        lbl_y = tk.Label(master=frm_y, text="y:", padx=5, pady=5)
        ent_y_start = tk.Entry(master=frm_y, width=5)
        ent_y_end = tk.Entry(master=frm_y, width=5)
        ent_y_start.insert(0, "-1")
        ent_y_end.insert(0, "1")
        self.widgets["y_start"] = ent_y_start
        self.widgets["y_end"] = ent_y_end
        lbl_y.pack(padx=5, pady=5, side=tk.LEFT)
        ent_y_start.pack(padx=5, pady=5, side=tk.LEFT)
        ent_y_end.pack(padx=5, pady=5, side=tk.LEFT)

        # Integration time frame
        frm_int = tk.Frame(
            master=self,
            relief=tk.RAISED,
            borderwidth=1
        )
        frames.append(frm_int)
        lbl_int = tk.Label(master=frm_int, text="integration time:", padx=5, pady=5)
        ent_int = tk.Entry(master=frm_int, width=5)
        ent_int.insert(0, "5")
        self.widgets["int_time"] = ent_int
        lbl_int.pack(padx=5, pady=5, side=tk.LEFT)
        ent_int.pack(padx=5, pady=5, side=tk.LEFT)

        # Start/Interrupt scan buttons frame.
        frm_buttons = tk.Frame(
            master=self,
            relief=tk.RAISED,
            borderwidth=1
        )
        frames.append(frm_buttons)
        btn_start = tk.Button(master=frm_buttons, text="Start Scan", command=self.startScanEvent)
        btn_interrupt = tk.Button(master=frm_buttons, text="Interrupt", command=self.interruptScanEvent)
        self.widgets["start_button"] = btn_start
        self.widgets["interrupt_button"] = btn_interrupt
        btn_start.pack(padx=5, pady=5, side=tk.LEFT)
        btn_interrupt.pack(padx=5, pady=5, side=tk.LEFT)

        # Add to grid (show).
        self.columnconfigure(0, minsize=300)
        self.rowconfigure([i for i in range(len(frames))], minsize=5)
        for i in range(len(frames)):
            frames[i].grid(column=0, row=i)

