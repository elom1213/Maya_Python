# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-26
# Framework.jali - JALI 립싱크 공용 코어 (A00540_JaliLipSync 의 app/core 를 2026-10-26 에 승격)
#
#   lipsync_data : VisemeNet 결과 txt(+json) 읽기, wav 찾기 · 길이        (Maya 비의존)
#   mapping      : 매핑 json (모델 열 -> 리그 어트리뷰트), mappings/*.json  (Maya 비의존)
#   sequence     : 클립 여러 개를 한 타임라인에 놓기 · 합친 wav             (Maya 비의존)
#   keyer        : 리그에 키 걸기 / 지우기                                 (maya.cmds)
#   scene        : 리그 찾기 · 사운드 노드                                  (maya.cmds)
#   bake         : DUMMY_IN 키를 컨트롤러로 베이크 (JUN_JALI bake_ctl_keys 이식)  (maya.cmds)
#   clip_stamp   : 클립 .mb 의 fileInfo 도장 (A00560 · A00570)              (파싱은 순수 파이썬, 쓰기 · 읽기는 cmds)
#
# 쓰는 곳: A00540_JaliLipSync(재노출) · A00560_JaliBatch 워커 · A00570_JaliReview.
# maya.cmds 를 쓰는 모듈은 import 할 때 마야가 있어야 한다 - standalone(A00560 UI 프로세스)은 Maya 비의존 셋만 import 한다.
