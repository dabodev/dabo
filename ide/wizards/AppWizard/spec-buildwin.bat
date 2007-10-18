del /q dist
rmdir /s /q dist
python -OO setup.py py2exe --bundle 3

rem You may need to change these paths:
copy c:\python25\lib\site-packages\wx-2.8-msw-unicode\wx\MSVCP71.dll dist
copy c:\python25\lib\site-packages\wx-2.8-msw-unicode\wx\gdiplus.dll dist
copy c:\windows\system32\mfc71.dll dist

