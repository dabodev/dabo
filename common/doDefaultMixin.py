import sys
import inspect


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

		# If the super() class doesn't have the method attribute, we'll pass silently
		# because that is what the user will expect: they probably defined the method
		# but out of habit used the doDefault() call anyway.		
		method = cls.__getattribute__(cls, methodName)
		
		# Assert that the method object is actually a method
		if method is not None and (inspect.ismethod(method) or inspect.isfunction(method)):
			return eval('super(cls, self).%s(*args, **kwargs)' % methodName)
	
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
