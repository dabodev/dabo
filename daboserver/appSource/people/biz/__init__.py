#!/usr/bin/env python
# -*- coding: utf-8 -*-
######
# In order for Dabo to 'see' classes in your biz directory, add an 
# import statement here for each class. E.g., if you have a file named
# 'MyClasses.py' in this directory, and it defines two classes named 'FirstClass'
# and 'SecondClass', add these lines:
# 
# from MyClass import FirstClass
# from MyClass import SecondClass
# 
# Now you can refer to these classes as: self.Application.biz.FirstClass and
# self.Application.biz.SecondClass
######

from People import PeopleBizobj
from Activities import ActivitiesBizobj
