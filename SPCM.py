import nidaqmx
from nidaqmx.constants import Edge, CountDirection
import time

class SPCM():
    read_task = None
    counter_channel = ""
    counter_terminal = ""

    def __init__(self, task, counter_channel, counter_terminal):
        self.read_task = task
        self.counter_channel = counter_channel
        self.counter_terminal = counter_terminal

        # Add channels to the read task.
        self.read_task.ci_channels.add_ci_count_edges_chan(self.counter_channel, 
                                        initial_count=0, 
                                        edge=Edge.RISING, 
                                        count_direction=CountDirection.COUNT_UP)
        self.read_task.ci_channels[0].ci_count_edges_term = self.counter_terminal

    def readCounts(self, integration_time=0):
        ##
        ## WAITS BY integration_time (s) THEN MEASURES COUNTS. RETURNS NUMBER OF COUNTS.
        ##
        if integration_time == 0: # instantaneous reading.
            self.read_task.start()
            counts = self.read_task.read()
            self.read_task.stop()
            return counts
        else:
            self.read_task.start()
            target_time = time.perf_counter() + integration_time
            while time.perf_counter() < target_time:
                pass
            counts = self.read_task.read()
            self.read_task.stop()
            return counts / integration_time