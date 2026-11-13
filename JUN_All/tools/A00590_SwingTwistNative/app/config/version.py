# -*- coding: utf-8 -*-
# A00590_SwingTwistNative - version info
#
# 01.00  첫 버전 (계획서 docs/plans/A00590_SwingTwistNative_plan.md §8 v1 범위).
#        Build 탭: Start / End / Swing 조인트 + Twist 조인트 · 블렌드 표 + From End → MetaHuman
#        SwingTwistEvaluatorNode 를 대체하는 quatNodes 노드망 생성(원본 대비 오일러 ~1e-13°, 골든 시험).
#        Rigs 탭: 만든 망(홀더) 목록 · Select Holder / Nodes / Joints · Load to Build · Delete.
#        코어는 공용 Framework/core/maya_swing_twist.py. Convert(§9) · Container(§10) 는 다음 단계.

VERSION = "01.00"
LAST_UPDATE = "2026-11-13"
