# -*- coding: utf-8 -*-
# A00600_SceneCleanup - version info
#
# 01.00  첫 버전 (계획서 docs/plans/A00600_SceneCleanup_plan.md). 체크한 항목대로 열린 씬 정리, undo 한 번.
#        항목: Display layers(defaultLayer 제외) · Animation layers(루트 BaseAnimation 까지 - Layer Editor 에 안 보이게)
#        · Unused nodes(Hypershade Delete Unused Nodes = MEL MLdeleteUnused). 창을 열 때 전부 체크.
#        정리 함수는 공용 Framework/core/maya_cleanup.py, 항목 = cleanup_items.ITEMS 에 클래스 하나씩.

VERSION = "01.00"
LAST_UPDATE = "2026-11-05"
