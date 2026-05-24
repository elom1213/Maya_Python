@echo off

pyinstaller ^
--noconfirm ^
--onefile ^
--windowed ^
--collect-all PySide6 ^
--add-data "Framework/styles;styles" ^
launch.py

pause