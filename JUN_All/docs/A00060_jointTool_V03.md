# A00060_jointTool_V03 — Joint Tool (사용 안내)

`A00060_jointTool_V02` 의 **탭 재분류판**이다. 기능은 하나도 빼거나 더하지 않았고,
평평하던 상위 탭 5개(그 안에 접이식 6섹션)를 **상위 탭 = 카테고리 / 하위 탭 = 기능**
의 2단 구조로 다시 나눠 담았다.

- 버전: `v03.00` (`app/config/version.py`)
- 위치: `JUN_All/tools/A00060_jointTool_V03`
- 형태: 아키텍처 (B) — Maya 내 PySide 툴 (상위 5 × 하위 11 중첩 `QTabWidget`)
- 계획서: [A00060_jointTool_V02 탭 재분류 계획서](plans/A00060_jointTool_V02_tab_reorg_plan.md)
- **`A00060_jointTool_V02` 는 재분류 전 상태로 그대로 둔다**(저장소 관례: 새 버전은 새 폴더).
  앞으로의 작업은 **V03 에서** 한다.

> 버전 번호는 폴더명(`_V03`)에 맞춰 **`03.xx`** 로 센다. V02 는 폴더가 `_V02` 인데
> 버전은 `01.05` 에서 멈춰 있던 저장소 유일한 예외였고, 구조가 바뀌는 이번에 바로잡았다
> (`A00010_humanIKTool_V02`=02.01, `A00110_animTool_V02`=02.12 와 같은 규칙).

---

## 1. 설치 / 실행

### 드래그&드롭 설치
`__dragDrop_A00060_V03.py` 를 Maya 뷰포트로 드래그&드롭 → 현재 셸프에 **`JointTool3`** 버튼 설치.
이후 셸프 버튼 클릭으로 실행된다.

### 코드로 실행
```python
import tools.A00060_jointTool_V03 as A00060_jointTool_V03
A00060_jointTool_V03.run(True)   # True 면 DEV_MODE 에서 reload 후 실행
```

> 창은 `objectName`(`JUN_A00060_jointTool_V03_window`)으로 식별되어 재실행 시 기존 창을 닫고
> 새로 띄운다. V02 와 objectName 이 달라 **두 툴을 동시에 띄워 놓아도 서로를 닫지 않는다.**

---

## 2. 공통 UI

- 상단 **Help > About** 메뉴: 버전/작성자/업데이트 일자.
- 하단 **로그창**: 모든 작업 결과가 `[OK]` / `[ERR]` 로 표시된다. **모든 탭이 공유**한다.
- 모든 작업은 **undo chunk** 로 감싸져 한 번의 Ctrl+Z 로 되돌릴 수 있다.
- 각 리스트는 재사용 위젯 `JUN_mod_tsl_qt_v01`:
  - **Select** : 현재 씬 선택으로 리스트 교체
  - **Add / Del** : 현재 선택 추가(중복 무시) / 선택 항목 제거
  - **Up / Down** : 선택 항목 순서 이동
  - 리스트 항목 클릭 시 해당 노드를 씬에서 선택
  - 우측 상단 `Number:` 에 항목 수 표시
- **하위 탭마다 자기 리스트를 갖는다.** 리스트 제목이 곧 무엇을 담아야 하는지다
  (`Curves` / `Objects` / `Joints` / `Root Joints` / `Start` / `End` / `pole tgt`).
  V02 는 리스트 하나를 다섯 기능이 나눠 써서 같은 자리에 커브·오브젝트·조인트가
  번갈아 담겼다.
- 접이식 프레임(`CollapsibleBox`)은 **사라졌다** — 전부 하위 탭이 됐다.
- 탭 라벨은 짧게 두고 **전체 이름은 탭 툴팁**에 있다. 폭이 모자라면 말줄임(`ElideRight`).

---

## 3. 탭 구조 — 상위 = 카테고리, 하위 = 기능

분류 기준은 하나다 — **"무엇이 바뀌는가"**. 입력이 아니라 결과물로 나눈다.

| 상위 탭 | 무엇이 바뀌나 | 하위 탭 |
|---|---|---|
| **Create** | 씬에 **조인트가 생긴다** | `From Curve` · `From Object` · `Divide` |
| **Orient** | 있는 조인트의 **방향만** 바뀐다 (위치·개수 불변) | `Aim` · `Set Orient` · `Orient / Rotate` |
| **Chain** | 있는 체인의 **구조·연결**을 고친다 | `Reverse` · `IK Edit` |
| **Curve** | 조인트가 아니라 **커브·디포머**를 다룬다 (조인트를 만들기 전 준비) | `Edit Curve` · `Clusters` |
| **Select** | **씬을 바꾸지 않는다** — 고르기만 한다 | `Unused Joints` |

### V02 에서 어디로 갔나

| V02 위치 | V03 위치 |
|---|---|
| Curve > joint to Crv > `Joints to Crv` | **Create > From Curve** |
| Curve > joint to Crv > `Clusters` | **Curve > Clusters** |
| Curve > joint to obj > `Match to Obj` / `Match to Sel` | **Create > From Object** |
| Curve > joint orient and rotate | **Orient > Orient / Rotate** |
| Curve > Set Orient | **Orient > Set Orient** (접힘 해제) |
| Divide | **Create > Divide** |
| Aim | **Orient > Aim** |
| Hair > Sub Tool : Curve (Separate / Remove / Rebuild) | **Curve > Edit Curve** |
| Hair > Tool : Edit > `Reverse joint chain` | **Chain > Reverse** |
| Hair > Tool : Edit > `Select Unused Joints` | **Select > Unused Joints** |
| IK Edit | **Chain > IK Edit** |

**빠지는 기능 없음. 합쳐지는 기능 없음. 버튼 이름 바뀌는 것 없음.**
사라진 것은 상위 탭 이름 `Hair` 와 접이식 섹션 제목들뿐이다
— 헤어 리깅에 쓰던 기능은 **`Curve > Edit Curve`** 와 **`Chain > Reverse`** 에 있다.

---

## 4. 탭별 사용법

### 4.1 Create — 조인트가 생긴다

#### Create > From Curve
`Curves` 리스트의 **NURBS 커브**를 따라 조인트 체인을 만든다.

- 포인트 종류 라디오:
  - `Control Vertex (Omit [1], [-2])` : CV 사용하되 두 번째·끝에서 두 번째 CV 생략
  - `Control Vertex` : 모든 CV
  - `Edit Point` : 에디트 포인트
- `Joints to Crv` : 위 옵션으로 조인트 생성 (월드 절대 좌표 — §6)
- 커브가 아닌 것이 들어 있으면 `is not a nurbsCurve` 경고를 내고 건너뛴다.

#### Create > From Object
`Objects` 리스트의 오브젝트/버텍스 위치마다 조인트를 만든다.

- `Connect` : 조인트들을 체인으로 연결 / `Separate` : 각각 분리(루트)
- `Foward axis` / `Secondary axis` / `Secondary axis orient` : orient 축 옵션
- `Match to Obj` : **리스트에 담긴 항목**으로 실행
- `Match to Sel` : **지금 씬에서 선택한** 오브젝트/버텍스로 바로 실행 (리스트 불필요, §7).
  이때 읽는 것은 리스트 내용이 아니라 **이 탭 리스트의 `Order` 체크박스**다.

#### Create > Divide
시작/끝 오브젝트 쌍 사이를 직선 커브로 잇고, 그 길이를 균등 분할해 조인트를 만든다.

- `Start` / `End` 리스트(좌우)
- `Select Start End` : 현재 선택 순서로 (sel[0]~sel[n-2]) = Start, (sel[1]~sel[n-1]) = End 자동 구성
- `Add Start End` : **정확히 2개** 선택 → 첫째를 Start, 둘째를 End 리스트에 추가
- `Joints Number` : 쌍마다 생성할 조인트 수 → `Make Joint Divided`
- Start/End 리스트의 항목 수는 같아야 한다.

### 4.2 Orient — 방향만 바뀐다

#### Orient > Aim
Start~End 조인트 체인을 **IK+pole 식으로 정렬**한다 — 회전만 바꾸고 **모든 joint 의 월드 위치는
완전 보존**. 자식을 향하는 +X 는 그대로 두고, 선택한 **Aim axis** 가 폴 타깃을 향하도록
X 둘레 트위스트만 적용한다.

- `Start` / `End` / `pole tgt` 리스트(3분할)
- `Select Start End` / `Add Start End` : Start·End 채우기(`Create > Divide` 와 동일 규칙)
- `Aim axis` (X/Y/Z, 기본 Y) : 폴 타깃을 향할 보조축. X 는 트위스트 축이라 보통 Y/Z.
- `Make Joint Aim` : 각 쌍의 체인을 root→leaf(부모→자식) 순으로 처리. 부모 X 를 **자식의 원본
  위치로 조준**(조준된 체인이면 X 불변=swing 보존)하고, 보조축이 pole 을 향하도록 X 둘레 트위스트를
  부모 **jointOrient 에 기록**(rotate=0). **translate 는 건드리지 않으므로** 자식이 고정 거리만큼
  새 X 위에 놓여 **월드 위치가 그대로 유지**된다. `setAttr`(jointOrient)만 쓰므로
  **레퍼런스 조인트에서도 동작**, `aimConstraint`/reparent 미사용 → 평가 cycle 없음.

#### Orient > Set Orient
`Joints` 리스트 조인트의 선택 축 `jointOrient` 를 입력 각도로 설정한다.

- `Orient axis` / `Orient degree` → `Set joints orientation`
- 내부적으로 체인을 역순 unparent → 설정 → 정순 reparent 한다(리스트는 root→end 순서여야 함).

#### Orient > Orient / Rotate
`Joints` 리스트 조인트에 대해

- `joint orient to rotate` : jointOrient 값을 0 으로, rotate 에 합산
- `rotate to joint orient` : 반대로 합산

### 4.3 Chain — 체인 구조를 고친다

#### Chain > Reverse
`Root Joints` 리스트의 root 조인트 체인을 위치/radius 유지하며 역순 재생성한다.

- `Remove origin` 체크 : 켜면 원본 체인 삭제 + `_rev` 접미사 제거
- 리스트 순서가 체인 순서(root→end)와 일치해야 한다.

#### Chain > IK Edit
이미 설치된 `ikHandle` 과 폴 벡터 컨스트레인트를 **그대로 둔 채** 본 체인을 고친다.
토글 버튼 `EDIT IK CHAIN` 으로 IK 를 내리고, 다시 눌러 확정하면 핸들과 폴 벡터가 편집된
체인에 맞춰진다. 이 탭만 리스트를 쓰지 않고 `Load Selection` 으로 대상을 잡는다.
**자세한 설명은 §8.**

> 편집 상태는 UI 가 아니라 **ikHandle 노드**에 있다(§8.6). V03 은 여기에 더해,
> **`Chain > IK Edit` 탭을 다시 열 때마다 씬을 다시 읽어** 버튼 상태를 맞춰 둔다
> (V02 는 창을 만들 때 한 번만 읽었다).

### 4.4 Curve — 커브·디포머를 다룬다 (조인트는 건드리지 않는다)

#### Curve > Edit Curve
`Curves` 리스트의 커브 자체를 손본다 (헤어 커브 정리 — 예전 `Hair` 탭).

- `Separate Curve` : 각 커브 shape 를 개별 transform(`hairCrv`)으로 분리
- `Max Length` + `Remove Curve` : 길이가 값 이하인 커브 삭제
- `Interval` + `Max joints` + `Rebuild Curve` : 길이/간격 기반 span 산정해 rebuild(최대 span = Max joints − 1)

#### Curve > Clusters
`Curves` 리스트의 커브 CV 마다 **클러스터 디포머**를 달아 커브를 손으로 잡을 수 있게 한다.
**조인트를 만들지 않는다** — 그래서 `Create` 가 아니라 여기에 있다.

> 이 기능은 타입 검사가 없어 커브 아닌 것을 주면 예외로 종료된다(V02 와 동일).
> V02 에서는 조인트와 같은 리스트를 쓴 탓에 쉽게 밟는 함정이었고,
> V03 은 리스트가 갈려 실수 자체가 어려워졌다.

### 4.5 Select — 씬을 바꾸지 않는다

#### Select > Unused Joints
`Joints` 리스트 조인트 중 **어느 skinCluster 에도 쓰이지 않는 것**을 리스트에서 하이라이트하고
씬에서 선택한다. **지우지는 않는다** — 지우는 것은 사용자가 판단한다.
이 툴에서 **씬을 전혀 바꾸지 않는 유일한 기능**이라 카테고리를 따로 두었다.

---

## 5. 구조 (개발자용)

```
A00060_jointTool_V03/
├── __init__.py                     # run 노출
├── launch.py                       # run(): reload → MainWindow → coral_dark 테마 → show
├── __dragDrop_A00060_V03.py        # 셸프 버튼 설치 (고유 파일명)
├── CHANGELOG.md
├── icon/A00060_jointTool_V03.svg|.png
├── requirements.txt
└── app/
    ├── config/version.py           # VERSION / LAST_UPDATE
    ├── core/                       # UI 비의존 maya.cmds 로직 (V02 에서 그대로)
    │   ├── curve_joint_manager.py  # Create > From Curve / Curve > Clusters
    │   ├── obj_joint_manager.py    # Create > From Object / Orient > Set Orient · Orient / Rotate
    │   ├── divide_manager.py       # Create > Divide
    │   ├── aim_manager.py          # Orient > Aim
    │   ├── hair_manager.py         # Curve > Edit Curve / Chain > Reverse / Select > Unused Joints
    │   └── ik_edit_manager.py      # Chain > IK Edit (ikHandle / 폴 벡터 갱신)
    └── ui/
        └── main_window.py          # 중첩 QTabWidget (5 × 11) + 공유 로그 + Help>About
```

- `app/core/*` 는 **V02 에서 한 줄도 고치지 않았다.** 바뀐 것은 UI 뿐이다.
  (`hair_manager` 는 이제 세 카테고리에 흩어져 있지만, 모듈명을 바꾸면 로직 diff 가 불필요하게 커진다.)
- `app/ui/collapsible.py` 는 **삭제됐다** — 접이식이 전부 하위 탭이 되어 쓰이지 않는다.
  다시 필요하면 공용 `Framework.qt.JUN_mod_collapsible_qt` 를 쓴다(툴 로컬 사본을 다시 만들지 않는다).

### 탭을 더할 때

`main_window.py` 상단의 **분류표에 줄만 넣는다.**

```python
CREATE_PAGES = (
    ("From Curve", "From Curve - ...", "_build_create_from_curve_tab"),
    ...
)
CATEGORIES = (
    ("Create", "Create new joints.", CREATE_PAGES, "create_tabs"),
    ...
)
```

- 페이지 빌더는 평범한 `QWidget` 을 돌려주면 된다 — `_build_sub_tabs` 가 `_scrolled()` 로
  감싸 하위 탭에 꽂는다. **상위에는 스크롤을 씌우지 않는다**(이중 스크롤).
- **상위 탭에 기능 하나를 직접 올리지 않는다.** 그 예외가 다시 불균형을 만든다.
- 하위가 하나뿐인 카테고리(`Select`)도 **하위 탭 바를 남긴다** — 없으면 기능 이름이 화면에서 사라진다.
- 탭 전환을 감지해야 한다면 **상위 탭 인덱스로 비교하지 말 것** — 탭이 늘고 줄면 뜻이 조용히 변한다.
  지금은 상위가 위젯 동일성(`self.chain_page`), 하위가 `CHAIN_PAGES` 순서와 묶인 상수(`IKE_SUB_INDEX`)다.
  `chain_tabs.widget(i)` 는 페이지가 아니라 **`QScrollArea` 래퍼**를 돌려준다.

### MEL → Python 포팅 매핑(요약)

| MEL proc | 이식 위치 |
|----------|-----------|
| `JUN_cmd_create_joints_toCrv` / `JUN_cmd_create_clusters_toCrv` | `curve_joint_manager` |
| `JUN_cmd_create_joints_toObj` / `JUN_cmd_joint_swap_rotate` / `JUN_cmd_set_jntOri` | `obj_joint_manager` |
| `JUN_cmd_makeJnt_divide` / `JUN_cmd_selStrEnd` / `JUN_cmd_addStrEnd` | `divide_manager` |
| `JUN_cmd_make_jntAim` | `aim_manager` |
| 리스트 Select/Add/Del/Up/Down (`JUN_cmd_*` TSL 군) | `JUN_mod_tsl_qt_v01` 내장 |

---

### 참고 / 주의

- 작업 대상은 **씬 선택이 아니라 각 하위 탭의 리스트에 담긴 항목**이다.
  **예외**: `Create > From Object` 의 `Match to Sel` 만 리스트를 거치지 않고 현재 씬 선택으로 동작한다(§7).
- `Set Orient` / `Reverse` 는 리스트 순서가 체인 순서(root→end)와 일치해야 한다.
- **리스트는 탭마다 따로다.** V02 처럼 한 번 담아 여러 기능에 돌려 쓸 수 없다 — 대신
  엉뚱한 타입을 담은 채 다른 버튼을 누를 일도 없다.

---

## 6. 월드 절대 위치로 조인트 생성 (v01.03)

**증상**: 오브젝트/커브가 이동·회전·스케일된 **그룹 계층 아래**에 있으면 **Match to Obj**(`Create > From Object`)·
**Make Joint Divided**(`Create > Divide`)·**Joints to Crv** 로 만든 조인트가 **엉뚱한 위치**에 생겼다.
원인은 대상 좌표를 **월드 기준 절대값**으로 받지 않은 것.

세 곳을 수정했다(모두 `app/core`):

| 위치 | 문제 | 수정 |
|------|------|------|
| `divide_manager.curves_from_pairs` | `xform(q, translation)` = **오브젝트 로컬 좌표**로 커브 생성 | `ws=True` 추가 → 월드 좌표 |
| `curve_joint_manager._joint_at_curve_point` | `pointPosition`(이미 월드)에 커브 world translation 을 **한 번 더 가산** → 커브가 원점이 아니면 위치 2배 오차 | 이중 가산 제거, 월드값 직접 사용 + `xform(ws)` 로 확정 |
| `obj_joint_manager._joint_at_obj` (Match to Obj) | 월드값을 받지만 `joint -p` 가 부모 체인 아래로 들어갈 때 위치 미확정 | 생성 직후 `xform(jnt, ws=True, translation=pos)` 로 월드 위치 확정 |

- `aim_manager` 는 원래부터 전 구간 `ws=True`(위치 보존형) 라 변경 없음.
- 세 수정 모두 **원점/무계층 케이스는 동작 불변**(하위 호환), 계층 아래 오브젝트만 올바르게 교정된다.

---

## 7. Match to Sel — 리스트 없이 현재 선택으로 바로 실행 (v01.04)

`Create > From Object` 의 `Match to Obj` **오른쪽에 `Match to Sel` 버튼**이 있다.

| 버튼 | 대상 | 순서 |
|------|------|------|
| `Match to Obj` | 그 탭의 **`Objects` 리스트**에 담긴 항목 | 리스트 순서 (Up/Down 으로 조정) |
| `Match to Sel` | **지금 씬에서 선택한** 오브젝트/버텍스 | Maya 선택 순서 (아래 Order 참고) |

축 옵션(`Connect`/`Separate`, Foward / Secondary axis, Secondary axis orient)은 **두 버튼이 공유**한다.
버텍스 몇 개를 찍고 바로 조인트를 놓는 흐름에서 리스트에 올리는 단계를 생략할 수 있다.

### 버텍스 선택 순서 (Order 체크박스)

`cmds.ls(sl=True)` 는 **컴포넌트를 고른 순서가 아니라 인덱스 순서**로 돌려준다. 버텍스를
5 → 0 → 3 → 1 로 찍어도 그냥 읽으면 0, 1, 3, 5 다. 그래서 `Match to Sel` 은 같은 탭 리스트(`Objects`)
헤더의 **`Order` 체크박스**를 그대로 따른다:

- **Order ON** — Maya 의 `Track Selection Order` 프리퍼런스가 켜지고
  `ls(orderedSelection=True, flatten=True)` 로 읽는다 → **찍은 순서대로** 체인이 생긴다.
  pref 는 **켠 시점부터** 기록하므로 **체크한 뒤에 다시 선택**해야 순서가 잡힌다.
- **Order OFF** — Maya 기본 순서(컴포넌트는 인덱스 순서). 2개 이상 선택 시 로그에
  `[INFO] ... 'Order' is off` 로 알려준다.

> **함정**: pref 가 꺼져 있으면 `ls(orderedSelection=True)` 는 **에러 없이 조용히 인덱스 순서**를
> 돌려준다. "순서가 되는지"는 반환값이 아니라 pref 를 조회해서 판단해야 한다 —
> 그 판정은 공용 위젯(`JUN_mod_tsl_qt_v01`)이 이미 하고 있어서, 이 버튼은 위젯의
> **`maya_selection()`** (v01.04 에서 public 으로 노출) 을 호출만 한다. Select/Add 버튼과 정확히
> 같은 규칙이라 두 경로가 어긋날 일이 없다.

- 선택이 비어 있으면 아무것도 만들지 않고 `[ERR] Match to Sel : nothing selected in the scene`.
- 전체 작업은 기존과 같이 **undo chunk** 로 묶인다(Ctrl+Z 한 번).
- headless(mayapy) 검증: pref ON/OFF 순서 거동, 찍은 순서(5,0,3,1)대로 생기는 체인,
  `Separate` 모드의 전원 루트 여부, 오프셋 그룹 아래 오브젝트의 월드 위치 보존.

---

## 8. IK Edit — 설치된 ikHandle 을 그대로 둔 채 본 체인 고치기 (v01.05 / V03 에서는 `Chain > IK Edit`)

본 체인에 ikHandle 을 걸어 둔 뒤 "조인트 위치를 조금 손보고 싶다" 는 상황을 위한 탭이다.
**IK 도 폴 벡터 컨스트레인트도 지우지 않고**, 체인만 고친 뒤 리그를 편집 결과에 맞춰 준다.

### 8.1 마야에는 이 기능이 없다

마야 2024 의 컨스트레인트에는 어트리뷰트 에디터에 **`Update Offset`** 버튼이 있다. 드리븐을
손으로 옮긴 뒤 그 자리를 새 오프셋으로 굳히는 버튼이고, 실체는
`parentConstraint -e -maintainOffset <targets> <constraint>` 다
(`scripts/AETemplates/AEparentConstraintTemplate.mel`).

**ikHandle 에는 그 버튼이 없다.** `AEikHandleTemplate.mel` 을 다 뒤져도 없고,
`ikHandle` 명령에도 대응 플래그가 없다(`-enable` 같은 플래그는 아예 존재하지 않는다).
그래서 이 기능을 만들었다.

### 8.2 왜 그냥은 안 되는가 — 실측

| | 실측 결과 |
|---|---|
| IK 가 켜진 채 중간 조인트를 `(2, 5, 1)` 로 이동 | 솔버가 **`(0.00068, 5.2, 1.72)` 로 되돌린다** |
| IK 를 끄고 고친 뒤, **핸들만** 이펙터로 스냅 | 최대 편차 **1.615** — 체인이 옛 평면으로 비틀린다 |
| 핸들 스냅 **+ 폴 벡터 재계산** | 최대 편차 **0.00000000** (위치·회전 모두) |

두 번째 줄이 이 기능의 핵심이다. 폴 벡터는 "IK 루트에서 뻗은 벡터" 이고 **체인이 놓일 평면**을
정한다. 체인을 고치면 그 평면이 바뀌는데 폴 벡터는 옛 평면을 계속 가리키므로, 핸들 위치만
맞춰서는 체인이 축을 중심으로 돌아가 버린다.

### 8.3 어떻게 고치는가

편집이 끝난 체인에서 **원하는 폴 벡터를 역산**해 넣는다.

```
poleVectorConstraint 의 식 (Maya 2024 실측)
    pv = (target_world - ikRoot_world) * handle.parentInverseMatrix(3x3) + offset
```

`offset` 은 출력(핸들 부모) 공간에서 그대로 더해지므로 역산이 선형이다.

```
    new_offset = desired_pv - (current_pv - current_offset)
```

즉 **컨스트레인트도 타깃도 건드리지 않고 offset 만** 갱신한다 — 마야의 `Update Offset` 과
정확히 같은 발상이다.

`desired_pv` 는 편집된 체인의 팔꿈치 방향이다. 루트→중간 벡터에서 체인 축(루트→끝) 성분을 뺀
**수직 성분**을 쓴다. 축과 평행해질 수 없어서 평면 정의가 안정적이다.

> **twist 보정** — `ikHandle.twist` 가 0 이 아니면 솔버가 폴 벡터 평면 위에 그 각을 **더** 얹는다
> (보정 없이는 편차 1.06). 그래서 원하는 폴 벡터를 체인 축 기준 **−twist** 만큼 미리 돌려 상쇄한다.
> **twist 값 자체는 애니메이션 채널이라 건드리지 않는다.** (`roll` 은 `ikRPsolver` 가 쓰지 않는다 — 실측.)

### 8.4 쓰는 법

1. IK 핸들을 고르고 `Load Selection`. **핸들 자체 / 체인 안의 아무 조인트 / 핸들을 구동하는
   컨트롤러** 중 무엇을 골라도 된다. 로드 직후 로그에 무엇이 되고 무엇이 막히는지 미리 나온다.
2. **`EDIT IK CHAIN`** — IK 가 내려가고 체인이 자유로워진다. 버튼이 주황색으로 바뀐다.
3. 조인트를 옮기거나 돌린다. 원하는 만큼.
4. **버튼을 다시 누른다** — 핸들이 새 체인 끝으로, 폴 벡터가 새 평면으로 맞춰지고 IK 가 돌아온다.
   로그에 **편집한 포즈와 얼마나 다른지 실측치**가 찍힌다.

`Cancel Edit` 은 `EDIT IK CHAIN` 을 누른 시점으로 전부 되돌린다(조인트 · 핸들 · 폴 벡터 오프셋 ·
폴 벡터 타깃 위치 · `ikBlend`).

`Update Now (no edit session)` 는 **편집 세션 없이 지금 상태로 한 번만 맞춘다.** 이미 다른
방법으로 IK 를 끄고 체인을 고쳐 둔 경우에 쓴다 — 마야 컨스트레인트의 `Update` 버튼에 가장
가까운 것이 이 버튼이다.

### 8.5 On Finish 옵션

| 옵션 | 뜻 |
|---|---|
| `Pole vector` → **Constraint offset** | **기본값.** 컨스트레인트와 타깃은 있던 자리 그대로, offset 만 갱신 |
| `Pole vector` → Move the pole vector target | 타깃 오브젝트를 새 평면 위로 옮기고 offset 은 0 으로. 오프셋이 굳는 걸 싫어하는 리그용이지만 **애니메이터의 컨트롤을 움직인다** |
| `Snap` → **IK handle** | **기본값.** 핸들 자신을 옮긴다 |
| `Snap` → Handle's parent | 부모를 옮긴다. 핸들이 IK 컨트롤 밑에서 로컬 0 으로 있어야 하는 리그용 |
| `Set preferred angles from the edited pose` | 기본 ON. 체인 조인트마다 Set Preferred Angle |

### 8.6 상태는 씬에 있다

`A00275_skinTool_V01` 의 `Edit Mesh` 와 같은 규칙이다. 편집 중이라는 사실과 되돌릴 스냅샷은
UI 가 아니라 **ikHandle 노드의 어트리뷰트**(`JUN_ikEdit` / `JUN_ikEditData`)에 있다.
툴을 껐다 켜도, 씬을 저장했다 열어도 이어서 확정하거나 취소할 수 있고, 툴을 열면 진행 중인
편집을 알아서 되찾는다.

### 8.7 알아 둘 것

- **`ikBlend` 가 FK/IK 스위치에 연결돼 있으면** `setAttr` 이 거부된다(실측 `RuntimeError`).
  그럴 때만 마야의 `Enable IK Solvers` 토글(`ikSystem -e -solve 0`)로 물러선다 — **씬 전체의 IK 가
  꺼지므로** 로그에 그렇게 썼다고 남긴다. 이 플래그는 씬이 아니라 세션 상태라 마야를 다시 켜면
  살아나는데, 툴을 열 때 진행 중인 편집을 찾으면 다시 꺼 준다.
- **`snapEnable`(기본 ON) 은 IK 가 꺼진 동안 핸들을 이펙터에 자동으로 붙여 준다.** 그래서 자유로운
  핸들에서는 스냅 단계가 사실상 무동작이다. `snapEnable` 을 꺼 둔 리그에서는 핸들이 뒤에 남으므로
  이 툴의 명시적 스냅이 실제로 일한다(둘 다 테스트로 덮었다).
- **핸들이 pointConstraint 로 구동되면** 핸들을 직접 못 옮기므로 그 컨스트레인트의 `offset` 을
  갱신한다. 이때 델타를 핸들의 트랜스폼에서 내면 안 된다 — 위 `snapEnable` 때문에 이미 이펙터에
  붙어 있어서 델타가 0 으로 나온다. **컨스트레인트의 출력 플러그(`constraintTranslate`)를 직접 본다.**
  parentConstraint 등 그 밖의 구동은 막힌 이유를 로그로 알리고 건너뛴다.
- **`ikSplineSolver` 는 거부한다.** 체인을 커브가 구동하므로 "핸들 스냅" 이라는 개념이 성립하지
  않는다. 조용히 망가뜨리는 대신 무엇이 문제인지 로그로 알린다.
- **체인이 일직선이면** 팔꿈치 방향을 읽을 수 없다. 폴 벡터를 손대지 않고 그 사실을 경고한다.
- `ikSCsolver` 는 폴 벡터가 없어서 핸들 스냅만으로 편차 0 이다.

### 8.8 검증

mayapy(Maya 2024) 헤드리스로 **core 87항목 + UI 스모크 56항목**.

편차 0 은 정적으로만 확인한 것이 아니라 — **핸들을 멀리 끌었다 되돌려도, 씬을 저장했다 다시
열어도** 편집한 포즈가 그대로 재현되는지까지 확인했다. 그 밖에 3·4 조인트 체인, 부모가 변환된
그룹 아래의 핸들(폴 벡터가 핸들 부모 공간에 산다), `twist` +35/−50/0, 폴 벡터 컨스트레인트가
없는 경우, `ikSCsolver`, `ikSplineSolver` 거부, `ikBlend` 가 연결된 리그, `snapEnable` ON/OFF,
pointConstraint 로 구동되는 핸들, 두 핸들 동시 편집, `Cancel` 복원, 일직선 체인 경고.
