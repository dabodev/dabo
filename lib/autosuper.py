# Improved autosuper by Tim Delaney
# http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/286195

import sys

class _super (object):
    """
    Wrapper for the super object.

    If called, a base class method of the same name as the current method
    will be called. Otherwise, attributes will be accessed.
    """

    __name__ = 'super'

    # We want the lowest overhead possible - both speed and memory
    __slots__ = ('__super', '__method')

    def __init__(self, super, name):
        object.__setattr__(self, '_super__super', super)

        try:
            object.__setattr__(self, '_super__method', getattr(super, name))
        except AttributeError:
            object.__setattr__(self, '_super__method', name)

    def __call__(self, *p, **kw):
        """
        Calls the base class method with the passed parameters.
        """

        # We want fastest performance in the normal case - i.e. calling
        # self.super(*p, **kw). We don't care as much about how long it
        # takes to fail.
        method = object.__getattribute__(self, '_super__method')

        try:
            return method(*p, **kw)
        except TypeError:
            if type(method) is not str:
                raise

        # This should throw an AttributeError, but they could have modified
        # the base class
        super = object.__getattribute__(self, '_super__super')
        method = getattr(super, method)
        object.__setattr__(self, '_super__method', method)
        return method(*p, **kw)

    def __getattribute__ (self, name):
        """
        Gets a base class attribute.
        """

        super = object.__getattribute__(self, '_super__super')

        try:
            return getattr(super, name)
        except AttributeError:
            # Cannot call like self.super.super - produces inconsistent results.
            if name == 'super':
                raise TypeError("Cannot get 'super' object of 'super' object")
            else:
                raise

    def __setattr__(self, name, value):
        """
        All we want to do here is make it look the same as if we called
        setattr() on a real `super` object.
        """
        super = object.__getattribute__(self, '_super__super')
        object.__setattr__(super, name, value)

def _getSuper (self):
    """
    Gets the `super` object for the class of the currently-executing method.
    """
    frame = sys._getframe().f_back
    code = frame.f_code
    name = code.co_name

    # Find the method we're currently running by scanning the MRO and comparing
    # the code objects - when we find a match, that's the class whose method
    # we're currently executing.

    for c in type(self).__mro__:
        try:
            m = getattr(c, name)
        except AttributeError:
            continue

        if m.func_code is code:
            return _super(super(c, self), name)

    # We could fail to find the class if we're called from a function
    # nested in a method
    raise TypeError, "Can only call 'super' in a bound method"

class autosuper (object):
    """
    Automatically determine the correct super object and use it.
    """

    # We want the lowest overhead possible - both speed and memory
    __slots__ = ()

    super = property(fget=_getSuper,
                     doc=_getSuper.__doc__.strip())


if __name__=="__main__":
	class A(autosuper):
		def fun1(self):
			print "A"
			self.super()   ## TypeError

	class B(A):
		def fun1(self):
			print "B"
			self.super()

	class C(B): pass    ## recursion

	# class C(B):
	#	def fun1(self):
	#		print "C"
	#		self.super()
	t = C()
	t.fun1()
