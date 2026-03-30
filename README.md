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

Dabo has three main subpackages, representing the three tiers common in database application design:

```
	dabo.db  : database
	dabo.biz : business objects
	dabo.ui  : user interface
```

```dabo.db``` and ```dabo.biz``` are completely ui-free, while ```dabo.ui``` requires wxPython.

To run Dabo, and apps based on Dabo, you need:
----------------------------------------------
 * Python 3.10 or later
 * wxPython 4.0 or later
 * Reportlab and Python Imaging Library if running reports.
 * Linux, MacOS, or Windows operating system.

If you are working on the Dabo codebase, you can clone the git repo from here:

`git clone git@github.com:dabodev/dabo.git`

 
How you get started is pretty much up to you. There are two related projects: `dabo_demo`, which
contains demonstration code for the various Dabo classes, and `dabo_ide`, which contains tools for
creating Dabo applications visually. Please note that the `dabo_ide` tools worked great when they
were written in the mid-2000s, and have largely been updated to work with modern Python. They are still a work in progress, though, so please post an issue on the [Dabo IDE Issues page](https://github.com/dabodev/dabo_ide/issues) in GitHub.

For some quick results for the impatient, once you've installed Dabo using the
standard ```uv add dabo``` or ```poetry install dabo``` method, do this from your Python
interpreter:

```python
from dabo.application import dApp
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
print(tb.Value)
```

Now, use the ui to change the value in the textbox, and switch back to
the command window.
```python
print(tb.Value)
```

You can even place it wherever you wish:

```python
tb.Left = 123
tb.Top = 99
```

When you type those lines, the textbox moves to the specified location.

For more information:

[Dabo Website](https://dabodev.com)

[Dabo Repo on GitHub](https://github.com/dabodev/dabo)
