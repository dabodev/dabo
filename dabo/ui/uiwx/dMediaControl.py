# -*- coding: utf-8 -*-
import wx
import wx.media
import dabo

from dabo.ui import makeDynamicProperty
if __name__ == "__main__":
	dabo.ui.loadUI("wx")

import dControlMixin as cm
# import dImageMixin as dim
import dabo.dEvents as dEvents
from dabo.dLocalize import _


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



class dMediaControl(cm.dControlMixin, wx.media.MediaCtrl):
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

		cm.dControlMixin.__init__(self, preClass, parent, properties=properties,
				attProperties=attProperties, *args, **kwargs)
		# Create lower-case method names to be consistent with Dabo
# 		self.play = self.Play
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
		print "LOAD"
		self.raiseEvent(dEvents.MediaLoaded, evt)
	def _onWxFinished(self, evt):
		print "FIN"
		self.raiseEvent(dEvents.MediaFinished, evt)
	def _onWxPause(self, evt):
		print "PAUS"
		self.raiseEvent(dEvents.MediaPause, evt)
	def _onWxPlay(self, evt):
		print "PLAY"
		self.raiseEvent(dEvents.MediaPlay, evt)
	def _onWxStateChanged(self, evt):
		print "CHHG"
		self.raiseEvent(dEvents.MediaStateChanged, evt)
	def _onWxStop(self, evt):
		print "STOP"
		self.raiseEvent(dEvents.MediaStop, evt)
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
		if dabo.ui.areYouSure(_("Could not load '%s'. Try again?") % val,
				title=_("Media Load Fail"), defaultNo=True,
				cancelButton=False):
			dabo.ui.setAfterInterval(500, self, "Source", val)
			return
		self._source = None
		self.clear()


	def _getContentDimensions(self):
		sc = self.ShowControls
		ret = self.GetBestSize().Get()
		self.ShowControls = sc
		return ret


	@_timeConvertOut
	def _getCurrentPosition(self):
		return self.Tell()

	@_timeConvertIn
	def _setCurrentPosition(self, val):
		if self._constructed():
			val = max(0, min(val, self.Length()))
			self.Seek(val)
		else:
			self._properties["CurrentPosition"] = val


	def _getDisplayDimensions(self):
		return self.GetBestSize().Get()


	@_timeConvertOut
	def _getDuration(self):
		return self.Length()


	def _getLoop(self):
		return self._loop

	def _setLoop(self, val):
		if self._constructed():
			self._loop = val
			self.unbindEvent(dEvents.MediaFinished)
			if val:
				self.bindEvent(dEvents.MediaFinished, self.__onLoop)
		else:
			self._properties["Loop"] = val


	def _getPlaybackRate(self):
		return self._playbackRate

	def _setPlaybackRate(self, val):
		if self._constructed():
			if not self.Status == "Playing":
				return
			self._playbackRate = val
			self.SetPlaybackRate(self._playbackRate / 100.0)
		else:
			self._properties["PlaybackRate"] = val


	def _getShowControls(self):
		return self._showControls

	def _setShowControls(self, val):
		if self._constructed():
			self._showControls = val
			self.ShowPlayerControls(val)
		else:
			self._properties["ShowControls"] = val


	def _getSource(self):
		return self._source

	def _setSource(self, val):
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


	def _getStatus(self):
		states = {0: "Stopped", 1: "Paused", 2: "Playing"}
		return states[self.GetState()]


	def _getTimeInSeconds(self):
		return self._timeInSeconds

	def _setTimeInSeconds(self, val):
		if self._constructed():
			self._timeInSeconds = val
		else:
			self._properties["TimeInSeconds"] = val


	def _getVolume(self):
		return int(self.GetVolume() * 100)

	def _setVolume(self, val):
		if self._constructed():
			self.SetVolume(val / 100.0)
		else:
			self._properties["Volume"] = val


	ContentDimensions = property(_getContentDimensions, None, None,
			_("""The native dimensions of the content, minus the player controls, if any.
			(read-only) (2-tuple of int)"""))

	CurrentPosition = property(_getCurrentPosition, _setCurrentPosition, None,
			_("""The current playback position of the content in either milliseconds (default)
			or seconds, depending on the setting of TimeInSeconds.  (int or float)"""))

	DisplayDimensions = property(_getDisplayDimensions, None, None,
			_("""The native dimensions of the content and the player controls, if any.
			When ShowControls is False, or when audio content is loaded, this is identical
			to ContentDimensions. (read-only) (2-tuple of int)"""))

	Duration = property(_getDuration, None, None,
			_("""Duration of the content in either milliseconds (default) or seconds, depending
			on the value of TimeInSeconds.  (read-only) (int or float)"""))

	Loop = property(_getLoop, _setLoop, None,
			_("""Controls whether the content stops when it reaches the end (False; default),
			or whether it restarts at the beginning (True).  (bool)"""))

	PlaybackRate = property(_getPlaybackRate, _setPlaybackRate, None,
			_("""Controls the speed at which the content is played. A rate of 100 (default)
			plays at normal speed; a rate of 200 would play back at double speed; 50 at
			half-speed, etc. Note that this has undefined behavior when the content is not
			playing: it can either do nothing, or can start the content playing immediately.
			Once the content stops, though, this value does not persist.  (int)"""))

	ShowControls = property(_getShowControls, _setShowControls, None,
			_("""Determines if the player controls are visible. Note that the specific controls
			that are shown with the control depends on the platform and the type of content.
			Default=True.  (bool)"""))

	Source = property(_getSource, _setSource, None,
			_("""This can be either a file path or a URI for the content displayed in this
			control. If the value begins with 'http', it is assumed to be a URI rather than
			a local file path. Setting the source to None will clear the control.  (str)"""))

	Status = property(_getStatus, None, None,
			_("""The current playback status. One of 'Playing', 'Paused', or 'Stopped'.
			(read-only) (str)"""))

	TimeInSeconds = property(_getTimeInSeconds, _setTimeInSeconds, None,
			_("""Determines whether we specify content length and position in
			seconds (default), or milliseconds. Affects the Duration and
			CurrentPosition properties. Default=True  (bool)"""))

	Volume = property(_getVolume, _setVolume, None,
			_("""Controls the sound level. 100 (default) is full volume; 0 turns the
			sound off.  (int)"""))



if __name__ == "__main__":
	from dabo.dApp import dApp
	class MediaForm(dabo.ui.dForm):
		def afterInit(self):
			# Here's a sample movie URI; you can change this to something local on
			# your machine, or another URI.
			#uri = "/Users/ed/Downloads/roc.mov"
			uri = "http://c0097282.cdn.cloudfiles.rackspacecloud.com/how_to_fold_a_shirt.mpg"
			if self.Application.Platform == "Win":
				backend = wx.media.MEDIABACKEND_WMP10
			else:
				backend = ""
			self.player = dMediaControl(self, Source=uri, Loop=False, OnMediaLoaded=self.onMediaLoaded,
					szBackend=backend)
			# Change this to fill the form
			show_native_size = True
			if show_native_size:
				self.Sizer.append(self.player)
			else:
				self.Sizer.append1x(self.player)

		def onMediaLoaded(self, evt):
			print "MediaLoaded"


	app = dApp(MainFormClass=MediaForm)
	app.start()
