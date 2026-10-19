# A00550_PoseMapper — 계획서 (음소 포즈 매핑 + blendWeighted 가중치 탭)

> **작성** 2026-10-19 · 상태: **구현 중** (진행 기록 §10 — 중단되면 §10 의 첫 미완료 항목부터 이어서) · 대상 Maya 2024
> 배경: JUN_JALI `out/jali_arkit_mapping_ctl.ma` 에서 JALI 음소 → ARKit 가중치를 손으로 다듬다가 나온 요청.
> 관련: `A00540_JaliLipSync`(음성 → JALI 키) · JUN_JALI `docs/0040_jali_arkit_mapping.md`(실측 시작 가중치) ·
> JUN_JALI `examples/build_jali_arkit_node.py`(지금 쓰는 bw → md → clamp 노드망)

---

## 0-A. 확정 사항 (2026-10-19 사용자 답)

| 항목 | 확정 |
|------|------|
| 툴 | **새 툴 `JUN_All/tools/A00550_PoseMapper`** (Q1) |
| 기준값(ref) | **기본 10, 사용자가 임의의 실수**를 입력 (`QDoubleSpinBox`, 0.001 ~ 100000, 소수 3자리). Solo preview 도 이 값으로 음소를 켠다. 라이브러리 json 의 `ref_value` 에 저장되고, Connect 때 라이브러리 값을 기본으로 보여 주되 바꿀 수 있다 (Q2) |
| 이미 연결된 타겟 | **기본 Skip** — Replace / Add 는 고를 수 있게 남긴다 (Q3) |
| Jaw / Lip 축 배율 | 답 없음 → **2단계** (§8) (Q4) |
| 테스트 씬 | **`D:\D__02.Art\D__Asset\D__Character\D__CHN\D__Rig\D__Revision_Rig_0010	mp\JP__CHN_Basic_1070_JALI_test.mb`** (Q5) — §0-B. **원본을 저장 · 덮어쓰지 않는다** (mayapy 에서 열기만, 결과 씬은 scratchpad 로) |

## 0-B. 테스트 씬 구성 (2026-10-19 mayapy 로 읽음)

- Maya 2024 `.mb` 357MB, 시간 단위 **ntsc (30fps)**. 열 때 `internalTimeUnitStringToDisplayFPSString` 오류 2줄은 mayapy 전용 무해.
- **레퍼런스** `C:/Users/USER/Desktop/JP/0030_maya_python_JUN/JUN_JALI/out/jali_arkit_mapping_ctl.ma` → 네임스페이스 **`JALI1:`**
  - `JALI1:JALI_IN` — 사용자 어트리뷰트 20개: `Jaw Lip AHH AAA Eh IEE OHH UUU WWW RRR SSS SSH FFF TTH MBP Schwa LNTD GK WA_PEDAL YA_PEDAL`
  - `JALI1:CNT_PHONEMES`(16) · `JALI1:CNT_COARTIC`(6) · `JALI1:CNT_JaLi`(tx/ty) · `JALI1:ARKIT_OUT`(52)
  - `JALI1:bw_*` blendWeighted **15개** (cheekPuff, jawForward, jawOpen, mouthClose, mouthDimple, mouthFunnel, mouthLowerDown, mouthPress, mouthPucker, mouthRollLower, mouthShrugLower, mouthSmile, mouthStretch, mouthUpperUp, tongueOut)
- 블렌드셰이프 **`CHN_n_Face_xx_bs`** (geo `CHN_n_Face_xx_geoShape`) — ARKit 타겟 **51개(`tongueOut` 없음)**, **51개 전부 이미 구동 중**(ARKIT_OUT 쪽에서).
  → 이 씬에서 Pose Map 을 BS 에 직접 Build 하면 기본 Skip 으로 전부 건너뛴다 — **검증 · 실사용은 `Replace` 로**(또는 Capture 로 지금 결과를 읽어 오기만).
- 레퍼런스 노드(`JALI1:bw_*`)의 weight 수정 · input 연결은 레퍼런스 편집으로 가능 — Blend Weights 탭이 이 씬의 `JALI1:bw_*` 를 바로 다룬다.

## 0. 요청

| # | 요청 | 이 계획의 탭 |
|---|------|-------------|
| R1 | 음소 어트리뷰트가 모여 있는 노드(예: `JALI_IN`)를 고른다 → 음소(`AAA`, `Eh` …)를 고른다 | **Pose Map** |
| R2 | 블렌드셰이프 노드(예: ARKit 52 타겟의 `BS_arkit`)를 고른다 | Pose Map |
| R3 | `AAA` 를 고른 상태에서 그에 맞는 `BS_arkit` 타겟 값을 조정한다 | Pose Map |
| R4 | `JALI_IN.AAA → BS_arkit.<조정한 타겟들>` 관계를 **저장**한다 | Pose Map (json) |
| R5 | 저장한 관계를 **임의의 노드**(같은 음소 어트리뷰트를 가진 노드 → 같은 타겟 어트리뷰트를 가진 노드)에 연결한다 | Pose Map > Connect |
| R6 | `blendWeighted` 에 UI 에서 보이는 weight 를 추가하는 탭 | **Blend Weights** |

---

## 1. 결정 (권장안 — §9 에서 확인)

| ID | 결정 | 권장 | 이유 |
|----|------|------|------|
| D1 | 어디에 만드나 | **새 툴 `A00550_PoseMapper`** (탭 2개: `Pose Map` · `Blend Weights`) | 기능이 JALI 전용이 아니다 — "어트리뷰트 묶음 → 블렌드셰이프 포즈" 는 ARKit → MetaHuman, FACS 컨트롤 → 셰이프 등에도 그대로 쓴다. `A00540` 은 "음성 → 키" 한 가지 일을 유지 |
| D2 | 관계를 씬에 만드는 방식 | **타겟마다 `blendWeighted` 하나 + (선택) `clamp`** | 지금 씬과 같은 노드라 익숙하고, 계산이 `Σ(음소값 × weight)` 로 그대로 드러난다. SDK(animCurve)보다 가중치를 읽고 고치기 쉽다 |
| D3 | 조정(R3) 방식 | **노드망을 실시간으로 고치며 본다** — 음소 하나를 기준값으로 켜고(나머지 0) 슬라이더가 그 음소의 weight 를 바꾼다 | 타겟이 이미 노드망에 연결돼 있어도 바로 보인다. "블렌드셰이프 값을 만졌다가 따로 저장" 하는 2단계가 없다 |
| D4 | 저장 형식 | **json 파일** (`app/libraries/*.json` + 다른 이름으로 저장) | `A00540` 매핑 · `A00145` 규칙과 같은 방식. 파일 하나 = 관계 묶음 하나 |
| D5 | Blend Weights 탭이 "빠진 weight" 를 채울 기본값 | **1.0** | 빠진 weight 는 이미 1.0 으로 계산되고 있다(실측). 1.0 으로 만들어 두면 **결과가 바뀌지 않은 채** UI 에 보이게만 된다 |

---

## 2. 실측으로 정한 사실 (Maya 2024 mayapy, 2026-10-19)

| 사실 | 계획에 주는 영향 |
|------|-----------------|
| `input[5]` 만 연결하면 `weight` 원소 목록(`getAttr bw.weight -mi`)은 `[0]` 뿐 — **`weight[5]` 가 없어서 Node Editor · Attribute Editor 에 안 보인다** | R6 의 원인. 연결할 때 weight 를 같이 만들어야 한다 |
| 없는 weight 는 **1.0 으로 계산된다** (input 0.5 두 개, weight 0.2 / 없음 → 출력 0.6) | 연결만 하고 두면 그 입력이 의도보다 수십 배 세다 (이 씬은 weight 가 0.01~0.1 대) |
| **`getAttr bw.weight[5]` 를 부르기만 해도 원소가 생긴다** | 검사 코드는 원소 값을 읽기 전에 `-mi` 목록만 보고 판단해야 한다. 안 그러면 검사가 상태를 바꾼다 |
| blendShape 타겟 이름 = `aliasAttr -q` 의 별칭 (`['jawOpen', 'weight[0]']`) | 타겟 목록은 별칭으로 보여 주고, 연결은 `BS.<별칭>` 으로 한다 |
| 지금 씬(`jali_arkit_mapping_ctl.ma`)은 `JALI_IN → bw_<타겟> → md_<타겟>(× Jaw/9 또는 Lip/9) → cl_<타겟> → ARKIT_OUT` | §3.6 "Capture" 로 이 노드망의 결과를 그대로 읽어 올 수 있다 (노드망 구조를 몰라도) |

---

## 3. 탭 1 — Pose Map

### 3.1 개념

**포즈** = "음소 하나를 기준값으로 올렸을 때 각 타겟이 가질 값".

```
타겟 t 의 값 = clamp( Σ_음소 p  ( p 의 현재값 / 기준값 ) × 포즈[p][t] , 0, 1 )
```

- 기준값(ref) 기본 **10** — VisemeNet · A00540 이 음소를 0~10 으로 키한다. 노드에 max 가 있으면 그 값도 고를 수 있다.
- 씬에서는 타겟마다 `blendWeighted` 하나: `input[i]` = 음소, `weight[i]` = 포즈[p][t] / ref. 출력 → (clamp) → 타겟.
- 결과 예: `AAA = 10` 이면 `jawOpen` = 포즈[AAA][jawOpen].

### 3.2 화면

```
┌ Pose Mapper v01.00 ──────────────────────────────────────────────────────┐
│ [ Pose Map ] [ Blend Weights ]                                           │
│ ┌ Source (phonemes) ────────────┐ ┌ Target (blendShape / any node) ────┐ │
│ │ Node [JALI_IN      ] [<< Sel] │ │ Node [BS_arkit     ] [<< Sel]       │ │
│ │ Ref value [10.0]              │ │ Filter [mouth____]  [x] Used only   │ │
│ │ ┌───────────────────────────┐ │ │ ┌─────────────────────────────────┐ │ │
│ │ │ AAA     4 targets         │ │ │ │ jawOpen        [====|    ] 0.67 │ │ │
│ │ │ Eh      3 targets         │ │ │ │ mouthLowerDown [===|     ] 0.54 │ │ │
│ │ │ AHH     2 targets   ◀ sel │ │ │ │ mouthDimpleL   [==|      ] 0.50 │ │ │
│ │ │ ...                       │ │ │ │ ... (52)                         │ │ │
│ │ └───────────────────────────┘ │ │ └─────────────────────────────────┘ │ │
│ │ [x] Solo preview              │ │ [Zero Pose] [Capture] [Mirror L/R]  │ │
│ └───────────────────────────────┘ └─────────────────────────────────────┘ │
│ Library [jali_arkit_v01 ▼] [Load] [Save] [Save As...]   [x] Clamp 0-1    │
│ [ Build / Update Network ]   [ Connect To... ]   [ Remove Network ]     │
│ Log                                                                      │
└──────────────────────────────────────────────────────────────────────────┘
```

### 3.3 동작

| 단계 | 동작 |
|------|------|
| **Source** (R1) | 노드를 고르면(선택 → `<< Sel`) **숫자형 · keyable 사용자 어트리뷰트**를 음소 목록에 띄운다. 이미 연결이 있는 것도 보이되 표시. 목록 체크로 다룰 음소를 고른다(기본 전부). 각 줄에 "포즈에 들어간 타겟 수" |
| **Target** (R2) | blendShape 면 **타겟 별칭** 52개, 일반 노드(예: `ARKIT_OUT`)면 숫자형 사용자 어트리뷰트. `Filter`(공용 `JUN_mod_filter_qt`) · `Used only`(지금 음소에서 0 이 아닌 타겟만) |
| **음소 선택 + 조정** (R3) | 음소를 고르면 오른쪽 슬라이더가 **그 음소의 포즈 값**(0~1)을 보여 준다. 슬라이더를 움직이면 포즈 값이 바뀌고, 노드망이 있으면 해당 `weight[i]` 를 **바로** 고친다 |
| **Solo preview** | 켜면 고른 음소 = ref, 다른 음소 = 0 으로 둔다(키가 있으면 키를 건드리지 않게 **임시 값 + 끌 때 원복**). 음소를 바꾸면 따라 바뀐다. 창을 닫거나 탭을 떠나면 원복 |
| **Zero Pose / Mirror L/R** | 지금 음소의 포즈를 0 으로 / `...Left` 값을 `...Right` 로 복사 (ARKit 좌우 쌍) |
| **Capture** | **씬의 현재 결과를 포즈로 읽어 온다**: 음소 하나씩 ref, 나머지 0 으로 두고 타겟 값을 읽는다. 기존 노드망이 무엇이든(지금 씬의 bw → md → clamp 포함) 그 결과가 포즈가 된다 → 옛 노드망에서 이 툴로 넘어올 때 쓴다 |
| **Save / Load** (R4) | 포즈 묶음을 json 으로 (§3.4) |
| **Build / Update Network** | Source → Target 에 노드망 생성. 이미 이 툴이 만든 노드망이면 **weight 만 갱신**(노드 재생성 없음) |
| **Connect To...** (R5) | 저장한 라이브러리를 **다른 노드 쌍**에 연결하는 대화상자 (§3.5) |
| **Remove Network** | 이 툴이 만든 노드만 지운다(태그로 찾는다, §3.6) |

### 3.4 라이브러리 json

```json
{
  "format": "jun.posemap/1",
  "name": "jali_arkit_v01",
  "description": "JALI phonemes -> ARKit 52, tuned on jali_arkit_mapping_ctl.ma",
  "ref_value": 10.0,
  "clamp": true,
  "source_attrs": ["AAA", "Eh", "AHH", "OHH", "UUU", "IEE", "RRR", "WWW", "SSS", "FFF", "TTH", "MBP", "SSH", "Schwa", "GK", "LNTD"],
  "poses": {
    "AHH": {"jawOpen": 1.0, "mouthLowerDownLeft": 0.34, "mouthLowerDownRight": 0.34},
    "MBP": {"mouthClose": 0.62, "jawOpen": 0.43, "cheekPuff": 0.1}
  }
}
```

- **이름만 저장한다**(`JALI_IN` · `BS_arkit` 같은 노드 이름은 넣지 않는다) — 그래서 임의의 노드에 연결할 수 있다.
- 0 인 값은 저장하지 않는다(희소).
- 0040 표를 그대로 옮긴 `jali_arkit_0040_default.json` 을 기본 라이브러리로 같이 넣는다.

### 3.5 Connect To... (R5)

```
┌ Connect Library ─────────────────────────────────┐
│ Library  jali_arkit_v01                          │
│ Source   [angela:JALI_IN    ] [<< Sel]           │
│ Target   [avatar:BS_face    ] [<< Sel]           │
│ Prefix   [avatarA_]                              │
│ Existing incoming connection on a target:        │
│   (•) Skip   ( ) Replace   ( ) Add (sum)         │
│ ┌ Preview ───────────────────────────────────────┐│
│ │ 16 / 16 source attrs found                     ││
│ │ 49 / 52 targets found  (missing: tongueOut...) ││
│ │ 2 targets already driven -> skipped            ││
│ └────────────────────────────────────────────────┘│
│                          [Connect]  [Cancel]     │
└──────────────────────────────────────────────────┘
```

- **이름 대조**: source 어트리뷰트와 타겟 이름은 정확히 같은 이름으로 찾는다. blendShape 면 별칭 기준.
  (옵션) 공용 `attr_match`(A00145 의 이름 유사 매칭)로 "비슷한 이름" 후보 — 2단계.
- 없는 이름은 **건너뛰고 목록을 보여 준다**(연결 전 Preview 에서 이미 보인다).
- 이미 다른 것이 연결된 타겟: `Skip`(기본) / `Replace`(끊고 연결) / `Add`(기존 소스를 bw 의 입력 하나로 넣어 합산).
- 같은 라이브러리를 여러 쌍에 연결할 수 있게 노드 이름에 `Prefix` 를 붙인다.
- 전체가 **Undo 한 번**.

### 3.6 씬에 만드는 노드와 태그

```
<prefix>pm_bw_<target>  (blendWeighted)  input[i] <- <source>.<phoneme>,  weight[i] = pose / ref
<prefix>pm_cl_<target>  (clamp, 옵션)     -> <target node>.<target>
<prefix>pm_NET          (network 노드)    message 로 위 노드들을 묶고, 라이브러리 이름 · source · target · ref 를 문자열 어트리뷰트로
```

- **weight 는 항상 input 과 같이 만든다** — R6 의 문제를 이 탭에서는 아예 만들지 않는다.
- Update / Remove 는 `pm_NET` 을 따라가 찾는다(이름 규칙에 기대지 않는다 — 사용자가 노드 이름을 바꿔도 동작).
- 입력이 0 개가 된 타겟의 bw 는 지운다.

### 3.7 코어 구성 (`app/core`, UI 비의존)

| 파일 | 함수 |
|------|------|
| `attrs.py` | `numeric_user_attrs(node)`, `blendshape_targets(bs)`(별칭), `target_attrs(node)` |
| `library.py` | `PoseLibrary`(poses 사전 + ref · clamp), `load/save/list`, `set_value(phoneme, target, v)` |
| `network.py` | `build(lib, source, target, prefix, on_existing)`, `update_weight(net, phoneme, target, v)`, `remove(net)`, `find_networks()`, `read_library(net)` |
| `capture.py` | `capture(source, phonemes, target, targets, ref)` → 포즈 (음소 하나씩 ref, 나머지 0, 값 읽기, **원래 값 · 키 원복**) |
| `preview.py` | `SoloPreview` (켜기 · 음소 바꾸기 · 원복) |

---

## 4. 탭 2 — Blend Weights (R6)

### 4.1 화면

```
┌ [ Pose Map ] [ Blend Weights ] ──────────────────────────────────┐
│ Nodes  [ bw_mouthFunnel ▼ ] [<< Sel] [Refresh]   Filter [bw_m__] │
│ ┌ idx │ input (source plug)   │ weight │ input × weight │ state ┐│
│ │  0  │ JALI_IN.UUU           │ 0.026  │ 0.000          │  OK   ││
│ │  1  │ JALI_IN.RRR           │ 0.042  │ 0.000          │  OK   ││
│ │  5  │ JALI_IN.OHH           │ (1.0)  │ 0.000          │ ⚠ no weight element ││
│ └──────────────────────────────────────────────────────────────┘│
│ output 0.000                                                      │
│ Add input: Source [JALI_IN.____ ▼] [<< Sel attr]  Weight [0.03] [Add] │
│ [Create Missing Weights (1.0)]  [Remove Selected]  [Select Source] │
│ Log                                                               │
└───────────────────────────────────────────────────────────────────┘
```

### 4.2 동작

| 기능 | 하는 일 |
|------|--------|
| **목록** | 씬의 `blendWeighted` 콤보(필터) 또는 선택에서. 표 = input 원소 · weight 원소의 **합집합**, 인덱스 순 |
| **state** | `OK` / **`no weight element`**(input 만 있음 → 1.0 으로 계산 중, 빨강) / `no input`(weight 만 남음, 회색) |
| **weight 편집** | 표에서 바로 숫자 입력 → `setAttr weight[i]` (원소가 생겨 Node Editor 에 보인다) |
| **Add** | Source plug(선택 노드 + 어트리뷰트 콤보, 또는 직접 입력) → **다음 빈 인덱스**에 `connectAttr` + **같은 인덱스 weight 를 바로 setAttr** |
| **Create Missing Weights** | `no weight element` 인 인덱스마다 `weight[i] = 1.0` — 결과는 그대로, UI 에 보이게만 (D5) |
| **Remove Selected** | `removeMultiInstance input[i]` + `weight[i]` (`-b true`) 둘 다 |
| **Select Source** | 고른 줄의 입력 노드 선택 |
| 갱신 | 탭을 열 때 · `Refresh` · 노드 바꿀 때. (scriptJob 자동 갱신은 2단계) |

- **검사는 `getAttr -mi` 로만** 한다 — `weight[i]` 를 `getAttr` 로 읽으면 원소가 생겨 "빠진 weight" 가 검사만으로 사라진다(§2). 값은 원소가 있는 인덱스만 읽는다.
- 모든 변경 Undo 한 번(`undo_chunk`).

### 4.3 코어 (`app/core/blend_weights.py`)

`list_nodes(filter)`, `rows(bw)` → `[(idx, source_plug|None, weight|None, has_weight_elem)]`,
`add_input(bw, plug, weight)`, `set_weight(bw, idx, v)`, `create_missing(bw, value=1.0)`, `remove(bw, idxs)`.

---

## 5. 폴더 구조

```
JUN_All/tools/A00550_PoseMapper/
├── __init__.py · launch.py · __dragDrop_A00550.py
├── app/config/version.py
├── app/core/{attrs.py, library.py, network.py, capture.py, preview.py, blend_weights.py}
├── app/libraries/jali_arkit_0040_default.json
├── app/ui/{main_window.py, pose_map_tab.py, blend_weights_tab.py, connect_dialog.py}
└── icon/A00550_PoseMapper.{svg,png}
JUN_All/docs/A00550_PoseMapper.md
```

공용: `JUN_mod_tsl_qt`(음소 목록) · `JUN_mod_filter_qt`(타겟 필터) · `JUN_mod_log_qt` · `JUN_mod_menuBar_qt` · `maya_undo.undo_chunk`.

---

## 6. 검증 계획

**mayapy 헤드리스** (실측 씬 2개 + 합성 씬):

| # | 확인 |
|---|------|
| P1 | `jali_arkit_mapping_ctl.ma` 에서 **Capture** → 포즈가 0040 표 값과 같다(음소=10, JaLi=9 기준; 예 AHH → jawOpen 1.0) |
| P2 | 합성 씬(`JALI_IN` + 52 타겟 `BS_arkit`)에 **Build** → `AAA=10` 일 때 타겟 값 = 포즈 값, 두 음소 합산 · clamp |
| P3 | 슬라이더 = `update_weight` → 노드 재생성 없이 weight 만 바뀜 |
| P4 | Save → 새 씬 · 다른 이름 노드(`avatar:JALI_IN` → `avatar:BS_face`)에 **Connect** → 같은 결과. 없는 타겟은 건너뛰고 보고 |
| P5 | Existing: Skip / Replace / Add 각각 |
| P6 | Solo preview 켜고 끄면 원래 값 · 키 그대로 |
| P7 | Remove Network → 태그 노드만 삭제, Undo 한 번에 원복 |
| B1 | input 만 연결된 인덱스 → `no weight element` 로 표시되고 **검사 후에도 원소가 생기지 않는다** |
| B2 | Create Missing Weights → 출력 값 그대로, 원소 생김 |
| B3 | Add → 다음 인덱스 + weight 같이 / Remove → input · weight 둘 다 제거 |
| U  | 오프스크린 UI: 노드 고르기 · 음소 선택 · 슬라이더 → 씬 반영 · 표 갱신 |

**사용자 GUI 확인**: 실제 얼굴로 Solo preview 하며 슬라이더 조정, Node Editor 에서 weight 가 보이는지.

---

## 7. 작업 순서

| 순서 | 작업 | 완료 기준 |
|------|------|----------|
| 1 | §9 답 받기 | D1~D5 확정 |
| 2 | `blend_weights.py` + Blend Weights 탭 (작고 독립적, 지금 바로 쓸모) | B1~B3 + UI |
| 3 | Pose Map 코어: `attrs` · `library` · `network` | P2 · P3 · P7 |
| 4 | `capture` · `preview` + 0040 기본 라이브러리 | P1 · P6 |
| 5 | Pose Map 탭 UI + Connect 대화상자 | P4 · P5 · U |
| 6 | 드롭 설치 · 아이콘 · `docs/A00550_PoseMapper.md` · WORKLOG · README · 포트폴리오 | — |

Blend Weights 를 먼저 하는 이유: 지금 막힌 문제(R6)를 바로 풀고, Pose Map 의 노드망 코드와 같은 함수(`add_input` · `set_weight`)를 공유한다.

---

## 8. 범위 밖 (2단계 후보)

- JALI **Jaw / Lip 축 배율**(지금 씬의 `md_<타겟>` = × Jaw/9 · Lip/9)을 Pose Map 노드망에도 넣기 — 타겟마다 "Jaw / Lip / 없음" 을 고르는 열.
- 이름이 다른 타겟 자동 대응(`A00145` 의 이름 유사 매칭).
- 음소 2개 조합 포즈(코렉티브) · 비선형(SDK 커브) 응답.
- scriptJob 으로 Blend Weights 표 자동 갱신.

---

## 9. 정해 줄 것

| # | 질문 | 권장 / 기본값 |
|---|------|--------------|
| Q1 | **새 툴 `A00550_PoseMapper`** 로 만들까, `A00540_JaliLipSync` 의 탭으로 넣을까 | ✅ 새 툴 |
| Q2 | 기준값(ref) 기본 **10** 으로 괜찮나 (음소 = 10 일 때의 포즈) | ✅ 기본 10 + 사용자 실수 입력 |
| Q3 | 연결 대상에 이미 연결이 있을 때 기본 동작 | ✅ Skip |
| Q4 | **Jaw / Lip 축 배율**을 1단계에 넣을까 (지금 씬은 이것까지 하고 있다) | 답 없음 → 2단계 |
| Q5 | 실제로 튜닝할 **ARKit 아바타 씬**이 있나 (`BS_arkit` 를 가진 메시) | ✅ §0-B 테스트 씬 |

---

## 10. 진행 기록 (중단 복구용 — 항목을 끝낼 때마다 체크하고 커밋)

이어서 할 때: `git log --oneline -- JUN_All/tools/A00550_PoseMapper` 로 마지막 커밋을 보고, 아래 첫 미완료 항목부터.
검증 스크립트는 `JUN_All/tools/A00550_PoseMapper/tests/` 에 둔다(mayapy 로 실행, 테스트 씬은 열기만).

- [x] 1. 툴 골격: `__init__` · `launch.py` · `__dragDrop_A00550.py` · `app/config/version.py` (A00540 에서 이름만 바꿔 복제)
- [x] 2. `app/core/blend_weights.py` + `tests/test_blend_weights.py` (B1~B3, 합성 씬 + 테스트 씬 `JALI1:bw_mouthFunnel`) — 13/13. 테스트 씬에 실제로 `JALI1:bw_mouthFunnel` `[5] OHH` 가 weight 원소 없이 저장돼 있다(사용자가 겪은 상태)
- [x] 3. `app/ui/blend_weights_tab.py` + `main_window.py`(탭 2개 틀) — 오프스크린 UI 확인 (`tests/test_ui_blend_weights.py` 10/10, 테스트 씬). Pose Map 탭이 없으면 main_window 가 자리표시 라벨을 넣는다
- [x] 4. `app/core/attrs.py` · `library.py` · `network.py` + `tests/test_network.py` (P2 · P3 · P4 · P5 · P7, ref 2.5 포함) — 20/20. 핵심 API: `network.build(lib, src, tgt, prefix, on_existing)` → (net, report), `network.sync(net, lib, on_existing, only_targets)`(슬라이더는 only_targets=[t]), `network.remove(net)`, `network.read_library(net)`. weight 는 float32 라 되읽은 값은 소수 4자리까지
- [x] 5. `app/core/capture.py`(`preview.py` 는 만들지 않고 `capture.PhonemeDriver` 로 합침 — solo / all_zero / restore) + `app/libraries/jali_arkit_0040_default.json`(JUN_JALI `examples/build_jali_arkit_node.py` 의 MAPPING 을 ast 로 읽어 좌우 펼침) + `tests/test_capture.py` 12/12. 음소 plug 가 연결돼 있으면 값을 넣을 수 있는 위쪽 plug 로 올라간다(테스트 씬: `JALI1:JALI_IN.AAA` → `JALI1:CNT_PHONEMES.AAA`). ref 가 그 plug 의 max 를 넘으면 CaptureError. Capture = (음소 ref, 나머지 0) − (전부 0)
- [x] 6. `app/ui/pose_map_tab.py` + `connect_dialog.py` (P4 · P5 · U — Skip 기본, 테스트 씬은 Replace 로) — `tests/test_ui_pose_map.py` 19/19 (테스트 씬: Capture · Used only · Solo · Build(Replace) · 슬라이더 실시간 · ref 5 / 7.25 · 음소 전환 · 원복 · 저장 · Connect 다른 쌍 · Remove · 기본 라이브러리 Load). 계획 대비 추가: 음소 목록에 **체크박스** — 체크 = 음소(Solo · Capture 대상), 기본으로 `Jaw` · `Lip` 해제(같은 노드의 배율 입력을 0 으로 만들면 출력 전체가 0)
- [ ] 7. 아이콘 · `docs/A00550_PoseMapper.md` · WORKLOG · README(툴 69 / 현행 54) · 포트폴리오 · 메모리 · 이 계획서 상태 갱신
