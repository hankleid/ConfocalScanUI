import nidaqmx
import json
from SPCM import *
from MainApp import *

channels = json.load(open('HardwareConfig.json'))

with nidaqmx.Task() as SPCM_task:
    DAQ = {
        "SPCM": SPCM(SPCM_task,
                     channels["SPCM"]["counter_channel"],
                     channels["SPCM"]["counter_terminal"]),
        "FSM": None
    }
    app = MainApp(DAQ)
    app.mainloop()