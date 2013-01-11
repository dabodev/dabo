Dabo Installation Notes
====================================

Prerequisites:
--------------
 * Python (we recommend 2.7.3 (Python3 not supported in wxPython yet)
 * wxPython UNICODE BUILD (we recommend the latest, currently 2.8.12.1)
 * MySQLdb (only to run the demos or for your project)
 * reportlab (only to run reports)
 * PIL (only to run reports) (also known as Imaging or the Python Imaging Library)

Installation:
-------------
 * Windows: run ```win_setup.bat```
 * Mac or Linux: Execute the following shell command: ```sudo python setup.py install```

Demo and IDE:
-------------
There are two other directories in the same folder as this file: ```demo``` and ```ide```. They contain useful programs (written in Dabo, of course!) to help you explore and develop with Dabo. You should move these to a convenient folder on your system, such as ```My Documents\Dabo``` on Windows, or ```~/dabo``` on Linux or Mac.

The ```demo``` folder contains the *DaboDemo* application, which shows off a lot of the user interface classes available for subclassing. 

The ```ide``` folder contains our visual tools, such as the *Class Designer*, which you can use to visually design your UI; the *Connection Editor*, which is used to create connections to database servers, the *Report Designer* to create professional PDF reports, as well as several other useful visual tools.

Having Problems Installing?
---------------------------
If you have trouble installing, and for whatever reason the ```setup.py``` doesn't work, just add a file named ```dabo.pth``` to your site-packages directory, with the path to dabo such as ```/home/pmcnett/projects/dabo```.

If you are on Linux and got the following error:
```
error: invalid Python installation: unable to open /usr/lib/python2.6/config/Makefile (No such file or directory)
```

and you really want to get setup.py to install dabo for you, you need to install the ```python-dev``` package. For instance (on Debian):

```
apt-get install python2.6-dev
```

(assuming you are running python2.6; change the version number as appropriate).

There are some problems with some of the third-party libraries like PIL when running in a mixed 32/64 bit environment, such as Mac OSX. While everything can be made to work running 64-bit versions of everything, if you are havingtrouble it may be worth trying to install 32-bit Python, wxPython, etc. Note: to run python in 32-bit on Mac, use ```python-32``` as the command instead of python.

