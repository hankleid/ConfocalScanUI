##############################################################
##############################################################
###                                                        ###
###                                                        ###
###   Author: Hannah Calzi Kleidermacher                   ###
###   To report bugs, questions, comments, please email:   ###
###   kleid@stanford.edu                                   ###
###                                                        ###
###                                                        ###
##############################################################
##############################################################


class ScanningMirror():
    analog_task = None
    x_channel = ""
    y_channel = ""
    voltage_range = [] # Default range, but can be overwritten by the instantiation arguments.

    def __init__(self, task, x_channel, y_channel, V_range=[-10, 10]):
        self.analog_task = task
        self.x_channel = x_channel
        self.y_channel = y_channel
        self.voltage_range = V_range

        self.analog_task.ao_channels.add_ao_voltage_chan(self.x_channel)
        self.analog_task.ao_channels.add_ao_voltage_chan(self.y_channel)
    
    def start(self):
        self.analog_task.start()
    
    def stop(self):
        self.analog_task.stop()
    
    def getVoltageRange(self):
        ##
        ## RETURNS THE MIN AND MAX VOLTAGE VALUES.
        ##
        return self.voltage_range[0], self.voltage_range[1]

    def moveTo(self, x_voltage, y_voltage):
        self.analog_task.write([-x_voltage, y_voltage])