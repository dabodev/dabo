import sys


class DoDefaultMixin(object):
	""" An alternative way to call superclass method code.
	
	Mix this class in to your classes, and you can now use the following
	form to call superclass methods:
	
		retval = cls.doDefault([args])
	
	instead of the usual:
	
		retval = super(cls, self).<methodName>([args])
	"""

	def doDefault(cls, *args, **kwargs):
		frame = sys._getframe(1)
		self = frame.f_locals['self']
		methodName = frame.f_code.co_name
		try:
			return eval('super(cls, self).%s(*args, **kwargs)' % methodName)
		except AttributeError:
			# The super() class didn't have the method attribute. Pass silently -
			# at this time I believe this to be the correct behavior, because the
			# user doesn't want to keep track of where a given method was defined
			# and whether or not to call doDefault(), they just want to call
			# doDefault() and have it work if it needs to work.
			pass
	doDefault = classmethod(doDefault)

	
if __name__ == '__main__':
	class TestBase(list, DoDefaultMixin):
		def MyMethod(self):
			print "TestBase.MyMethod called."
			
	class MyTest(TestBase):
		def MyMethod(self):
			print "MyTest.MyMethod called."
			MyTest.doDefault()
			
	t = MyTest()
	t.MyMethod()
