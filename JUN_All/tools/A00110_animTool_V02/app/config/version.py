# Anim Key Tool
# 02.22  Pin 켜짐(Pinned) = 연한 빨강 - 공용 Framework/qt/pin_style (A00240_PathTool 과 같은 색).

# 02.23  Follow 탭 `Point` 체크박스 - Maintain Offset 의 위치를 pointConstraint 처럼(target 이 돌아도 공전 안 함).
#        끄면 예전 그대로 parentConstraint 처럼. Maintain Offset + Translate 일 때만 켤 수 있다.

# 02.24  Follow 탭 `Maintain Offset` 기본 켜짐(예전엔 꺼짐).

# 02.25  View > Graph Focus `Layer curves` 콤보 - 애니메이션 레이어가 있을 때 그래프 에디터의 레이어 필터
#        (View > Animation Layer Filter)를 Selected / Active / Active+Selected / All 로 걸고, 세로(Fit value)
#        맞춤도 **그 필터로 보이는 커브만** 잰다. 예전엔 `keyframe -q -name` 이 활성 레이어 커브만 돌려줘
#        Layer1 선택 시 ±200 에 맞추는데 화면엔 베이스 ±400 도 겹쳐 보였다. 기본 Selected(없으면 활성 → 전부),
#        `Keep` 은 GE 설정을 건드리지 않고 그대로 따른다. 레이어 없는 씬은 영향 없음.

VERSION = "02.25"
LAST_UPDATE = "2026-10-29"
