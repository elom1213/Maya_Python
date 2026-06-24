# Changelog — A00290_BSTool

## v01.00 (2026-06-24)
- 최초 버전. 레거시 `JUN_PY_BSTool_V01_01`(maya.cmds) 을 PySide(Qt) 로 재작성.
  `A00270_skinMigrate` 클론, green_dark 테마, Maya 메인 윈도우 parent.
- **탭 1 — Edit BS** (레거시 Edit BS 탭 이식. Connect BS 탭은 제외):
  - BlendShape 노드 리스트(씬 선택 연동, `JUN_mod_tsl_qt`).
  - `Key every target` — 각 타겟을 프레임 i 에서 1, i-1/i+1 에서 0 으로 키(타겟 순차 노출).
  - `Copy every target` — 위 키 후 프레임마다 베이스 메시를 복제해 타겟 모양을 타겟 이름의
    메시로 추출(visibility off) → `<node>_targets` 그룹.
- **탭 2 — Base Shape** (신규):
  - blendShape 노드를 지정하면 타겟 이름을 리스트업(`List Targets` / 선택에서 `<- Set`).
  - 선택 타겟의 **weight=Value 모양을 weight=1.0 기본 모양으로 재정의**.
    예) Value 0.5 → 타겟 절반, 1.3 → 과장. 내부적으로 타겟 포인트 델타를 Value 배 스케일
    (`inputTargetItem[*].inputPointsTarget`), in-between 아이템도 함께 스케일. 단일 undo 청크.
  - 저장된 포인트 델타가 없는(라이브 지오 입력) 타겟은 건너뛰고 로그에 안내.
