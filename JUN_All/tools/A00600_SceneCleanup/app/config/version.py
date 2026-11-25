# -*- coding: utf-8 -*-
# A00600_SceneCleanup - version info
#
# 01.00  첫 버전 (계획서 docs/plans/A00600_SceneCleanup_plan.md). 체크한 항목대로 열린 씬 정리, undo 한 번.
#        항목: Display layers(defaultLayer 제외) · Animation layers(루트 BaseAnimation 까지 - Layer Editor 에 안 보이게)
#        · Unused nodes(Hypershade Delete Unused Nodes = MEL MLdeleteUnused). 창을 열 때 전부 체크.
#        정리 함수는 공용 Framework/core/maya_cleanup.py, 항목 = cleanup_items.ITEMS 에 클래스 하나씩.

# 01.01  항목 추가: Delete all namespaces - 네임스페이스 전부, 노드는 루트로 옮겨 남긴다(이름 겹치면 마야가 box1).
#        깊은 것부터 지운다(부모부터면 자식 네임스페이스가 루트로 올라와 남음 - 실측). 레퍼런스 네임스페이스와
#        그 부모는 남기고 경고(부모를 지우면 레퍼런스 네임스페이스가 옮겨짐 - 실측). Done 줄 "node(s)" 빼기.

VERSION = "01.01"
LAST_UPDATE = "2026-11-25"
