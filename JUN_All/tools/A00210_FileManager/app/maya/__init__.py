# -*- coding: utf-8 -*-
# A00210_FileManager / Maya 탭 - 마야 파일(씬 파일 자체)을 다루는 탭. 이 폴더가 통째로 분리 단위다:
# 폴더 밖을 가리키는 import 는 Framework 와 A00210 prefs(mayapy 경로 저장)뿐이고 안에서는 상대 import 만 쓴다.
# 나중에 독립 툴로 뗄 때는 app/maya 를 새 툴의 app 으로 복사하고 launch.py · main_window.py 만 새로 쓴다.
# A00210 은 마야 밖 standalone 이라 maya.cmds 가 필요한 일은 core/maya_worker.py 를 mayapy 로 띄워 한다.
# (설계: docs/plans/A00210_FileManager_maya_reference_plan.md)
