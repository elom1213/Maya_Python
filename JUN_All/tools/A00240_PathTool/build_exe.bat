@echo off

cd /d %~dp0

pyinstaller ^
--noconfirm ^
--onefile ^
--windowed ^
--name A00240_PathTool ^
--icon "icon/A00240_PathTool.ico" ^
--paths "../../" ^
--paths "." ^
--collect-all PySide6 ^
--add-data "../../Framework/styles;Framework/styles" ^
--add-data "icon;icon" ^
launch.py

pause
