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


from nidaqmx.constants import Edge, CountDirection
import time


class PhotonCounter:
    read_task = None
    counter_channel = ""
    counter_terminal = ""

    def __init__(self, task, counter_channel, counter_terminal):
        self.read_task = task
        self.counter_channel = counter_channel
        self.counter_terminal = counter_terminal

        # Add channels to the read task.
        self.read_task.ci_channels.add_ci_count_edges_chan(
            self.counter_channel,
            initial_count=0,
            edge=Edge.RISING,
            count_direction=CountDirection.COUNT_UP,
        )
        self.read_task.ci_channels[0].ci_count_edges_term = self.counter_terminal

    def readCounts(self, integration_time=0, storage=[]):
        ##
        ## WAITS BY integration_time (s) THEN MEASURES COUNTS. RETURNS NUMBER OF COUNTS.
        ##
        if integration_time == 0:  # instantaneous reading.
            self.start()
            counts = self.read()
            storage.append(counts)
            self.stop()
            return counts
        else:
            self.start()
            target_time = time.perf_counter() + integration_time
            while time.perf_counter() < target_time:
                pass
            counts = self.read()
            storage.append(counts / integration_time)
            self.stop()
            return int(counts / integration_time)

    def start(self):
        self.read_task.start()

    def stop(self):
        self.read_task.stop()

    def read(self, storage=[]):
        c = self.read_task.read()
        storage.append(c)
        return c
