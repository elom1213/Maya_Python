# Changelog — Control Rig Tool

## 01.00 (2026-06-10)
- `01_Modules/JUN_PY_ControlRigTool_V01_07.py` (maya.cmds 단일 파일, 1922줄)를
  현행 프레임워크 규약에 맞춰 모듈화 / 리펙토링.
- maya.cmds UI → PySide(Qt) UI (`Framework.qt.qt` 추상화).
- 로직(`app/core`)과 UI(`app/ui`) 분리. 모든 씬 조작은 `MayaScene` 어댑터 경유.
- 매칭/IK 알고리즘은 동작 동등하게 이식. 정리 사항:
  - `solver is "ikRPsolver"` 등 `is` 문자열 비교 → `==` 교정.
  - 상태 메시지 오타 `State : Sucess` → `State : Success`.
  - 전역 `JUN_cage_glo` → `MainWindow` 인스턴스 속성으로 캡슐화.
  - 미사용 `import maya.mel` 제거.

### 이력 (원본 V01_07 기준)
- v01.03 : deleting joints for matching cage objects, fix joint orientation (leg, spine)
- v01.04 : set pole vector on helper joints, set wrist controllers orientation to 0 in world space
- v01.05 : match pole vector object to correct place, set distance to option controller
- v01.06 : pose objects matching, fingers zro node matching
- v01.07 : set pole object expected direction (leg to z+, arm to z-)
