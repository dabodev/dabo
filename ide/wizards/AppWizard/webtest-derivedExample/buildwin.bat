del /q dist
rmdir /s /q dist
python -OO setup.py py2exe --bundle 1

rem pkm: in the future I may share my LiveUpdater software, but for now
rem this is commented out.
rem copy ..\liveupdater\dist\LiveUpdater.exe dist
