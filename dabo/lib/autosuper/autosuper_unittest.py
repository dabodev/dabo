# -*- coding: utf-8 -*-
# Improved version of Python Cookbook recipe
# http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/286195

#import psyco
#psyco.log()
#psyco.profile()

import sys
import time
import types
import unittest

RANGE = range(10)

autosuper_modules = []

# Make sure that it doesn't import the pyd
sys.modules['_autosuper'] = None
import autosuper as autosuper_py
autosuper_modules.append(autosuper_py)

try:
    # Now we want to import the pyd
    del sys.modules['_autosuper']
    import _autosuper as autosuper_pyd
    autosuper_modules.append(autosuper_pyd)
except ImportError:
    import traceback
    traceback.print_exc()
    pass

for autosuper in autosuper_modules:

    print autosuper.autosuper, autosuper

    # Classes for testing

    class A (autosuper.autosuper):

        def __init__ (self):
            increment_call('A.__init__')
            self.super()

        def test (self):
            increment_call('A.test')

        def test2 (self):
            increment_call('A.test2')

    class B (A):

        def __init__ (self):
            increment_call('B.__init__')
            self.super()

        def test (self):
            increment_call('B.test')
            self.super()

    class C (A):

        def __init__ (self):
            increment_call('C.__init__')
            self.super.__init__()

        def test (self):
            increment_call('C.test')
            self.super.test()

    class D (B, C):

        def __init__ (self):
            increment_call('D.__init__')
            self.super()

        def test (self):
            increment_call('D.test')
            self.super.test2()
            self.super()

        def test2 (self):
            increment_call('D.test2')
            self.super()

    class E (A):

        def __init__(self):
            def helper (super):
                super()

            increment_call('E.__init__')
            helper(self.super)

        def test (self):
            def helper (super):
                super()

            increment_call('E.test')
            helper(self.super)

    class F (A):

        def __init__(self):
            def helper (super):
                super.__init__()

            increment_call('F.__init__')
            helper(self.super)

        def test (self):
            def helper (super):
                super.test()

            increment_call('F.test')
            helper(self.super)

    class G (A):

        def __init__(self):
            def helper():
                self.super()

            increment_call('G.__init__')
            helper()

        def test (self):
            def helper():
                self.super()

            increment_call('G.test')
            helper()

    class H (A):

        def __init__(self):
            def helper():
                self.super.__init__()

            increment_call('H.__init__')
            helper()

        def test (self):
            def helper():
                self.super.test()

            increment_call('H.test')
            helper()

    class I (A):
        pass

    class J (A):
        def __getattr__(self, name):
            if name == 'test3':
                return self.test

            return A.__getattribute__(self, name)

    class Fail (autosuper.autosuper):

        def __init__(self):
            increment_call('Fail.__init__')
            self.__private = None

        def test (self):
            increment_call('Fail.test')
            print self.super()

    class Fail2 (Fail):

        def test (self):
            increment_call('Fail2.test')
            print self.super.__private

    class Fail3 (Fail2):

        def test (self):
            increment_call('Fail3.test')
            self.super.test = 1

    class Fail4 (Fail2):

        def test (self):
            increment_call('Fail4.test')
            print self.super.super

    # Test cases

    CALLS = {}

    def increment_call (name):
#        print name
        try:
            CALLS[name] += 1
        except :
            CALLS[name] = 1

    print

    class AutoSuperUnitTest (unittest.TestCase):

        def setUp (self):
#            print
            CALLS.clear()

        def test1 (self):
            A().test()

            assert CALLS['A.__init__'] == 1
            assert CALLS['A.test'] == 1
            assert len(CALLS) == 2

        def test2 (self):
            B().test()

            assert CALLS['B.__init__'] == 1
            assert CALLS['B.test'] == 1
            assert CALLS['A.__init__'] == 1
            assert CALLS['A.test'] == 1
            assert len(CALLS) == 4

        def test3 (self):
            C().test()

            assert CALLS['C.__init__'] == 1
            assert CALLS['C.test'] == 1
            assert CALLS['A.__init__'] == 1
            assert CALLS['A.test'] == 1
            assert len(CALLS) == 4

        def test4 (self):
            D().test()

            assert CALLS['D.__init__'] == 1
            assert CALLS['D.test'] == 1
            assert CALLS['B.__init__'] == 1
            assert CALLS['B.test'] == 1
            assert CALLS['C.__init__'] == 1
            assert CALLS['C.test'] == 1
            assert CALLS['A.__init__'] == 1
            assert CALLS['A.test'] == 1
            assert CALLS['A.test2'] == 1
            assert len(CALLS) == 9

        def test5 (self):
            E().test()

            assert CALLS['E.__init__'] == 1
            assert CALLS['E.test'] == 1
            assert CALLS['A.__init__'] == 1
            assert CALLS['A.test'] == 1
            assert len(CALLS) == 4

        def test6 (self):
            F().test()

            assert CALLS['F.__init__'] == 1
            assert CALLS['F.test'] == 1
            assert CALLS['A.__init__'] == 1
            assert CALLS['A.test'] == 1
            assert len(CALLS) == 4

##        def test7 (self):
##            G().test()
##
##            assert CALLS['G.__init__'] == 1
##            assert CALLS['G.test'] == 1
##            assert CALLS['A.__init__'] == 1
##            assert CALLS['A.test'] == 1
##            assert len(CALLS) == 4
##
##        def test8 (self):
##            H().test()
##
##            assert CALLS['H.__init__'] == 1
##            assert CALLS['H.test'] == 1
##            assert CALLS['A.__init__'] == 1
##            assert CALLS['A.test'] == 1
##            assert len(CALLS) == 4

        def test9 (self):
            try:
                Fail().test()
                self.fail()
            except AttributeError, e:
                assert "'super' object has no attribute 'test'" == str(e)

            assert CALLS['Fail.__init__'] == 1
            assert CALLS['Fail.test'] == 1
            assert len(CALLS) == 2

        def test10 (self):
            try:
                Fail2().test()
                self.fail()
            except AttributeError, e:
                assert "'super' object has no attribute '_Fail2__private'" == str(e)

            assert CALLS['Fail.__init__'] == 1
            assert CALLS['Fail2.test'] == 1
            assert len(CALLS) == 2

        def test11 (self):
            try:
                Fail3().test()
                self.fail()
            except AttributeError, e:
                assert "'super' object has no attribute 'test'" == str(e)

            assert CALLS['Fail.__init__'] == 1
            assert CALLS['Fail3.test'] == 1
            assert len(CALLS) == 2

        def test12 (self):
            try:
                Fail4().test()
                self.fail()
            except TypeError, e:
                assert "Cannot get 'super' object of 'super' object" == str(e)

            assert CALLS['Fail.__init__'] == 1
            assert CALLS['Fail4.test'] == 1
            assert len(CALLS) == 2

        def test13 (self):
            I().test()

            assert CALLS['A.__init__'] == 1
            assert CALLS['A.test'] == 1
            assert len(CALLS) == 2

        def test14 (self):
            J().test3()

            assert CALLS['A.__init__'] == 1
            assert CALLS['A.test'] == 1
            assert len(CALLS) == 2

    for i in range(2):
        try:
            unittest.main()
        except SystemExit:
            pass

    print

#sys.exit()

# super(cls, self)

class A1 (object):
    def __init__(self):
        pass

    def test (self):
        pass

class B1 (A1):
    def __init__(self):
        super(B1, self).__init__()

    def test (self):
        super(B1, self).test()

class C1 (A1):
    def __init__(self):
        super(C1, self).__init__()

    def test (self):
        super(C1, self).test()

class D1 (B1, C1):
    def __init__(self):
        super(D1, self).__init__()

    def test (self):
        super(D1, self).test()

class E1 (A1):
    def __init__(self):
        super(E1, self).__init__()

    def test (self, r=RANGE):
        for i in r:
            super(E1, self).test()

# self.__super

class A2 (object):
    def __init__(self):
        self.__super = super(A2, self)

    def test (self):
        pass

class B2 (A2):
    def __init__(self):
        self.__super = super(B2, self)
        self.__super.__init__()

    def test (self):
        self.__super.test()

class C2 (A2):
    def __init__(self):
        self.__super = super(C2, self)
        self.__super.__init__()

    def test (self):
        self.__super.test()

class D2 (B2, C2):
    def __init__(self):
        self.__super = super(D2, self)
        self.__super.__init__()

    def test (self):
        self.__super.test()

class E2 (A2):
    def __init__(self):
        self.__super = super(E2, self)
        self.__super.__init__()

    def test (self, r=RANGE):
        for i in r:
            self.__super.test()

r = 10000
r1 = range(min(10000, r))
r2 = range(r / len(r1))

base_elapsed = []
base_titles = [
    'super(cls, self)',
    'self.__super',
    'super(cls, self) (x%s)' % len(RANGE),
    'self.__super (x%s)' % len(RANGE)
]

for t in (D1, D2, E1, E2):

    t().test()

    start = time.clock()

    for i in r1:
        o = t()

        for j in r2:
            o.test()

    base_elapsed.append(time.clock() - start)

for t1, e1 in zip(base_titles, base_elapsed):
    print '%-28s %.7f' % (t1 + ':', e1,)

print

for autosuper in autosuper_modules:

    # self.super()

    class A3 (autosuper.autosuper):
        def __init__(self):
            pass

        def test (self):
            pass

    class B3 (A3):
        def __init__(self):
            self.super()

        def test (self):
            self.super()

    class C3 (A3):
        def __init__(self):
            self.super()

        def test (self):
            self.super()

    class D3 (B3, C3):
        def __init__(self):
            self.super()

        def test (self):
            self.super()

    class E3 (A3):
        def __init__(self):
            self.super()

        def test (self, r=RANGE):
            for i in r:
                self.super()

    class A4 (autosuper.autosuper):
        def __init__(self):
            pass

        def test (self):
            pass

    # self.super.attr()

    class B4 (A4):
        def __init__(self):
            self.super()

        def test (self):
            self.super.test()

    class C4 (A4):
        def __init__(self):
            self.super()

        def test (self):
            self.super.test()

    class D4 (B4, C4):
        def __init__(self):
            self.super()

        def test (self):
            self.super.test()

    class E4 (A4):
        def __init__(self):
            self.super()

        def test (self, r=RANGE):
            for i in r:
                self.super.test()

    elapsed = []
    titles = [
        'self.super()',
        'self.super.test()',
        'self.super() (x%s)' % len(RANGE),
        'self.super.test() (x%s)' % len(RANGE)
    ]

    for t in (D3, D4, E3, E4):

        t().test()

        start = time.clock()

        for i in r1:
            o = t()

            for j in r2:
                o.test()

        elapsed.append(time.clock() - start)

    print autosuper.autosuper, autosuper

    for t1, e1 in zip(titles[:2], elapsed[:2]):
        print
        print '%-28s %.7f' % (t1 + ':', e1,)

        for t2, e2 in zip(base_titles[:2], base_elapsed[:2]):
            print '    %-24s %.1fx' % (t2 + ':', e1 / e2)

    for t1, e1 in zip(titles[2:], elapsed[2:]):
        print
        print '%-28s %.7f' % (t1 + ':', e1,)

        for t2, e2 in zip(base_titles[2:], base_elapsed[2:]):
            print '    %-24s %.1fx' % (t2 + ':', e1 / e2)

    print
