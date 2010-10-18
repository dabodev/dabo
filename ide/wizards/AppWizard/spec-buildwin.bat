del /q dist
rmdir /s /q dist build

python -OO setup.py py2exe --bundle 1

copy c:\python26\lib\site-packages\wx-2.8-msw-unicode\wx\gdiplus.dll dist


rem  You either need to have your users install the Microsoft Visual Studio 9.0 Runtimes,
rem  which is apparently a free download and install from the Microsoft site, *or* you need
rem  to find and copy 3 DLL's and 1 manifest file into your distribution. The following 
rem  lines will fail if you haven't copied those files into a new win_todist\ directory.
rem  In my testing, running py2exe from Windows Vista, I don't need to distribute the 
rem  runtimes for installation on Vista or Windows7, but I must distribute them for
rem  installation on XP and earlier. In addition, these requirements will probably change
rem  with new versions of Python and wxPython. My current setup is Python 2.6.5, 
rem  and wxPython 2.8.11.0.

copy win_todist\msvcr90.dll dist
copy win_todist\msvcm90.dll dist
copy win_todist\msvcp90.dll dist
copy win_todist\Microsoft.VC90.CRT.manifest dist

rem Those 3 DLL's can be found in c:\Windows\WinSxS\x86_Microsoft.VC90.CRT_*\
rem The Manifest is c:\Windows\WinSxS\Manifests\x86_Microsoft.VC90.CRT_*.manifest
rem (note the *: the files can be named differently on your system here)

