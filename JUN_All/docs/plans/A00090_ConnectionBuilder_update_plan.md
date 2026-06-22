# A00090_ConnectionBuilder 업데이트 계획서 (v01.03)

## 배경

기존 UI 는 Source/Target/BlendShape 를 각각 **단일 `QLineEdit`** 로 받아 1:1 연결만 가능했다.
실제 작업은 여러 노드를 한 번에 batch 연결해야 하고, BlendShape 직접 연결 경로는 현 워크플로
(solver→intermediate null 경유)에서 쓰지 않는다.

목표:
- 사용하지 않는 BlendShape 입력행 제거
- 용어 정리: **Base → Source**, **Driver → Target**
- Source/Target 을 `JUN_mod_tsl_qt_v01` 리스트 위젯으로 교체(여러 노드 입력, 좌·우 배치)
- **1→n(broadcast) / n→n(index pair)** 모드 체크박스로 batch 연결

용어 매핑(내부 식별자 의미 유지): Source = solver_node, Target = driver_node.

## 결정 사항

1. **BlendShape 제거 범위**: 하단 `BlendShape` 행만 제거. 상단 `Mesh for blendShape`(Create targets)·
   `BlendShapeManager` 는 유지(`create_blendshape` 는 `blendshape_node` 미참조라 안전).
2. **연결 모드**: 1→n = 첫 Source 를 모든 Target 에 broadcast / n→n = `Source[i]→Target[i]`(개수 동일 필요).
3. **n→n rule**: 콤보박스에서 선택한 단일 rule 의 mapping 을 모든 쌍에 동일 적용.

## 변경 파일

- `app/ui/main_window.py` — UI 재구성 + UI 측 batch 루프
- `app/config/version.py` — `01.02 → 01.03`, `LAST_UPDATE = 2026-06-22`
- core 파일 변경 없음 — 단일 rule 단위 로직을 UI 에서 짝별로 루프 호출하여 재사용

## 구현 요약

- **import**: `from Framework.qt.MOD_tsl_qt_v01 import JUN_mod_tsl_qt_v01` 추가.
- **UI**: `BlendShape` 행 제거. Source/Target 을 `JUN_mod_tsl_qt_v01` 두 개로 좌·우(`QHBoxLayout`) 배치.
  `Is Solver` 는 Source 컬럼 상단. Set/Del Attr 는 `add_button` 으로 각 리스트에 부착. 액션행 맨 앞에
  `cb_pair_mode = QCheckBox("n->n (index pair)")` 추가. `build_ui` 끝에서 모든 `QPushButton` 높이 축소.
- **`_build_pairs(sources, targets)`**: 모드에 따라 broadcast / index-pair 짝 리스트 생성(오류 시 `[]`+로그).
- **`get_rule(rule_name, solver_node, driver_node)`**: `blendshape_node=""` 고정. 짝별 호출.
- **핸들러**: `on_connect`(선택 rule×짝), `on_connect_all`(전체 rule×짝), `on_disconnect`/`on_validate`
  (선택 rule×짝). `is_solver` 는 connect 계열에 전달.
- **Set/Del Attr**: `create_attributes_for(tsl)` / `delete_attributes_for(tsl)` 가 리스트 전체 노드에
  `AttributeManager.create/delete` 적용(노드별 try/except 로그).

## 검증

Maya 내 실행(`tools.A00090_ConnectionBuilder.run(True)`):

1. 창 타이틀 `v01.03`, 하단 BlendShape 행 제거, Source/Target 리스트 좌·우 배치, `n->n (index pair)` 체크박스 확인.
2. RBF solver + driver null 준비 후:
   - **1→n**: 체크 해제, Source 1 / Target 여러개 → Connect → 다중 `Connected`, Validate `[OK]`, Disconnect 해제.
   - **n→n**: 체크, 개수 동일 → `Source[i]→Target[i]` 연결. 개수 불일치 시 `[ERROR]` 만.
3. Set/Del Attr 로 리스트 전체 노드 attr 생성/삭제.
4. 회귀: `Create targets`(Mesh), `Connect Intermediate` 기존대로 동작.
