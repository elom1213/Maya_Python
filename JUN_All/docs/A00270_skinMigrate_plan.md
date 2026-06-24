# A00270_skinMigrate — 작업 계획서

> **목적**: 외형은 비슷하지만 토폴로지가 다른 두 리깅 메시 사이에서
> "메시 A 웨이트 → 메시 B 전이(Transfer)" + "본 A[] → 본 B[] 웨이트 이동(Move)" 을
> **버튼 한 번**으로 처리한다. 기존 수동 2단계(Kangaroo Transfer → Move)를 1-click 으로 단축.

- **Author**: Ji Hun Park (Junny)
- **상태**: ✅ 구현 완료 (2026-06-24, v01.00) — 가이드 문서 [A00270_skinMigrate.md](A00270_skinMigrate.md) 참고
- **작성일**: 2026-06-24
- **툴 번호**: `A00270_skinMigrate` (현재 최신 `A00260` 다음)
- **아키텍처**: (B) Standalone/Qt — **PySide**, `A00110_animTool` 클론 (Maya 내 PySide)
- **UI 언어**: 영어 전용(주석·docstring 만 한국어 허용)

---

## 1. 배경 — 현재 수동 워크플로우

토폴로지가 다른 리깅된 메시 A, B 가 있다.
- A 는 `[A_joint_01, A_joint_02, A_joint_03]` 에 바인드
- B 는 `[B_joint_01, B_joint_02, B_joint_03]` 에 바인드

수동 과정(Kangaroo Builder, skinCluster 탭):

| 단계 | 동작 | 결과 |
|------|------|------|
| 1. **Transfer** | From=메시 A 지정 → B 선택 → Transfer | A·B 모두 `[A_joint_01..03]` 에 바인드 (B 가 A 의 본/웨이트를 받음) |
| 2. **Move** | From=`[A_joint_01..03]`, To=`[B_joint_01..03]` 지정 → Move | B 의 웨이트가 A 본 → B 본 으로 정확히 이동 |

**원하는 것**: 위 1→2 를 한 버튼으로. 입력은 (메시 A, 메시 B, 본 A 리스트, 본 B 리스트) 를 **정확한 순서**로 지정.

---

## 2. 기술 분석 (조사 완료)

### 2-1. Kangaroo 실제 함수 = 당신이 누르는 버튼 그 자체
경로: `C:\Users\USER\Desktop\JP\0020_maya_plugin\0010_kangaroo\scripts\kangarooTabTools\weights.py`

- **Transfer 버튼** = `transferSkinCluster(...)` (`weights.py:1821`)
  ```python
  import kangarooTabTools.weights as ktw
  from kangarooTabTools.weights import TransferMode
  ktw.transferSkinCluster(
      _pSelection=['meshB'],        # 타겟(없으면 현재 선택)
      sFrom=['meshA'],              # From 칸
      iMode=TransferMode.closestPoint,   # 0~5 전이 모드
      bAutoCreateNewSkinCluster=True,    # B 에 A 와 같은 본으로 새 skinCluster 생성
      fBlend=1.0)
  ```
- **Move 버튼** = `moveSkinClusterWeights(...)` (`weights.py:2772`)
  ```python
  ktw.moveSkinClusterWeights(
      _pSelection=['meshB'],
      xJoints={'A_joint_01':'B_joint_01',
               'A_joint_02':'B_joint_02',
               'A_joint_03':'B_joint_03'},   # From→To, 순서 쌍
      iSmoothSteps=5, fStrength=1.0)
  ```
  - `xJoints` 의 key=From, value=To. To 본이 인플루언스에 없으면 `checkInfluences` 가 자동 추가.
  - From 본이 1개의 To 본에 매핑되면 가중치 전량 이동. 여러 개면 per-vertex 최근접 본 선택 + 스무딩.

> 두 함수 모두 `@addToUI` 데코레이터로 UI에 노출되지만, 데코레이터는 단순 래퍼라
> **일반 Python 함수로 직접 import·호출 가능**. → 체이닝이 곧 1-click 구현.

### 2-2. 기존 A00020 가 이미 두 함수를 각각 호출 중
`JUN_All/tools/A00020_move_skineWeightTool/MOD_move_skinWeightTool_v01.py`
- `JUN_move_each_skin_weight()` → `weights.moveSkinClusterWeights(xJoints=...)`
- `JUN_transfer_meshes_to_meshes()` → `weights.transferSkinCluster(sFrom=..., iMode=...)`

즉 **두 동작은 이미 코드로 검증되어 돌아가고 있다.** 신규 툴 = 둘을 한 콜백에서 순차 호출.

### 2-3. 네이티브(엔진 옵션 2)
Kangaroo 없이 동작하는 대안. UI 토글로 선택 가능하게 한다.
- Transfer → `cmds.copySkinWeights(ss=srcSC, ds=dstSC, sa='closestPoint', ia='oneToOne'/'closestJoint')`
  (B 에 A 의 인플루언스로 `cmds.skinCluster(meshB, A_joints, tsb=True)` 선바인드 후 copy)
- Move → `cmds.skinPercent` 또는 MFnSkinCluster getWeights/setWeights 로 A 본 컬럼을 B 본 컬럼으로 가산
  - **주의**: Kangaroo 의 closest-joint/barycentric/스무딩 로직까지 1:1 재현은 어렵다.
    단순 1:1(본 A_i → 본 B_i, per-vertex 판정 없음) 수준은 충분히 구현 가능.

---

## 3. 설계

### 3-1. 엔진 선택 (사용자 결정 반영)
UI 상단에 **Engine** 라디오/콤보 제공:
- **`Kangaroo` (기본)** — `transferSkinCluster` + `moveSkinClusterWeights` 체이닝. 수동과 100% 동일 결과. kangaroo 플러그인 로드 필요.
- **`Native`** — `copySkinWeights` + `skinPercent` 자체 구현. 의존성 없음(단, Move 는 단순 1:1 매핑).

`app/core/skin_migrate_manager.py` 에서 엔진을 추상화:
```python
class SkinMigrateManager:
    def migrate(self, mesh_a, mesh_b, joints_a, joints_b, *, engine, transfer_mode, ...):
        if engine == "kangaroo": self._run_kangaroo(...)
        else:                    self._run_native(...)
```

### 3-2. 한 번에 처리하는 흐름 (Transfer 버튼 콜백)
```
입력: mesh_a, mesh_b, joints_a=[A1,A2,A3], joints_b=[B1,B2,B3]
검증:
  - mesh_a, mesh_b 존재 & 폴리곤
  - mesh_a 에 skinCluster 존재
  - len(joints_a) == len(joints_b), 모두 존재하는 joint
  - joints_a ⊆ mesh_a 의 인플루언스
1) Transfer:  A 의 웨이트/본을 B 로 (B 는 A_joints 에 바인드)
2) Move:      xJoints = dict(zip(joints_a, joints_b)) 로 B 웨이트를 A본→B본 이동
3) (옵션) removeUnusedInfluences 로 B 에서 weight 0 인 A 본 정리
4) 결과 로그 + (옵션) B 선택
전체를 undoInfo(openChunk/closeChunk) 한 청크로 묶어 한 번에 Undo 가능
```

### 3-3. UI (PySide, A00110 클론)
```
┌ Skin Migrate (A00270) ─────────────────┐
│ Engine:  (•) Kangaroo   ( ) Native      │
│ Transfer Mode: [ Closest Point ▼ ]      │  ← iMode 0~5
│                                         │
│ Source Mesh A : [____________] [<- Set] │  ← 선택에서 채움
│ Target Mesh B : [____________] [<- Set] │
│                                         │
│ Joints A (From)   |  Joints B (To)      │
│ ┌───────────────┐ | ┌───────────────┐   │  ← 두 리스트, index 로 쌍
│ │ A_joint_01    │ | │ B_joint_01    │   │
│ │ A_joint_02    │ | │ B_joint_02    │   │
│ │ A_joint_03    │ | │ B_joint_03    │   │
│ └───────────────┘ | └───────────────┘   │
│ [<- Add From sel] | [<- Add To sel]     │
│ [Clear] [Up/Down] | [Clear] [Up/Down]   │
│                                         │
│ [ ] Remove unused influences after move │
│ [ ] Select result mesh                  │
│            [  TRANSFER  ]               │  ← 1-click
│ Log: ...                                │
└─────────────────────────────────────────┘
```
- A 리스트와 B 리스트는 **index 로 쌍** (A00020 의 `zip` 방식과 동일). 개수 불일치 시 버튼 비활성/경고.
- QListWidget 두 개 + Up/Down 으로 순서 보장.

### 3-4. 파일 구조 (A00110 클론)
```
JUN_All/tools/A00270_skinMigrate/
├── __init__.py                 # from .launch import run
├── launch.py                   # run(): MainWindow → ThemeManager qss → show
├── requirements.txt
├── __dragDrop_A00270.py        # 셸프 설치 (고유 이름 + sys.modules.pop)
├── icon/A00270_skinMigrate.png / .svg
└── app/
    ├── config/version.py       # VERSION, LAST_UPDATE
    ├── core/
    │   └── skin_migrate_manager.py   # 엔진 추상화 + kangaroo/native 구현 (DCC 로직)
    └── ui/
        └── main_window.py      # PySide UI (core 와 분리)
```
- core(로직) / ui(화면) 분리 유지.
- standalone 패키지 충돌 방지: import 는 `tools.A00270_skinMigrate.app.*` + 상대 import (메모리 규칙).

---

## 4. 작업 항목 (TODO)
1. `A00110_animTool` 복제 → `A00270_skinMigrate` 로 리네임 (`__init__`, `launch.py`, `__dragDrop_A00270.py`, `app/config/version.py`).
2. 불필요한 anim core/ui 제거, 빈 골격만 남김.
3. `app/core/skin_migrate_manager.py` 작성
   - `_run_kangaroo()`: transfer → move 체이닝 (+ undo 청크, removeUnused 옵션)
   - `_run_native()`: copySkinWeights → skinPercent (단순 1:1)
   - 입력 검증 헬퍼 (메시/본 존재, 개수 일치, 인플루언스 포함)
4. `app/ui/main_window.py` 작성 (Engine/Mode/메시/본 두 리스트/TRANSFER/Log).
5. ThemeManager qss 적용(카테고리 색 통일).
6. `__dragDrop_A00270.py` (고유 이름 규칙 + `sys.modules.pop(__name__, None)`).
7. 아이콘 추가, CHANGELOG/version 기록.
8. `JUN_All/docs/A00270_skinMigrate.md` 가이드 문서.
9. Maya 2023/2024 실기 테스트(토폴로지 다른 A/B 샘플).

---

## 5. 실현 가능성 — **높음 (High)**

| 근거 | 내용 |
|------|------|
| ✅ 검증된 로직 | Transfer/Move 둘 다 당신이 매일 수동으로 쓰는 함수이며, A00020 가 이미 코드로 호출 중. 신규 작업은 "체이닝 + UI". |
| ✅ 단순 결합 | 핵심 콜백은 `transferSkinCluster(...)` → `moveSkinClusterWeights(xJoints=zip(A,B))` 두 줄. |
| ✅ 정확한 순서 보장 | A/B 본을 두 QListWidget 으로 받아 index zip → `{A_i: B_i}` 매핑. A00020 와 동일 검증된 패턴. |
| ✅ 안전성 | 전체를 undo 한 청크로 묶어 1회 Undo. 실패 시 검증 단계에서 사전 차단. |
| ⚠️ 의존성 | 기본 엔진은 kangaroo 플러그인 로드 필요(기존과 동일 제약). Native 옵션으로 회피 가능하나 Move 는 단순 1:1 수준. |
| ⚠️ Native 한계 | Kangaroo 의 closest-joint/barycentric/스무딩까지는 재현 안 함. "본 1:1, 동일 토폴로지에 가까운 경우" 정도 목적. 정밀 작업은 Kangaroo 권장. |

**결론**: Kangaroo 엔진 기준으로는 **위험 거의 없이 구현 가능**. Native 엔진은 보조 옵션으로 두되 한계를 UI/문서에 명시한다.

---

## 6. 열린 질문 (구현 전 확인)
1. 본 매핑 검증 강도 — A 본이 mesh A 인플루언스에 없으면 에러 중단 vs 경고 후 스킵?
2. Native Move 의 closest-joint per-vertex 판정까지 필요한가, 단순 1:1 로 충분한가?
3. Transfer Mode 기본값 — `Closest Point`(현재 추정) 유지?
4. 다중 메시 쌍(여러 A→B 동시) 지원 필요? (현재 계획은 단일 A→B 쌍)
