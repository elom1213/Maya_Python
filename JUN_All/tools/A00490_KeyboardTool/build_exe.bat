@echo off

cd /d %~dp0

pyinstaller ^
--noconfirm ^
--onefile ^
--windowed ^
--name A00490_KeyboardTool ^
--icon "icon/A00490_KeyboardTool.ico" ^
--paths "../../" ^
--paths "." ^
--collect-all PySide6 ^
--add-data "../../Framework/styles;Framework/styles" ^
--add-data "icon;icon" ^
launch.py

pause
