# -*- coding: utf-8 -*-
# A00050_uvTool_V02 - version info
#
# V01 (`A00050_uvTool`, maya.cmds UI) 에서 갈라져 나온 PySide 버전이다.
# 폴더가 V02 이므로 버전도 02.xx 로 센다 (A00110_animTool_V02 와 같은 규칙).
#
# 02.00  PySide 이식 + 로그 : Catch Objects 가 **어떤 메시가 왜** 규칙에 어긋나는지
#        한 줄씩 적고 그 메시를 씬에서 선택한다. Rename UV Set 은 이름이 **어떻게
#        바뀌었는지**(before -> after) 적고, 못 바꾼 것은 사유를 적는다

# 02.01  바꿀 UV 세트 이름을 **화면에서 입력**한다(기본 map1). 칸 하나가 Rename 의 목표
#        이름이자 Catch 의 규칙 이름이다 - 잡은 것을 고치면 규칙에 맞도록

# 02.02  리스트 옆에 **UV Sets 표**(Object / UV Sets / Rule) - A00330 Quick Rename > Insert 의
#        Preview 와 같은 형식. 리스트 · 이름 칸이 바뀔 때, Catch · Rename 뒤에 다시 그린다.
#        로그의 `[wrong_name]` 줄은 빨간색. 표는 app/ui/uv_set_table.py + 코어 inspect() -
#        A00380_MeshTool 로 옮길 때 그대로 가져간다

VERSION = "02.02"
LAST_UPDATE = "2026-09-23"
