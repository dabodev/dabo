# -*- coding: utf-8 -*-
import time

class StopWatch(object):
	"""This is a lightweight stopwatch for timing things."""

	def __init__(self, *args, **kwargs):
		super(StopWatch, self).__init__(*args, **kwargs)
		self.reset()

	def reset(self):
		"""Reset the stopwatch timer."""
		self.stop()
		self._value = 0.00

	def start(self):
		"""Start the stopwatch if not started already."""
		if not self.Running:
			self._beg = time.time()
			self._running = True

	def stop(self):
		"""Stop the stopwatch if not stopped already."""
		if self.Running:
			self._running = False
			end = time.time()
			self._value += (end - self._beg)
			self._beg = 0.00

	def _getRunning(self):
		try:
			v = self._running
		except AttributeError:
			v = self._running = False
		return v

	def _getValue(self):
		v = self._value

		if self.Running:
			# need to add on the accumulated time.
			end = time.time()
			v += (end - self._beg)
		return v

	Running = property(_getRunning)
	Value = property(_getValue)

if __name__ == "__main__":
	sw = StopWatch()
	print sw.Running
	print sw.Value
	print "-------1---------"
	sw.start()
	for i in range(100000):
		pass
	sw.stop()
	print sw.Value, sw.Running
	print "-------2---------"
	sw.start()
	for i in range(100):
		print sw.Value, sw.Running
	sw.reset()
	print sw._running, sw._value, sw._beg
	print sw.Value, sw.Running
	print "-------3---------"
	sw.start()
	for i in range(100):
		print sw.Value, sw.Running
	sw.stop()
	print sw.Value
