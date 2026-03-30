import time


class StopWatch:
    """This is a lightweight stopwatch for timing things."""

    ZERO_VALUE = 0.00

    def __init__(self, precision=4, *args, **kwargs):
        """These property setters will all define their underlying attribute"""
        self.Precision = precision
        self.Running = False
        self.StartTime = self.ZERO_VALUE
        self.Value = self.ZERO_VALUE

    def reset(self):
        """Reset the stopwatch timer."""
        self.stop()
        self._value = self.ZERO_VALUE

    def start(self):
        """Start the stopwatch if not started already."""
        if not self.Running:
            self.StartTime = time.time()
            self.Running = True

    def stop(self):
        """Stop the stopwatch if not stopped already."""
        if self.Running:
            self._running = False
            end = time.time()
            self._value += end - self.StartTime
            self.StartTime = 0.00

    @property
    def Precision(self):
        return self._precision

    @Precision.setter
    def Precision(self, val):
        if not isinstance(val, int):
            raise ValueError("Precision must be an integer")
        self._precision = val

    @property
    def Running(self):
        return self._running

    @Running.setter
    def Running(self, val):
        self._running = val

    @property
    def StartTime(self):
        return self._start_time

    @StartTime.setter
    def StartTime(self, val):
        self._start_time = val

    @property
    def Value(self):
        if self.Running:
            # need to add on the accumulated time.
            val = time.time() - self.StartTime
        else:
            val = self._value
        return round(val, self.Precision)

    @Value.setter
    def Value(self, val):
        self._value = val


if __name__ == "__main__":
    sw = StopWatch()
    print(sw.Running)
    print(sw.Value)
    print("-------1---------")
    sw.start()
    for i in range(100000):
        pass
    sw.stop()
    print(sw.Value, sw.Running)
    print("-------2---------")
    sw.start()
    for i in range(100):
        print(sw.Value, sw.Running)
    sw.reset()
    print(sw._running, sw._value, sw.StartTime)
    print(sw.Value, sw.Running)
    print("-------3---------")
    sw.start()
    for i in range(100):
        print(sw.Value, sw.Running)
    sw.stop()
    print(sw.Value)
