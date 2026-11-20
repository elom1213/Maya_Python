# -*- coding: utf-8 -*-
# A00640_AttrSlider - version info
#
# 01.00  첫 버전 (계획서 docs/plans/A00640_AttrSlider_plan.md). 선택한 노드의 채널박스 어트리뷰트를 슬라이더로.
#        - 노드마다 섹션(+ 셰이프 · 히스토리의 blendShape, View 메뉴), blendShape = envelope + 타겟 웨이트
#        - float/int = 슬라이더 + 숫자 칸, bool = 체크박스, enum = 콤보. FBXASC 이름(노드 · 어트리뷰트 · 타겟 · enum 항목)을 풀어서
#        - 범위 = 사용자(어트리뷰트 이름 기준 저장) > 하드 양쪽 > 소프트 양쪽 > 최소만 > 자동, 행 우클릭 Set Range
#        - 상태 색 Keyed / Driven / Locked, Auto Key, 드래그 한 번 = undo 한 번, 선택 · 시간 · undo 따라 갱신, Lock List, Filter

VERSION = "01.00"
LAST_UPDATE = "2026-11-20"
