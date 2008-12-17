# Improved version of Tim Delaney's Python Cookbook recipe
# http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/286195

import new
import sys
import types

cdef int __super_modify_bytecode__
cdef int LOAD_CONST
cdef int LOAD_FAST
cdef int LOAD_ATTR
cdef int STORE_FAST
cdef int CALL_FUNCTION
cdef int STORE_GLOBAL
cdef int JUMP_FORWARD
cdef int JUMP_ABSOLUTE
cdef int CONTINUE_LOOP

try:
    # Try to get it from the python wrapper
    import __builtin__
    __super_modify_bytecode__ = __builtin__.__dict__['__super_modify_bytecode__']
except (ImportError, KeyError):
    # It wasn't there - we'll assume we can
    __super_modify_bytecode__ = 1

try:

    from opcode import opmap, HAVE_ARGUMENT, EXTENDED_ARG

    LOAD_CONST = opmap['LOAD_CONST']
    LOAD_FAST = opmap['LOAD_FAST']
    LOAD_ATTR = opmap['LOAD_ATTR']
    STORE_FAST = opmap['STORE_FAST']
    CALL_FUNCTION = opmap['CALL_FUNCTION']

    STORE_GLOBAL = opmap['STORE_GLOBAL']
    JUMP_FORWARD = opmap['JUMP_FORWARD']
    JUMP_ABSOLUTE = opmap['JUMP_ABSOLUTE']
    CONTINUE_LOOP = opmap['CONTINUE_LOOP']

    ABSOLUTE_TARGET = (JUMP_ABSOLUTE, CONTINUE_LOOP)
    ABORT_CODES = (EXTENDED_ARG, STORE_GLOBAL)

except ImportError:

    # Python 2.2 doesn't have opcode
    LOAD_CONST = 100
    LOAD_FAST = 124
    LOAD_ATTR = 105
    STORE_FAST = 125
    CALL_FUNCTION = 131
    STORE_GLOBAL = 97
    JUMP_FORWARD = 110
    JUMP_ABSOLUTE = 113
    CONTINUE_LOOP = 119
    HAVE_ARGUMENT = 90
    EXTENDED_ARG = 143

    ABSOLUTE_TARGET = (JUMP_ABSOLUTE, CONTINUE_LOOP)
    ABORT_CODES = (EXTENDED_ARG, STORE_GLOBAL)

# Python 2.2 doesn't have enumerate - so we'll use the same for all
cdef enumerate (sequence):
    return zip(range(len(sequence)), sequence)

# We split _super into an extension type for handling direct calls, and a subclass
# for handling attribute access. This allows the most common case -
# self.super(*p, **kw) - to be as fast as possible.
cdef class _super_base:

    cdef readonly object super
    cdef object method

    def __init__(self, klass, obj, name):
        self.super = super(klass, obj)

        try:
            self.method = getattr(self.super, name)
        except AttributeError:
            self.method = name

    def __call__(self, *p, **kw):
        # We want fastest performance in the normal case - i.e. calling
        # self.super(*p, **kw). We don't care as much about how long it
        # takes to fail.
        try:
            return self.method(*p, **kw)
        except TypeError:
            if type(self.method) is not str:
                raise

        # This should throw an AttributeError, but they could have modified
        # the base class
        self.method = getattr(self.super, self.method)
        return self.method(*p, **kw)

    def __setattr__(self, name, value):
        setattr(self.super, name, value)

# We want to make access to these as fast as possible.
_super_base_getattribute = _super_base.__getattribute__
_NO_SUPER_SUPER = TypeError("Cannot get 'super' object of 'super' object")
_getframe = sys._getframe
FunctionType = types.FunctionType
new_code = new.code

# We only need this to be a python class because __getattribute__ doesn't work
# with pyrex extension classes.
class _super (_super_base):

    try:
        # Fails in Python 2.2
        __name__ = 'super'
    except TypeError:
        pass

    def __getattribute__(self, name):
        if name == 'super':
            raise _NO_SUPER_SUPER

        super = _super_base_getattribute(self, 'super')
        return getattr(super, name)

cdef _bind_autosuper (func, klass):
    """
    Modifies the bytecode of the function so that a single call to _super() is
    performed first thing in the function call, then all accesses are via
    LOAD_FAST. Once this has been done for a function the MRO will not need to
    be trawled again.

    The function should be the underlying function of a method.

    Note: If the function does not call `self.super` then the bytecode will
    be unchanged.
    """

    # If it's already bound, don't try again
    try:
        func.__super_original_bytecode__
        return func
    except AttributeError:
        pass

    cdef int i
    cdef int sl_pos
    cdef int s_pos
    cdef int k_pos
    cdef int n_pos
    cdef int codelen
    cdef int opcode
    cdef int oparg
    cdef int need_setup

    func.__super_original_bytecode__ = func.func_code

    name = func.func_name
    co = func.func_code
    newcode = map(ord, co.co_code)
    codelen = len(newcode)
    newconsts = list(co.co_consts)
    sl_pos = len(co.co_varnames)
    newvarnames = co.co_varnames + (co.co_varnames[0] + '.super',)

    # Find the positions of `_super`, `klass` and `name`.
    # Normally these wouldn't be there, but it's possible they are.
    s_pos, k_pos, n_pos = -1, -1, -1

    for pos, v in enumerate(newconsts):
        if v is _super:
            s_pos = pos
        elif v is klass:
            k_pos = pos
        elif v == name:
            n_pos = pos

    if s_pos == -1:
        s_pos = len(newconsts)
        newconsts.append(_super)

    if k_pos == -1:
        k_pos = len(newconsts)
        newconsts.append(klass)

    if n_pos == -1:
        n_pos = len(newconsts)
        newconsts.append(name)

    # This goes at the start of the function. It is:
    #
    #   self.super = _super(klass, self, name)
    #
    # except of course `self.super` isn't a valid name -
    # but that is what will appear in the disassembly.
    setup_code = [
        LOAD_CONST, s_pos & 0xFF, s_pos >> 8,
        LOAD_CONST, k_pos & 0xFF, k_pos >> 8,
        LOAD_FAST, 0, 0,
        LOAD_CONST, n_pos & 0xFF, n_pos >> 8,
        CALL_FUNCTION, 3, 0,
        STORE_FAST, sl_pos & 0xFF, sl_pos >> 8,
    ]

    need_setup = 0
    i = 0

    while i < codelen:
        opcode = newcode[i]

        if opcode in ABORT_CODES:
            return func    # for simplicity, only optimize common cases

        # If we have a LOAD_FAST (0) followed by a LOAD_ATTR (super) then
        # it is `self.super`.
        elif opcode == LOAD_FAST:
            oparg = newcode[i+1] + (newcode[i+2] << 8)

            if oparg == 0:
                i = i + 3
                opcode = newcode[i]

                if opcode == LOAD_ATTR:
                    oparg = newcode[i+1] + (newcode[i+2] << 8)
                    attrname = co.co_names[oparg]

                    if attrname == 'super':
                        need_setup = 1
                        newcode[i-3:i] = [LOAD_FAST, sl_pos & 0xFF, sl_pos >> 8]
                        newcode[i:i+3] = [JUMP_FORWARD, 0 & 0xFF, 0 >> 8]

        # If the opcode is an absolute target it needs to be adjusted
        # to take into account the setup code.
        elif opcode in ABSOLUTE_TARGET:
            oparg = newcode[i+1] + (newcode[i+2] << 8) + len(setup_code)
            newcode[i+1] = oparg & 0xFF
            newcode[i+2] = oparg >> 8

        i = i + 1

        if opcode >= HAVE_ARGUMENT:
            i = i + 2

    # No changes needed - get out
    if not need_setup:
        return func

    # Our setup code will have 4 things on the stack
    cdef int co_stacksize
    co_stacksize = max(4, co.co_stacksize)

    # Conceptually, our setup code is on the `def` line.
    co_lnotab = map(ord, co.co_lnotab)

    if co_lnotab:
        co_lnotab[0] = co_lnotab[0] + len(setup_code)
    
    co_lnotab = ''.join(map(chr, co_lnotab))

    # Our code consists of the setup code and the modified code.
    codestr = ''.join(map(chr, setup_code + newcode))

    codeobj = new.code(co.co_argcount, len(newvarnames), co_stacksize,
                    co.co_flags, codestr, tuple(newconsts), co.co_names,
                    newvarnames, co.co_filename, co.co_name,
                    co.co_firstlineno, co_lnotab, co.co_freevars,
                    co.co_cellvars)

    func.func_code = codeobj
    return func

cdef _do_bind_autosuper_class (klass, attrs):
    """
    Modifies the bytecode of every method on the class that invokes `self.super`.
    """

    for a in vars(klass).values():
        if type(a) is types.FunctionType:
            try:
                # Check if it's already been bound
                a.__super_original_bytecode__
            except AttributeError:
                _bind_autosuper(a, klass)

    try:
        setattr(klass, '_%s__super_bound' % klass.__name__, True)
    except (TypeError, AttributeError):
        pass

cdef _bind_autosuper_class (klass):
    """
    Modifies the bytecode of every method on the class and base classes that
    invokes `self.super`.
    """

    for k in klass.__mro__:
        if (k is autosuper) or not issubclass(k, autosuper):
            continue

        attrs = vars(k)

        try:
            # So we don't pick up base class value if there's two classes
            # in the hierarchy that resolve to the same mangled names
            bound = attrs['_%s__super_bound' % k.__name__]
        except KeyError:
            bound = False

        if not bound:
            _do_bind_autosuper_class(k, attrs)

# This is the class we want to expose.
cdef class autosuper:

    def __init__(self, *p, **kw):
        """
        Modify the bytecode of the methods to improve performance.
        """
        if __super_modify_bytecode__:
            klass = type(self)
            attrs = vars(klass)

            try:
                # So we don't pick up base class value if there's two classes
                # in the hierarchy that resolve to the same mangled names
                bound = attrs['_%s__super_bound' % klass.__name__]
            except KeyError:
                bound = False

            if not bound:
                _bind_autosuper_class(klass)

        super(autosuper, self).__init__(*p, **kw)

    property super:
        """Gets the `super` object for the class of the currently-executing method."""

        def __get__(self):
            code = _getframe().f_code
            name = code.co_name

            # Find the method we're currently running by scanning the MRO and comparing
            # the code objects. When we find a match, that *might* be the class we're
            # currently in - however, we need to keep searching until we fail to find
            # a match. This is due to the way that methods are created - if you have
            #
            # class A (autosuper):
            #     def test (self):
            #         pass
            #
            # class B (A):
            #     pass
            #
            # then calling getattr(B, 'test') will return A.test, with no way to
            # determine that it's A.test. We only want to use this after calling 
            # getattr(A, 'test') otherwise we will determine the wrong class.

            cur_class = None
            m = None

            for c in type(self).__mro__:
                last_method = m

                try:
                    m = getattr(c, name)
                    func_code = m.func_code
                except AttributeError:
                    func_code = None

                match_code = (func_code is code)

                # It could have been bound in this execution of the function -
                # in which case the code object will no longer match up. So we
                # need to match against the original code object.
                if not match_code:
                    try:
                        match_code = (m.__super_original_bytecode__ is code)
                    except AttributeError:
                        pass

                if match_code:
                    cur_class = c
                elif cur_class is not None:
                    break

            if cur_class is None:
                # We could fail to find the class if we're called from a function
                # nested in a method
                raise TypeError("Can only call 'super' in a bound method")

            if __super_modify_bytecode__:
                _bind_autosuper(last_method.im_func, cur_class)

            return _super(cur_class, self, name)
