# -*- coding: utf-8 -*-
import wx
import wx.media

from .. import events
from .. import ui
from ..localization import _
from . import dControlMixin
from . import makeDynamicProperty


def _timeConvertOut(fn):
    """
    Takes millisecond values returned by wx and converts them to
    fractional seconds if the current setting of TimeInSeconds is True.
    """

    def wrapper(instance):
        ret = fn(instance)
        if instance.TimeInSeconds:
            ret = ret / 1000.0
        return ret

    return wrapper


def _timeConvertIn(fn):
    """
    Takes values set by the program and converts them to milliseconds
    if the current setting of TimeInSeconds is True.
    """

    def wrapper(instance, val):
        if instance.TimeInSeconds:
            val = int(val * 1000)
        fn(instance, val)

    return wrapper


class dMediaControl(dControlMixin, wx.media.MediaCtrl):
    """Wraps the wx MediaCtrl to display video and audio content."""

    def __init__(self, parent, properties=None, attProperties=None, *args, **kwargs):
        self._baseClass = dMediaControl
        preClass = wx.media.MediaCtrl
        self._loop = False
        self._source = None
        self._timeInSeconds = True
        self._playbackRate = 100
        self._showControls = self._extractKey((properties, kwargs), "ShowControls", True)
        kwargs["ShowControls"] = self._showControls
        dropHandler = self._extractKey((properties, kwargs), "DroppedFileHandler", self)
        kwargs["DroppedFileHandler"] = dropHandler

        dControlMixin.__init__(
            self,
            preClass,
            parent,
            properties=properties,
            attProperties=attProperties,
            *args,
            **kwargs,
        )
        # Create lower-case method names to be consistent with Dabo
        #         self.play = self.Play
        self.pause = self.Pause
        self.stop = self.Stop

    def play(self, rate=None):
        """
        Plays the content. By default, the content is played forward at normal
        speed. You can optionally pass a playback rate which will be applied
        to the content. To start the playback in reverse mode, pass in -100.
        """
        self.Play()
        if rate is not None:
            self.PlaybackRate = rate

    def moveToPct(self, pct):
        """
        Moves the CurrentPosition to the specified percentage of the content's
        Duration. E.g., passing 50 moves to the middle; 75 to 3/4 of the way through.
        Negative values measure from the end; e.g., -10 will set the CurrentPosition
        to 90% through the content.
        """
        if not -100 <= pct <= 100:
            raise ValueError(_("Cannot set percentages greater than 100."))
        if pct < 0:
            pct = 100 + pct
        self.CurrentPosition = self.Duration * (pct / 100.0)

    def moveByPct(self, pct):
        """
        Moves the CurrentPosition by the specified percentage of the content.
        Negative values move backward.
        """
        fulltime = self.Duration
        change = (pct / 100.0) * fulltime
        newpos = self.CurrentPosition + change
        self.CurrentPosition = max(0, min(newpos, fulltime))

    def processDroppedFiles(self, filelist):
        """
        Load the dropped file into the control. Only one file can be
        the source, so if by chance more than one file was dropped,
        only use the first.
        """
        self.Source = filelist[0]

    def _initEvents(self):
        self.Bind(wx.media.EVT_MEDIA_LOADED, self._onWxLoaded)
        self.Bind(wx.media.EVT_MEDIA_FINISHED, self._onWxFinished)
        self.Bind(wx.media.EVT_MEDIA_PAUSE, self._onWxPause)
        self.Bind(wx.media.EVT_MEDIA_PLAY, self._onWxPlay)
        self.Bind(wx.media.EVT_MEDIA_STATECHANGED, self._onWxStateChanged)
        self.Bind(wx.media.EVT_MEDIA_STOP, self._onWxStop)

    #### Start event methods ####
    # Note: I've left the debug print statements to help determine when these
    # events are actually raised. I've noticed that clicking the player controls
    # does not seem to cause these events to fire.
    def _onWxLoaded(self, evt):
        self.scale()
        print("LOAD")
        self.raiseEvent(events.MediaLoaded, evt)

    def _onWxFinished(self, evt):
        print("FIN")
        self.raiseEvent(events.MediaFinished, evt)

    def _onWxPause(self, evt):
        print("PAUS")
        self.raiseEvent(events.MediaPause, evt)

    def _onWxPlay(self, evt):
        print("PLAY")
        self.raiseEvent(events.MediaPlay, evt)

    def _onWxStateChanged(self, evt):
        print("CHHG")
        self.raiseEvent(events.MediaStateChanged, evt)

    def _onWxStop(self, evt):
        print("STOP")
        self.raiseEvent(events.MediaStop, evt)

    #### End event methods ####

    def scale(self, prop=1.0):
        """
        Size the control to the video's native size. By default, the size is scaled
        to the video's native size, but you can optionally pass a proportion to
        enlarge or reduce the size.
        """
        w, h = self.GetBestSize().Get()
        self.Size = (w * prop, h * prop)

    def reverse(self):
        """
        Reverses the direction of the playing content stream. Has no effect if the
        content is not playing.
        """
        if not self.Status == "Playing":
            return
        # Since the internal attribute '_playbackRate' can get out of sync with the actual
        # rate if the video is stopped or paused, always grab the current value.
        self.PlaybackRate = -100 * self.GetPlaybackRate()

    def __onLoop(self, evt):
        """Handler for when the content finishes playing, and self.Loop = True."""
        self.play()

    def handleLoadFailure(self, val):
        """
        This method contains the default behavior when an attempt to load
        content into the control by setting the Source property fails. If you want
        your app to handle things differently, override this method.
        """
        if ui.areYouSure(
            _("Could not load '%s'. Try again?") % val,
            title=_("Media Load Fail"),
            defaultNo=True,
            cancelButton=False,
        ):
            ui.setAfterInterval(500, self, "Source", val)
            return
        self._source = None
        self.clear()

    # Property definitions
    @property
    def ContentDimensions(self):
        """
        The native dimensions of the content, minus the player controls, if any.  (read-only)
        (2-tuple of int)
        """
        sc = self.ShowControls
        ret = self.GetBestSize().Get()
        self.ShowControls = sc
        return ret

    @property
    @_timeConvertOut
    def CurrentPosition(self):
        """
        The current playback position of the content in either milliseconds (default) or seconds,
        depending on the setting of TimeInSeconds.  (int or float)
        """
        return self.Tell()

    @CurrentPosition.setter
    @_timeConvertIn
    def CurrentPosition(self, val):
        if self._constructed():
            val = max(0, min(val, self.Length()))
            self.Seek(val)
        else:
            self._properties["CurrentPosition"] = val

    @property
    def DisplayDimensions(self):
        """
        The native dimensions of the content and the player controls, if any.  When ShowControls is
        False, or when audio content is loaded, this is identical to ContentDimensions. (read-only)
        (2-tuple of int)
        """
        return self.GetBestSize().Get()

    @property
    @_timeConvertOut
    def Duration(self):
        """
        Duration of the content in either milliseconds (default) or seconds, depending on the value
        of TimeInSeconds.  (read-only) (int or float)
        """
        return self.Length()

    @property
    def Loop(self):
        """
        Controls whether the content stops when it reaches the end (False; default), or whether it
        restarts at the beginning (True).  (bool)
        """
        return self._loop

    @Loop.setter
    def Loop(self, val):
        if self._constructed():
            self._loop = val
            self.unbindEvent(events.MediaFinished)
            if val:
                self.bindEvent(events.MediaFinished, self.__onLoop)
        else:
            self._properties["Loop"] = val

    @property
    def PlaybackRate(self):
        """
        Controls the speed at which the content is played. A rate of 100 (default) plays at normal
        speed; a rate of 200 would play back at double speed; 50 at half-speed, etc. Note that this
        has undefined behavior when the content is not playing: it can either do nothing, or can
        start the content playing immediately. Once the content stops, though, this value does not
        persist.  (int)
        """
        return self._playbackRate

    @PlaybackRate.setter
    def PlaybackRate(self, val):
        if self._constructed():
            if not self.Status == "Playing":
                return
            self._playbackRate = val
            self.SetPlaybackRate(self._playbackRate / 100.0)
        else:
            self._properties["PlaybackRate"] = val

    @property
    def ShowControls(self):
        """
        Determines if the player controls are visible. Note that the specific controls that are
        shown with the control depends on the platform and the type of content.  Default=True.
        (bool)
        """
        return self._showControls

    @ShowControls.setter
    def ShowControls(self, val):
        if self._constructed():
            self._showControls = val
            self.ShowPlayerControls(val)
        else:
            self._properties["ShowControls"] = val

    @property
    def Source(self):
        """
        This can be either a file path or a URI for the content displayed in this control. If the
        value begins with 'http', it is assumed to be a URI rather than a local file path. Setting
        the source to None will clear the control.  (str)
        """
        return self._source

    @Source.setter
    def Source(self, val):
        if self._constructed():
            if val is None:
                self.Load("")
                self.clear()
                return
            if val.startswith("http:"):
                success = self.LoadURI(val)
            else:
                success = self.Load(val)
            if success:
                self._source = val
            else:
                self.handleLoadFailure(val)
        else:
            self._properties["Source"] = val

    @property
    def Status(self):
        """
        The current playback status. One of 'Playing', 'Paused', or 'Stopped'.  (read-only) (str)
        """
        states = {0: "Stopped", 1: "Paused", 2: "Playing"}
        return states[self.GetState()]

    @property
    def TimeInSeconds(self):
        """
        Determines whether we specify content length and position in seconds (default), or
        milliseconds. Affects the Duration and CurrentPosition properties. Default=True  (bool)
        """
        return self._timeInSeconds

    @TimeInSeconds.setter
    def TimeInSeconds(self, val):
        if self._constructed():
            self._timeInSeconds = val
        else:
            self._properties["TimeInSeconds"] = val

    @property
    def Volume(self):
        """
        Controls the sound level. 100 (default) is full volume; 0 turns the sound off.  (int)
        """
        return int(self.GetVolume() * 100)

    @Volume.setter
    def Volume(self, val):
        if self._constructed():
            self.SetVolume(val / 100.0)
        else:
            self._properties["Volume"] = val


ui.dMediaControl = dMediaControl


if __name__ == "__main__":
    from ..application import dApp
    from ..ui import dForm

    class MediaForm(dForm):
        def afterInit(self):
            # Here's a sample movie URI; you can change this to something local on
            # your machine, or another URI.
            uri = "/home/johnf/Downloads/gettysburg10.wav"
            # uri = "http://c0097282.cdn.cloudfiles.rackspacecloud.com/how_to_fold_a_shirt.mpg"
            if self.Application.Platform == "Win":
                backend = wx.media.MEDIABACKEND_WMP10
            else:
                backend = ""
            self.player = dMediaControl(
                self,
                Source=uri,
                Loop=False,
                OnMediaLoaded=self.onMediaLoaded,
                szBackend=backend,
            )
            # Change this to fill the form
            show_native_size = True
            if show_native_size:
                self.Sizer.append(self.player)
            else:
                self.Sizer.append1x(self.player)

        def onMediaLoaded(self, evt):
            print("MediaLoaded")

    app = dApp(MainFormClass=MediaForm)
    app.start()
