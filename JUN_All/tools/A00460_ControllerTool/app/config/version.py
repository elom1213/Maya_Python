# -*- coding: utf-8 -*-
# A00460_ControllerTool - version info
#
# 01.00  FK  - 리스트업한 조인트에 zro > con > ctl > tgt 계층 생성 + 조인트 컨스트레인트
#              (Bone Root / Bone Chain, zro·con·tgt 선택, parent/point/orient/scale 선택)

# 01.01  fix - undo_chunk() 인자 오류(TypeError) 수정 + 결과 select 를 chunk 안으로
#              옮겨 Ctrl+Z 한 번에 전부 되돌아가게

# 01.02  컨트롤러 모양을 원 -> **정육면체 테두리**로 (A00145_RigConnect Match 탭과 같은
#              CV 데이터). 큐브는 회전 대칭이라 Shape Axis 옵션 제거

VERSION = "01.02"
LAST_UPDATE = "2026-08-21"
