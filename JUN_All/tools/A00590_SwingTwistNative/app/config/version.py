# -*- coding: utf-8 -*-
# A00590_SwingTwistNative - version info
#
# 01.00  첫 버전 (계획서 docs/plans/A00590_SwingTwistNative_plan.md §8 v1 범위).
#        Build 탭: Start / End / Swing 조인트 + Twist 조인트 · 블렌드 표 + From End → MetaHuman
#        SwingTwistEvaluatorNode 를 대체하는 quatNodes 노드망 생성(원본 대비 오일러 ~1e-13°, 골든 시험).
#        Rigs 탭: 만든 망(홀더) 목록 · Select Holder / Nodes / Joints · Load to Build · Delete.
#        코어는 공용 Framework/core/maya_swing_twist.py. Convert(§9) · Container(§10) 는 다음 단계.
# 01.01  계획서 §9 Convert · §10 Container.
#        Convert 탭: 씬의 원본 SwingTwistEvaluatorNode 목록 → Convert Selected / All(노드마다 무작위 포즈로 원본과
#        수치 대조 후 원본 삭제, 블렌드 키 · 연결은 홀더로 옮김, 레퍼런스 노드는 거부) · Load / Unload Plugin.
#        Rigs 탭: Wrap / Unwrap(container, 블렌드 · 입출력을 원본 이름으로 공개) · Black Box · Restore Original(DNA export 용).
#        Build · Convert 의 Wrap in Container 기본 켬.

VERSION = "01.01"
LAST_UPDATE = "2026-11-13"
