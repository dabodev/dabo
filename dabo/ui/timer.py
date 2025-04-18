# -*- coding: utf-8 -*-
from .. import events
from .. import ui
from ..localization import _
from . import dPanel
from . import dPemMixin
from . import makeDynamicProperty


class dTimer(dPemMixin):
    """Creates a timer, for causing something to happen at regular intervals."""

    def __init__(self, parent=None, properties=None, *args, **kwargs):
        self._baseClass = dTimer
        super().__init__(preClass=None, parent=parent, properties=properties, *args, **kwargs)

    def isRunning(self):
        return self.Enabled

    def start(self, interval=-1):
        if interval >= 0:
            self.Interval = interval
        self.Enabled = self.Interval > 0
        return self.Enabled

    def stop(self):
        self.Enabled = False

    def release(self):
        """Make sure that the timer is stopped first"""
        self.stop()
        super().release()

    # The following methods are not needed except for
    # compatibility with the various properties.
    def Show(self, val):
        pass

    def GetSize(self):
        return (-1, -1)

    def SetBestFittingSize(self, val):
        pass

    def GetParent(self):
        return None

    def Bind(self, *args, **kwargs):
        pass

    def Destroy(self):
        pass

    def _onTimerHit(self):
        if self.Enabled and self.Interval > 0:
            self.raiseEvent(events.Hit)
            ui.callAfterInterval(self.Interval, self._onTimerHit)

    # property definitions
    @property
    def Enabled(self):
        """
        Alternative means of starting/stopping the timer, or determining its status. If Enabled is
        set to True and the timer has a positive value for its Interval, the timer will be started.
        (bool)
        """
        return getattr(self, "_enabled", False)

    @Enabled.setter
    def Enabled(self, val):
        self._enabled = val
        if val:
            ui.callAfterInterval(self.Interval, self._onTimerHit)
        else:
            self._properties["Enabled"] = val

    @property
    def Interval(self):
        """Specifies the timer interval (milliseconds)."""
        try:
            v = self._interval
        except AttributeError:
            v = self._interval = 0
        return v

    @Interval.setter
    def Interval(self, val):
        self._interval = val

    DynamicEnabled = makeDynamicProperty(Enabled)
    DynamicInterval = makeDynamicProperty(Interval)


ui.dTimer = dTimer


class _dTimer_test(dPanel):
    def afterInit(self):
        # Only setting this so that the test Caption is correct
        self._baseClass = dTimer
        self.fastTimer = dTimer(self, Interval=500)
        self.fastTimer.bindEvent(events.Hit, self.onFastTimerHit)
        self.slowTimer = dTimer(Interval=2000)
        self.slowTimer.bindEvent(events.Hit, self.onSlowTimerHit)
        self.fastTimer.start()
        self.slowTimer.start()

    def onFastTimerHit(self, evt):
        print("fast timer fired!")

    def onSlowTimerHit(self, evt):
        print("slow timer fired!")


if __name__ == "__main__":
    from . import test

    test.Test().runTest(_dTimer_test)
