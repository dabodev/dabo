import sys
import inspect
import dabo


class DoDefaultMixin(object):
	""" DEPRECATED: use self.super() instead
	
	An alternative way to call superclass method code.
	
	Mix this class in to your classes, and you can now use the following
	form to call superclass methods:
	
		retval = cls.doDefault([args])
	
	instead of the usual:
	
		retval = super(cls, self).<methodName>([args])
	"""

	def super(self,  *args, **kwargs):
		print "__"
		#print inspect.stack()[-1]
		#if len(inspect.stack()) < 20:
		#	for st in inspect.stack():
		#		print st
		#else:
		#	return
			
		frame = sys._getframe().f_back
		code = frame.f_code
		name = code.co_name

		foundSelf = False
		for c in type(self).__mro__:
			#print c
			if c is type(self):
				print "1"
				foundSelf = True
				continue
			try:
				m = getattr(c, name)
			except AttributeError:
				continue

			if m.func_code is code:
				print self, c, name
				s = super(c, self)
				return eval("super(c, self).%s(*args, **kwargs)" % name)
				
				break
				
				#return _super(super(c, self), name)


	def doDefault(cls, *args, **kwargs):
#		dabo.infoLog.write("Warning: doDefault is deprecated. Use self.super() instead.")
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
