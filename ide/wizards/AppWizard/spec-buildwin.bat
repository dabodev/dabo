del /q dist
rmdir /s /q dist build

python -OO setup.py py2exe --bundle 1

copy c:\python26\lib\site-packages\wx-2.8-msw-unicode\wx\gdiplus.dll dist

rem  THE FOLLOWING LINE WILL FAIL, until you put msvcr90.dll inside a new win_todist folder
copy win_todist\msvcr90.dll dist


