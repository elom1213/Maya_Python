# A00290_BSTool

레거시 `JUN_PY_BSTool_V01_01`(maya.cmds) 을 **PySide(Qt)** 로 재작성한 blendShape 작업 툴.
기존 툴의 **Connect BS 탭은 제외**하고 **Edit BS 탭만** 이식했으며, **Base Shape 탭**과
**Shape Editor 탭**을 신규 추가했다.

- **아키텍처**: (B) Standalone/Qt — PySide, Maya 내 실행 (`A00270_skinMigrate` 클론, green_dark 테마)
- **버전**: `app/config/version.py`
- **설치**: `__dragDrop_A00290.py` 를 Maya 뷰포트로 드래그&드롭 → 셸프 버튼 생성 → `tools.A00290_BSTool.run(True)`

---

## 탭 1 — Shape Editor  (v01.02~, Maya 기본 Shape Editor 대체)

Maya 의 Shape Editor 는 가끔 원하는 타겟을 트리에 노출하지 않아 **Edit 버튼조차 없어** 수정을 못 한다.
이 탭은 blendShape 노드의 별칭(`aliasAttr`)에서 타겟을 **직접** 읽으므로 항상 전부 보이고,
타겟마다 Edit 토글이 생긴다.

### 사용 흐름
1. 씬에서 blendShape 노드(또는 그 메시)를 선택 → **`Select BlendShape Nodes`**.
   리스트가 바뀌는 즉시 아래에 타겟 행이 채워진다. (여러 노드를 담으면 노드별 헤더로 구분)
2. 원하는 타겟의 **`Edit`** 버튼 ON → 베이스 메시가 선택되고 그 타겟 모양이 보인다.
3. 뷰포트에서 메시를 조각(버텍스 이동, 스컬프트 브러시 등).
4. **`Edit`** 버튼 OFF → 수정된 메시 상태가 **그대로 타겟 모양으로 확정**된다.

| 요소 | 동작 |
|------|------|
| **Edit** (토글) | 그 타겟의 sculpt 모드 ON/OFF. 노드당 **한 타겟만** 가능(Maya 와 동일) — 다른 타겟을 켜면 이전 것이 자동 해제 |
| weight 스핀박스 | 타겟 weight 직접 조절. 편집 중에는 1.0 으로 고정(비활성), 잠금/구동된 weight 도 비활성 |
| **Filter** | 타겟 이름 부분 일치 필터 (MetaHuman 처럼 타겟이 수백 개일 때) |
| **Refresh** | 리스트의 노드에서 타겟/weight/편집 상태를 다시 읽는다 |
| **Exit Edit Mode (all blendShapes)** | 씬의 모든 blendShape 편집 모드를 해제 |

### 동작 원리

```python
cmds.sculptTarget(bs, e=True, target=weightIdx, inbetweenWeight=1.0)  # Edit ON
cmds.sculptTarget(bs, e=True, target=-1)                              # Edit OFF (편집 확정)
```

ON 인 동안 베이스 메시에 가한 버텍스 편집은 그 타겟의 델타
(`inputTargetItem[6000].inputPointsTarget`)로 기록된다.

> **주의 — `setAttr` 로는 안 된다.**
> 같은 값을 담는 `<bs>.inputTarget[g].sculptTargetIndex` 어트리뷰트를 `setAttr` 로 직접 써도
> 편집 모드처럼 *보이지만* 실제로는 동작하지 않는다. 디포머가 버텍스 편집을 가로채도록 설정하는
> 일은 `sculptTarget` 커맨드가 하고 `setAttr` 은 값만 바꾸므로, 편집이 그대로 **베이스 shape 의
> tweak(`.pnts`)** 로 들어가 **원본 메시가 수정**된다. (Maya 의 `setSculptTargetIndex.mel` 은 이미
> sculpt 세팅이 끝난 상태에서 인덱스만 옮기는 용도다.)
> 따라서 **읽기는 어트리뷰트로, 쓰기는 반드시 커맨드로** 한다.

부가 동작:

- Edit 진입 시 타겟이 보이도록 **weight 를 1.0** 으로 올리고 이전 값을 저장 → 해제 시 **원복**.
- `envelope` 이 1.0 이 아니면 1.0 으로 맞춘다(편집 결과가 그대로 보이도록).
- weight 가 잠기거나 다른 노드에 구동되면 값을 바꾸지 못하므로 로그로 안내한다(편집 자체는 가능).
- Maya 뷰포트의 편집 HUD(`updateBlendShapeEditHUD`)를 함께 갱신 → 기본 Shape Editor 와 같은 표시.
- **창을 닫으면** 열려 있던 편집 모드를 모두 해제(= 편집 결과 확정)한다.

로직: `core/shape_editor_manager.py` — `ShapeEditorManager.begin_edit / end_edit / exit_all_edits`.

## 탭 2 — Edit BS

여러 blendShape 노드를 리스트에 담고 일괄 처리한다. (레거시 Edit BS 탭 그대로)

| 버튼 | 동작 |
|------|------|
| **Select BlendShape Nodes** / Add / Del / Up / Down / Sort | 씬 선택을 blendShape 리스트로 관리 (공용 `JUN_mod_tsl_qt`) |
| **Key every target** | 각 타겟을 프레임 `i` 에서 `1`, `i-1`/`i+1` 에서 `0` 으로 키 → 타임라인을 넘기면 타겟이 하나씩 순차로 보인다 |
| **Copy every target** | 위 키를 건 뒤, 프레임마다 베이스 메시를 복제해 각 타겟 모양을 **타겟 이름의 메시**로 추출(visibility off) → `<node>_targets` 그룹으로 묶음 |
| **Copy every frame** (v01.01~) | `Start`/`End` 구간을 **1프레임마다** 씬에서 **선택한 메시**를 복제(visibility off)해 `<mesh>_f<frame>`(0 패딩) 으로 추출 → `<mesh>_frames` 그룹. **키를 걸지 않고** 현재 씬 애니메이션 상태를 그대로 캡처 |

> 리스트에 담긴 노드의 이름/순서는 자유. blendShape 가 아닌 항목은 무시된다.

> **Copy every frame** 의 구간 입력 UI(`Start`/`End` + `Get Current`)는 A00110 Follow 탭 패턴을 따른다.
> `Get Current` 는 해당 입력을 현재 Maya 프레임으로 채운다. 대상은 blendShape 리스트가 아니라 **씬에서
> 선택한 메시**다. `suspend_refresh` 로 빠르게 처리하고 끝나면 **현재 프레임을 원복**한다(전체 단일 undo).
> 로직: `edit_bs_manager.copy_every_frame(meshes, start, end)`.

## 탭 3 — Base Shape  (신규)

선택한 타겟의 **"기본(weight=1.0) 모양"을 다시 정의**한다.

### 사용 흐름
1. 아웃라이너/노드에디터에서 blendShape 노드(또는 그 메시)를 선택하고 **`<- Set`**.
   (메시를 고르면 히스토리에서 blendShape 를 찾아 채운다.)
2. **`List Targets`** → 타겟 이름이 weight 인덱스 순으로 리스트업된다.
3. 리스트에서 대상 타겟을 선택(`Select All` / `Clear Selection` 보조).
4. **Value** 에 기준 값을 입력(예: `0.5`, `1.3`).
5. **`Apply (Value -> 1.0)`** → 선택 타겟의 *Value 에서 보이던 모양*이 *weight 1.0 의 기본 모양*이 된다.

### 동작 원리
blendShape 결과는 `base + weight * delta` 이다(`delta` = 타겟 포인트 오프셋).
weight `X` 에서 보이던 모양을 weight `1.0` 의 모양으로 만들려면 **델타를 `X` 배**하면 된다:

```
new_delta = delta * X
weight 1.0 → base + 1.0*(delta*X) = base + X*delta = 예전 weight X 모양
```

즉 "값 X 의 모양을 1.0 의 기본 모양으로" == 타겟 포인트 델타를 `X` 배 스케일.
구현은 blendShape 노드의
`inputTarget[g].inputTargetGroup[w].inputTargetItem[i].inputPointsTarget`(pointArray)
를 직접 읽어 `X` 배 후 다시 써넣는다. in-between 아이템과 다중 출력 지오메트리도 함께 스케일한다.
전체가 **단일 undo 청크**.

- Value `0.5` → 타겟 강도 절반, `1.3` → 과장, 음수 → 반대 방향.
- Value 는 0 이 될 수 없다(0 이면 델타가 사라지므로 경고).
- 저장된 포인트 델타가 없는 타겟(라이브 지오 입력으로 연결된 경우 등)은 건너뛰고 로그에 표시.

---

## 구조

```
A00290_BSTool/
├── __init__.py                 # run() 노출
├── launch.py                   # run(reload): 창 생성 + green_dark 테마
├── __dragDrop_A00290.py        # 셸프 버튼 설치
├── CHANGELOG.md / requirements.txt
├── icon/A00290_BSTool.(png|svg)
└── app/
    ├── config/version.py
    ├── core/
    │   ├── blendshape_utils.py     # 타겟 조회 / 인덱스 매핑 / 베이스 메시 / 선택→blendShape
    │   ├── shape_editor_manager.py # Shape Editor 탭: sculptTargetIndex 편집 토글
    │   ├── edit_bs_manager.py      # Edit BS 탭: key/copy every target + copy every frame
    │   └── base_shape_manager.py   # Base Shape 탭: 타겟 델타 스케일
    └── ui/main_window.py           # QTabWidget 3탭 + 공용 로그
```

레거시 대비: **Connect BS 탭 제거**(Source/Attr/Destination 연결 기능). Edit BS 탭은 동작 동일.
