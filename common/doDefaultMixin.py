_inspect = False

import sys

if _inspect:
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
		"""Call the superclass's method code, if any.

		Arguments are sent along to the super method, and the return value from 
		that super method is returned to the caller.

		Example:
			class A(dabo.ui.dForm):
				def afterInit(self):
					print "hi"
					return A.doDefault()

		Note that doDefault() must be called on the class, and not the self reference. 

		Also, due to the implementation, the calling class must use the 'self'
		convention - don't use 'this' or some other identifier for the class instance.
		"""

		if _inspect and "self.doDefault(" in inspect.stack()[1][4][0]:
			## I can't find a way, besides using the inspect.stack() call, to find
			## out if the caller is calling this on self (incorrect). I'm leaving
			## this code in because it works, but we can't run with it because it
			## is way too slow.
			raise TypeError("doDefault() must be called on the class, not on self.")
		
		frame = sys._getframe(1)
		self = frame.f_locals["self"]
		methodName = frame.f_code.co_name
		
		# If the super() class doesn't have the method attribute, we'll pass silently
		# because that is what the user will expect: they probably defined the method
		# but out of habit used the doDefault() call anyway.		
		method = cls.__getattribute__(cls, methodName)
		
		# Assert that the method object is actually a method
		if not _inspect or (
			method is not None and (
			inspect.ismethod(method) or inspect.isfunction(method))):
	
			return eval("super(cls, self).%s(*args, **kwargs)" % methodName)
	
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
