Dabo: A Framework for developing data-driven business applications
==================================================================

Dabo is for developing multi-platform database business applications - you
know, applications that need to connect to a database like MySQL, Oracle,
MS-SQL, PostgreSQL, or SQLite, get recordsets of data based on criteria set by
the user, provide easy ways to edit and commit changes to the data, and to
report on the data.

You program in Python, subclassing Dabo's base classes. In addition, there are
several graphical tools for laying out your GUI, editing your menus, and
creating professional business reports. 

Dabo has three main subpackages, representing the three tiers common in modern
database application design:
```
	dabo.db  : database
	dabo.biz : business objects
	dabo.ui  : user interface
```
```dabo.db``` and ```dabo.biz``` are completely ui-free, while ```dabo.ui```
requires wxPython.

To distribute your application to end users
-------------------------------------------
Use PyInstaller or cxFreeze to make an executable package to deploy to Mac,
Windows, and Linux clients. Or, make sure your end users have Python, wxPython,
etc. installed and distribute your source code.

To run Dabo, and apps based on Dabo, you need:
----------------------------------------------
 * Python 3.6 or later
 * wxPython 4.0 or later
 * Reportlab and Python Imaging Library if running reports.
 * One or more of the following operating systems:
   * Windows XP or higher
   * Macintosh OSX 10.5 or higher
   * Linux 2.6 or higher with X11 running and Gtk2

How you get started is pretty much up to you. There are two related projects: `dabo_demo`, which
contains demonstrtion code for the various Dabo classes, and `dabo_`ide`, which contains tools for
creating Dabo applications visually. Please note that the `dabo_ide` tools worked great when they
were written in the mid-2000s, but have not been fully updated to the modern Python tools.

For some quick results for the impatient, once you've installed Dabo using the
standard ```python setup.py install``` method, do this from your Python
interpreter:

```python
from dabo.dApp import dApp
dApp().start()
```

press Ctrl+D and type the following into the command window that appears:

```python
tb = dabo.ui.dTextBox(self)
```

Notice the textbox in the upper left hand corner?
```python
tb.Value = "yippee!"
tb.FontBold = True
print tb.Value
```

Now, use the ui to change the value in the textbox, and switch back to
the command window.
```python
print tb.Value
```

https://dabodev.com

https://github.com/dabodev/dabo
