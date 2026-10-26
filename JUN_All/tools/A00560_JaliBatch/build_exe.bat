@echo off

cd /d %~dp0

pyinstaller ^
--noconfirm ^
--onefile ^
--windowed ^
--name A00560_JaliBatch ^
--icon "icon/A00560_JaliBatch.ico" ^
--paths "../../" ^
--paths "." ^
--collect-all PySide6 ^
--add-data "../../Framework/styles;Framework/styles" ^
--add-data "app/maya;tools/A00560_JaliBatch/app/maya" ^
--add-data "../../Framework/jali;Framework/jali" ^
--add-data "../../Framework/core;Framework/core" ^
--add-data "icon;icon" ^
launch.py

pause
