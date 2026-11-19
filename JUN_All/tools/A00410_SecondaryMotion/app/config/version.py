# Secondary Motion Tool
# 01.12  Solver: Kawaii / Physics Asset - 언리얼 Physics Asset 흉내. 체인 루트만 애니메이션, 나머지는 중력 · 관성 ·
#        감쇠 · Swing1/2 한계로만(자식 회전 키 무시). Start From animation / Settled, Collision None / Ground.
#        core physics_solver (순수 파이썬). 시험 core 18 · maya 15 · UI 18.
# 01.13  Physics Asset 이 처음에 크게 튀던 것 수정 - FTL 길이 구속이 에너지를 만들어 냈다(놓은 체인의 흔들림 에너지
#        52~139배, 팁이 루트 위로). DFTL 속도 보정(s = 1.0). Substeps 를 올리면 덜 감쇠(수렴). 시험 core 23.
VERSION = "01.13"
LAST_UPDATE = "2026-11-19"
