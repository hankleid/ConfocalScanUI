import tkinter as tk
from ScanWindow import *


class MainApp(tk.Tk):
    widgets = {} # Grid --> frames --> widgets
    subwindow = None

    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)
        self.title("Control Menu")
        self.generateControlMenu() # Grid is generated in this method

    def disableWidgetInputs(self):
        ##
        ## Disables all widgets in the control menu to user input.
        ##
        self.widgets["start_button"].config(state='disabled')
        self.widgets["interrupt_button"].config(state='disabled')
        self.widgets["custom_json_button"].config(state='disabled')
        self.widgets["custom_loop_button"].config(state='disabled')
        self.widgets["x_start"].config(state='readonly')
        self.widgets["x_end"].config(state='readonly')
        self.widgets["x_step"].config(state='readonly')
        self.widgets["y_start"].config(state='readonly')
        self.widgets["y_end"].config(state='readonly')
        self.widgets["y_step"].config(state='readonly')
        self.widgets["int_time"].config(state='readonly')
    
    def enableWidgetInputs(self):
        ##
        ## Enables all widgets in the control menu to user input.
        ##
        self.widgets["start_button"].config(state='normal')
        self.widgets["interrupt_button"].config(state='normal')
        self.widgets["custom_json_button"].config(state='normal')
        self.widgets["custom_loop_button"].config(state='normal')
        self.widgets["x_start"].config(state='normal')
        self.widgets["x_end"].config(state='normal')
        self.widgets["x_step"].config(state='normal')
        self.widgets["y_start"].config(state='normal')
        self.widgets["y_end"].config(state='normal')
        self.widgets["y_step"].config(state='normal')
        self.widgets["int_time"].config(state='normal')

    def startScanEvent(self):
        ##
        ## [Event handler] STARTS SCAN.
        ##
        self.disableWidgetInputs()
        self.widgets["interrupt_button"].config(state="normal")

        print("start")
        if self.subwindow is not None:
            self.subwindow.destroy()
        self.subwindow = ScanWindow(self)
        self.subwindow.takeScan()
    
    def interruptScanEvent(self):
        ##
        ## [Event handler] INTERRUPTS SCAN.
        ##
        self.enableWidgetInputs()
        self.widgets["interrupt_button"].config(state="disabled")
        self.widgets["custom_loop_button"].config(state="disabled")
        print("interrupt")
    
    def uploadJsonEvent(self):
        self.widgets["custom_loop_button"].config(state="normal")

    def startCustomLoopEvent(self):
        self.widgets["start_button"].config(state="disabled")
        self.widgets["interrupt_button"].config(state="normal")
        self.widgets["custom_loop_button"].config(state="disabled")
        example = {
            'x_coords': [-0.5, -0.25, 0, 0.25, 0.5],
            'y_coords': [-0.5, -0.25, 0, 0.25, 0.5]
        }
        self.subwindow.goCustomCoords(example["x_coords"], example["y_coords"])
        self.widgets["interrupt_button"].config(state="disabled")
        self.widgets["start_button"].config(state="normal")
        self.widgets["custom_loop_button"].config(state="normal")

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
        ent_x_step.insert(0, "0.1")
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
        ent_y_step.insert(0, "0.1")
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

        # Custom coordinates frame.
        frm_customcoords = tk.Frame(
            master=self,
            relief=tk.RAISED,
            borderwidth=1
        )
        widget_frames.append(frm_customcoords)
        lbl_customcoords = tk.Label(master=frm_customcoords, text="custom coordinates:", padx=1, pady=1)
        btn_uploadjson = tk.Button(master=frm_customcoords, text="Upload .json", state="disabled", command=self.uploadJsonEvent)
        btn_gocustom = tk.Button(master=frm_customcoords, text="Start Loop", state="disabled", command=self.startCustomLoopEvent)
        lbl_jsonfilename = tk.Label(master=frm_customcoords, text="", fg="blue", padx=1, pady=1)
        self.widgets["custom_json_button"] = btn_uploadjson
        self.widgets["custom_loop_button"] = btn_gocustom
        self.widgets["custom_coords_path"] = lbl_jsonfilename
        lbl_customcoords.pack(padx=1, pady=1)
        btn_uploadjson.pack(padx=1, pady=1)
        btn_gocustom.pack(padx=1, pady=1)
        lbl_jsonfilename.pack(padx=1, pady=1)

        # Add to grid (show).
        self.columnconfigure(0, minsize=300)
        self.rowconfigure([i for i in range(len(widget_frames))], minsize=5)
        for i in range(len(widget_frames)):
            widget_frames[i].grid(column=0, row=i)
