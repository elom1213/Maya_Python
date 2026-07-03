@echo off

cd /d %~dp0

pyinstaller ^
--noconfirm ^
--onefile ^
--windowed ^
--name A00210_FileManager ^
--icon "icon/A00210_FileManager.ico" ^
--paths "../../" ^
--paths "." ^
--collect-all PySide6 ^
--add-data "../../Framework/styles;Framework/styles" ^
--add-data "icon;icon" ^
launch.py

pause
