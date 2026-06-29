# A00270_skinMigrate

스킨 웨이트 이동/전이 PySide 툴. 레거시 `JUN_PY_move_skinWeightTool_v01_04` 을 이식해 **두 개의 탭**으로 구성한다.

- **Tab 1 "Classic"** — 레거시 원본 2버튼 UI. 단일 메시 내 본↔본 웨이트 이동, 메시↔메시 전이.
- **Tab 2 "Migrate A → B"** — 토폴로지가 다른 두 메시 사이 **Transfer + Move 를 한 번에**(통합 마이그레이션).

- **아키텍처**: (B) Standalone/Qt — PySide, Maya 내 실행 (`A00110_animTool` 클론)
- **버전**: `app/config/version.py`
- **설치**: `__dragDrop_A00270.py` 를 Maya 뷰포트로 드래그&드롭 → 셸프 버튼 생성 → `tools.A00270_skinMigrate.run(True)`

---

## Tab 1 — Classic (레거시 원본 2버튼)

레거시 `JUN_PY_move_skinWeightTool_v01_04` 의 UI 를 그대로 옮긴 탭. `From` / `To` 두 리스트(행 순서로 짝)와
Transfer Mode 콤보, 두 버튼으로 구성된다. 두 동작 모두 **Kangaroo Builder 플러그인**을 사용한다.

| 버튼 | 동작 |
|------|------|
| **Joints to Joints (single mesh)** | 현재 **선택한 메시** 위에서 `From-joint[i] → To-joint[i]` 로 스킨 웨이트 이동 (Kangaroo `moveSkinClusterWeights`, 현재 selection 기반). 실행 전 바인드된 메시를 씬에서 선택해 둘 것 |
| **Meshes to Meshes** | `From-mesh[i] → To-mesh[i]` 로 skinCluster 전이 (Kangaroo `transferSkinCluster`, Transfer Mode 적용, 인덱스 쌍 루프) |

> `From` / `To` 리스트는 버튼에 따라 **joints**(Joints to Joints) 또는 **meshes**(Meshes to Meshes)를 담는다.
> 두 리스트의 개수와 순서를 맞출 것.

---

## Tab 2 — Migrate A → B

토폴로지가 다른 두 리깅 메시 A, B 사이의 **스킨 웨이트 전이 + 본 재매핑**을 버튼 한 번으로 처리한다.
기존 수동 2단계(Kangaroo Builder의 skinCluster 탭 Transfer → Move)를 1-click 으로 단축한다.

### 무엇을 하나

메시 A 는 `[A_joint_01..]`, 메시 B 는 `[B_joint_01..]` 에 바인드된 상태에서:

1. **Transfer** — A 의 웨이트(+본)를 B 로 전이. B 가 A 의 본에 바인드된다.
2. **Move** — B 의 웨이트를 `A_joint_i → B_joint_i` 로 정확히 이동.
3. (옵션) weight 0 이 된 A 본을 B 에서 제거 → B 는 자신의 본만 남는다.

전체가 하나의 undo 청크로 묶인다.

### 입력

| 항목 | 설명 |
|------|------|
| **Source Mesh A** | 웨이트를 가져올 원본 메시(skinCluster 필요). `<- Set` 으로 선택에서 채움 |
| **Target Mesh B** | 웨이트를 받을 대상 메시 |
| **Joints A (From)** | A 의 본 리스트 |
| **Joints B (To)** | B 의 본 리스트 — **A 와 같은 순서**로. `A[i] → B[i]` 로 쌍을 이룬다 |

> Joints A/B 는 **행 순서(index)로 매핑**된다. 두 리스트의 개수와 순서를 반드시 맞출 것. (Up/Down 으로 정렬)

### 옵션

- **Engine**
  - `Kangaroo` (기본) — `kangarooTabTools.weights` 의 `transferSkinCluster` + `moveSkinClusterWeights` 체이닝. 수동 워크플로우와 **동일 결과**. Kangaroo Builder 플러그인이 로드되어 있어야 한다.
  - `Native` — `cmds.copySkinWeights` + `maya.api setWeights`. 플러그인 무의존. **Move 는 본 1:1 컬럼 이동**(per-vertex 최근접 본/스무딩 없음)이라 단순하며, setWeights 특성상 세밀한 Ctrl+Z 가 보장되지 않는다. 정밀 작업은 Kangaroo 권장.
- **Transfer Mode** — 전이 방식 (Vertex Index / Closest Vertex / **Closest Point**(기본) / Closest UV / Closest UV Point / Spikes). Native 는 UV/Spikes 를 근사 처리.
- **Remove unused influences** (기본 ON) — 이동 후 0 가중치가 된 A 본을 B 에서 제거.
- **Strict joint check** (기본 ON) — From 본이 실제로 A 에 바인드돼 있지 않으면 에러. 순서/오타 실수를 조기에 잡는다. 끄면 경고 후 진행.
- **Select result mesh** — 완료 후 B 를 선택.

## 구조

```
A00270_skinMigrate/
├── __init__.py / launch.py / __dragDrop_A00270.py
└── app/
    ├── config/version.py
    ├── core/skin_migrate_manager.py   # SkinMigrateManager — 엔진 추상화 + classic 동작
    └── ui/main_window.py              # PySide UI (QTabWidget: Classic / Migrate)
```

핵심 진입점 (`SkinMigrateManager`, 모두 `(count, msg)` 반환):

- `migrate(mesh_a, mesh_b, joints_a, joints_b, engine=..., transfer_mode=..., remove_unused=..., select_result=..., strict_joints=...)` — Tab 2 통합 마이그레이션.
- `move_joints_in_mesh(joints_from, joints_to)` — Tab 1 Joints to Joints (현재 선택 메시 기준).
- `transfer_meshes(meshes_from, meshes_to, transfer_mode=...)` — Tab 1 Meshes to Meshes.

Kangaroo 의존은 `_import_kangaroo()` 로 lazy import — 플러그인 미존재 시 안내 메시지를 반환한다.

## 참고

- 계획서: `A00270_skinMigrate_plan.md`
- 전신/참고: `A00020_move_skineWeightTool` (Transfer/Move 를 각각 호출하던 maya.cmds 툴)
