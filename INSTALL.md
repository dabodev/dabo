Dabo Installation Notes
====================================

Prerequisites:
--------------
 * Python (we recommend 3.10 or later)
 * wxPython 4.2.2 or later
 * pymysql (only to run the MySQL-based demos or for your project)
 * reportlab (only to run reports)
 * PIL (only to run reports) (also known as Imaging or the Python Imaging Library)
   - the `Pillow` package is a PIL-compatible fork.

Installation:
-------------
It's best to use a modern tool such as [poetry](https://python-poetry.org/) or [uv](https://docs.astral.sh/uv/) to handle installation. The manual methods listed below were from the original Dabo release, and may or may not work today. But I'm including them in case they're helpful.

 * Windows: run ```win_setup.bat```
 * Mac or Linux: Execute the following shell command: ```sudo python setup.py install```

Having Problems Installing?
---------------------------
*This is also old advice!*

If you have trouble installing, and for whatever reason the ```setup.py``` doesn't work, just add a file named ```dabo.pth``` to your site-packages directory, with the path to dabo such as ```/home/pmcnett/projects/dabo```.

If you are on Linux and got the following error:
```
error: invalid Python installation: unable to open /usr/lib/python3.6/config/Makefile (No such file or directory)
```

and you really want to get setup.py to install dabo for you, you need to install the ```python-dev``` package. For instance (on Debian):

```
apt-get install python3.6-dev
```

(assuming you are running python3.6; change the version number as appropriate).

There are some problems with some of the third-party libraries like PIL when running in a mixed 32/64 bit environment, such as Mac OSX. While everything can be made to work running 64-bit versions of everything, if you are havingtrouble it may be worth trying to install 32-bit Python, wxPython, etc. Note: to run python in 32-bit on Mac, use ```python-32``` as the command instead of python.

