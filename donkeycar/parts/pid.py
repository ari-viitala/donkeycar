import datetime
import time
from collections import deque
import numpy as np

class PID(object):

    def __init__(self, p=0.01, i=0.00, d=-0.2):
        self.p = p
        self.d = d
        self.i = i

        self.history_length = 100

        self.derivation_time = 5

        self.history = np.zeros(self.history_length)

        self.throttle = 0.15

        zero = (0, 0, 0)
        self.state = {"a": zero, "v": zero, "x": zero}

    def run(self, target_speed, speed, training):
        
        if not speed:
            speed = target_speed

        if training:

            self.throttle = 0.15
            return 0, self.state
        
        error = target_speed - speed

        self.history = np.roll(self.history, 1)
        self.history[0] = error

        i_error = np.mean(self.history)
        d_error = np.mean(np.diff(self.history[:self.derivation_time]))

        adjustment = self.p * error + self.i * i_error + self.d * d_error

        print("Speed: {:.2f}, Throttle: {:.2f}, Error: {:2f}".format(speed, self.throttle, error))
        
        self.throttle += adjustment
        
        return self.throttle