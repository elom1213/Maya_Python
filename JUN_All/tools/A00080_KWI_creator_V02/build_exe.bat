@echo off

cd /d %~dp0

pyinstaller ^
--noconfirm ^
--onefile ^
--windowed ^
--paths "../../" ^
--collect-all PySide6 ^
--add-data "../../Framework/styles;Framework/styles" ^
launch.py

pause