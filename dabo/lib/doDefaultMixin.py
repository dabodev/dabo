# -*- coding: utf-8 -*-
import inspect
import warnings

deprecation_warnings_issued = []


class DoDefaultMixin(object):
	"""
	An alternative way to call superclass method code.

	Mix this class in to your classes, and you can now use the following
	form to call superclass methods::

		retval = cls.doDefault([args])

	instead of the usual::

		retval = super(cls, self).<methodName>([args])
	
	"""

	def doDefault(cls, *args, **kwargs):
		"""
		DEPRECATED in r7036: use python's explicit super(cls, self).method(<args>)

		Call the superclass's method code, if any.

		Arguments are sent along to the super method, and the return value from
		that super method is returned to the caller.

		Example::
			
			class A(dabo.ui.dForm):
				def afterInit(self):
					print "hi"
					return A.doDefault()

		Note that doDefault() must be called on the class, and not the self reference.

		Also, due to the implementation, the calling class must use the 'self'
		convention - don't use 'this' or some other identifier for the class instance.
		"""

		frame = inspect.currentframe(1)
		self = frame.f_locals["self"]
		methodName = frame.f_code.co_name

		if (cls, methodName) not in deprecation_warnings_issued:
			warnings.warn("""
  doDefault() deprecated since r7036. Please replace your doDefault() call with:
    super(%s, self).%s(<args>)""" % (cls.__name__, methodName), DeprecationWarning, 2)
			deprecation_warnings_issued.append((cls, methodName))

		# If the super() class doesn't have the method attribute, we'll pass silently
		# because that is what the user will expect: they probably defined the method
		# in their code but out of habit used the doDefault() call anyway.
		method = getattr(super(cls, self), methodName, None)

		# Assert that the method object is actually a method
		if inspect.ismethod(method):
			return method(*args, **kwargs)

	doDefault = classmethod(doDefault)


if __name__ == '__main__':
	class TestBase(list, DoDefaultMixin):
		# No myMethod here
		pass

	class MyTest1(TestBase):
		def myMethod(self):
			print "MyTest1.myMethod called."
			MyTest1.doDefault()

	class MyTest2(MyTest1): pass

	class MyTest(MyTest2):
		def myMethod(self):
			print "MyTest.myMethod called."
			MyTest.doDefault()

	print "Test 1: simple test:"
	t = MyTest()
	t.myMethod()

	print "\nTest 2: diamond inheritence test:"

	class A(DoDefaultMixin):
		def meth(self, arg):
			print self.__class__
			arg.append("A")

	class B(A):
		def meth(self, arg):
			print self.__class__
			arg.append("B")
			B.doDefault(arg)

	class C(A):
		def meth(self, arg):
			print self.__class__
			arg.append("C")
			C.doDefault(arg)

	class D(B,C):
		def meth(self, arg):
			print self.__class__
			arg.append("D")
			D.doDefault(arg)

	t = D()
	testList = []
	t.meth(testList)
	print testList

