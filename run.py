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


import nidaqmx
import json
from PhotonCounter import *
from ScanningMirror import *
from MainApp import *

channels = json.load(open('HardwareConfig.json'))

with nidaqmx.Task() as photon_counter_task, nidaqmx.Task() as scanning_mirror_task:
    DAQ = {
        "Photon Counter": PhotonCounter(photon_counter_task,
                            channels["Photon Counter"]["counter_channel"],
                            channels["Photon Counter"]["counter_terminal"]),
        "Scanning Mirror": ScanningMirror(scanning_mirror_task,
                            channels["Scanning Mirror"]["x_channel"],
                            channels["Scanning Mirror"]["y_channel"],
                            channels["Scanning Mirror"]["V_range"])
    }

    scanning_mirror = DAQ["Scanning Mirror"]
    scanning_mirror.start()

    app = MainApp(DAQ)
    app.mainloop()
    
    scanning_mirror.stop()