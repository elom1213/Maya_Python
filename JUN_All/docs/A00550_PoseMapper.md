# A00550_PoseMapper

음소처럼 **값 하나로 켜지는 어트리뷰트 묶음**(예: JALI 의 `JALI_IN`)을 **블렌드셰이프 타겟 조합(포즈)** 에 연결하는 in-Maya PySide 툴.
음소를 하나 골라 타겟 값을 슬라이더로 정하고, 그 관계를 json 으로 저장해 **아무 노드 쌍에나 다시 연결**한다.
두 번째 탭은 `blendWeighted` 의 **input / weight 편집기** — Node Editor 에서 weight 가 안 보이는 문제를 푼다.

- **버전**: v01.05 (2026-10-19)
- **아키텍처**: (B) in-Maya PySide (`maya.cmds`), 드래그&드롭 셸프 설치
- **계획 · 진행 기록**: `docs/plans/A00550_PoseMapper_plan.md`
- **관련**: `A00540_JaliLipSync`(음성 → JALI 키) · JUN_JALI `docs/0040_jali_arkit_mapping.md`(JALI ↔ ARKit 실측 시작 가중치)

---

## 1. 설치 · 실행

창 크기는 **언제든 드래그로 자유롭게** 바꿀 수 있다(v01.04). 처음 열 때만 내용 크기(화면 작업 영역까지)에 맞추고,
그 뒤로 Save · Build · Capture · 탭 이동이 창 크기를 바꾸지 않는다. 내용보다 작게 줄이면 탭 안에 스크롤바가 생긴다.

`__dragDrop_A00550.py` 를 뷰포트로 드래그&드롭 → 현재 셸프에 `PoseMapper` 버튼. 버튼 = `tools.A00550_PoseMapper.run(True)`.

## 2. Pose Map 탭

```
┌ Source (phonemes) ─────────┐ ┌ Target (blendShape or any node) ────────┐
│ Node [JALI1:JALI_IN] [<<Sel]│ │ Node [CHN_n_Face_xx_bs]       [<< Sel] │
│ Ref value [10.000]          │ │ Filter [mouth__]  [x] Used only         │
│ ☐ Jaw   ☐ Lip              │ │ jawOpen        [=========|  ] 0.800     │
│ ☑ AHH (3)  ◀ 선택           │ │ mouthLowerDownL[===|        ] 0.340     │
│ ☑ AAA (6)  ...              │
│ [Check Sel][Uncheck Sel][Check All] │ │ ...                                     │
│ [x] Solo preview            │ │ [Zero Pose] [Mirror L > R] [Capture]    │
└─────────────────────────────┘ └─────────────────────────────────────────┘
 Library [jali_arkit_0040_default ▼] [Load] [Save] [Save As...] [New] [x] Clamp 0-1
 If target is driven [Skip ▼]  [ Build / Update Network ] [Connect To...] [Remove Network]
```

### 순서

1. **Source** — 음소 어트리뷰트가 모인 노드를 선택하고 `<< Sel`. 숫자형 사용자 어트리뷰트가 목록에 뜬다.
   **여러 개를 한 번에 체크 / 해제 (v01.01)** — Shift / Ctrl 로 여러 줄을 고른 뒤 `Check Sel` / `Uncheck Sel`, 또는 고른 줄 중 하나의
   체크박스를 누르거나 Space(고른 줄 전부가 같이 바뀐다, 공용 `JUN_mod_checkList_qt`). `Check All` 은 토글 — 전부 체크돼 있으면
   `Uncheck All` 로 바뀐다. 체크가 바뀌면 켜져 있던 Solo preview 는 꺼지고 값이 원복된다.
   **체크 = 음소.** `Jaw` · `Lip` 은 기본으로 체크 해제 — Solo preview · Capture 가 체크된 것만 0 / Ref 로 바꾸므로,
   같은 노드에 있는 배율 입력(JALI 의 턱 / 입술)은 건드리지 않는다. 괄호 숫자 = 그 음소의 포즈에 들어간 타겟 수.
2. **Target** — 블렌드셰이프(타겟 별칭) 또는 숫자 어트리뷰트를 가진 아무 노드(예: `ARKIT_OUT`)를 `<< Sel`.
3. **Ref value** — 포즈가 완성되는 음소 값. **기본 10, 아무 실수나**(0.001 ~ 100000). VisemeNet · A00540 은 음소를 0~10 으로 키한다.
4. **음소를 고르고 슬라이더로 타겟 값을 정한다** — "이 음소 = Ref 일 때 이 타겟 = 이 값". 슬라이더는 0~1, 숫자 칸은 −2~2.
   - 노드망이 있으면 **움직이는 즉시 씬에 반영**된다(그 타겟 체인만 갱신, 노드를 다시 만들지 않는다).
   - `Used only` = 지금 음소에서 0 이 아닌 타겟만. `Zero Pose` = 지금 음소 비우기. `Mirror L > R` = `...Left` 값을 `...Right` 로.
5. **Solo preview** — 켜면 고른 음소만 Ref, 다른 음소는 0. 음소를 바꾸면 따라 바뀐다.
   **체크박스를 직접 눌러 끌 때(또는 창을 닫을 때)만 꺼지고 원래 값으로 돌아간다** (v01.03). 슬라이더 · 체크 변경 · 탭 이동 · Ref 변경 ·
   Capture · Build / Remove 중에도 켜진 채 유지되고, Source 를 바꾸면 이전 Source 는 원복하고 새 Source 에 다시 건다.
   목록에서 체크 안 된 줄을 고르면 체크된 음소를 전부 0 으로 둔다.
   음소 어트리뷰트가 다른 노드에 연결돼 있으면(예: `JALI_IN.AAA` ← `CNT_PHONEMES.AAA`) **값을 넣을 수 있는 위쪽 어트리뷰트**를 대신 바꾼다.
   Ref 가 그 어트리뷰트의 max 를 넘으면 `[ERROR] Reference value 15 is above the max 12 of ...`.
6. **Build / Update Network** — 지금 라이브러리대로 노드망을 만든다 / 고친다(§4).
   `If target is driven` = 타겟에 이미 다른 연결이 있을 때 **Skip(기본)** / Replace(끊고 연결) / Add(기존 것을 합산 입력으로 유지).
7. **Save / Save As...** — json 으로 저장(`app/libraries/<이름>.json` 또는 고른 경로). `Load` = 콤보의 라이브러리.
   메뉴 **`Library > Show Libraries Folder`** (v01.02) = 그 `app/libraries` 폴더를 탐색기로 연다(json 복사 · 백업 · 다른 PC 로 옮길 때).

### JaLi — 턱 / 입술 비중을 타겟마다 (v01.05)

v01.04 까지는 Pose Map 노드망이 음소 값만 더해서 **`CNT_JaLi` 가 얼굴에 영향을 주지 않았다**(테스트 씬 실측: JaLi 를 2~15 로 바꿔도
jawOpen · mouthFunnel 그대로). 이제 타겟마다 JaLi 축과 세기를 정한다.

```
타겟 = clamp( Σ(음소/Ref × 포즈) × factor ),   factor = 1 + Strength × (축값 / Neutral − 1)
```

| Strength | 의미 | 예: Jaw 축, Neutral 9, CNT_JaLi Jaw 2 |
|----------|------|-----------------------------------|
| 1 | 원래 JALI 노드망과 같다(축값에 비례) | × 0.222 |
| 0.5 | 절반만 | × 0.611 |
| 0 | JaLi 무시 | × 1 |

1. **Source 박스 아래 `JaLi` 칸** — `Node` 에 JaLi 컨트롤을 `<< Sel`(테스트 씬: `JALI1:CNT_JaLi`). `Jaw` / `Lip` 어트리뷰트는
   라이브러리 이름(기본 `Jaw` / `Lip`)이 있으면 그것, 없으면 `translateX` / `translateY` 를 자동으로 고른다. Source 에 `Jaw` / `Lip` 이 있으면
   (예: `JALI_IN`) 칸이 비어 있을 때 Source 가 들어간다. `Neutral` = 포즈를 만들 때의 JaLi 값(factor 1, 기본 9 = 0040 실측).
2. **Target 표의 `Axis` · `Strength` 열** — 타겟마다(음소와 무관). `-` 면 JaLi 무시. 바꾸면 그 타겟 체인만 바로 갱신.
3. **`JALI Defaults`** — jawOpen · jawForward · tongueOut = Jaw, 포즈가 있는 나머지 = Lip, Strength 1 (원래 JALI 노드망과 같은 출발점).
   **`Clear Axes`** — 전부 `-`.
4. 저장하면 라이브러리 json 의 `"jali"` 에 축 · 세기 · 어트리뷰트 이름 · Neutral 이 들어간다(노드 이름은 안 들어감).
   `Connect To...` 에 `JaLi node` 칸이 있다 — 비우면 Source 에 `Jaw` / `Lip` 이 있을 때 Source. 옛 json(v01.04 이전)은 축 없이 그대로 열린다.
5. **Capture 는 JaLi 를 Neutral 에 두고** — 아니면 그 배율이 포즈에 섞인다(로그 경고). Capture 는 축 · 세기 설정을 그대로 이어받는다.
6. JaLi 노드를 정하지 않은 채 축을 주면 축은 저장되지만 효과가 없다(factor 1) — 로그 경고.

### Capture — 지금 씬의 결과를 포즈로

노드망이 어떤 구조든(예: JUN_JALI 의 `bw → md(× Jaw/9) → clamp → ARKIT_OUT → 블렌드셰이프`) **체크된 음소를 하나씩 Ref 로 올리고
나머지 0 일 때의 타겟 값 − 전부 0 일 때의 값** 을 포즈로 읽는다. 옛 노드망에서 이 툴로 넘어올 때, 손으로 고친 값을 그대로 가져올 때 쓴다.
씬은 원래 값으로 돌아온다.

### Connect To... — 저장한 관계를 다른 노드 쌍에

```
Source [avatar:JALI_IN] [<< Sel]   Target [avatar:BS_face] [<< Sel]
Prefix [avatar_]   Ref value [10.000]
Target already driven: (•) Skip ( ) Replace ( ) Add (sum)
16 / 16 source attributes found
49 / 52 targets found  (missing: tongueOut ...)
2 target(s) already driven -> skip
                                   [Check] [Connect] [Cancel]
```

**이름이 같은 것만** 연결한다(블렌드셰이프는 타겟 별칭). 없는 이름은 미리 보이고 건너뛴다. 전체가 Undo 한 번.

## 3. Blend Weights 탭

`blendWeighted` 의 `input[]` 과 `weight[]` 는 **따로 존재하는 멀티 어트리뷰트**다. Node Editor 에서 `input[5]` 에만 연결하면
`weight[5]` 원소가 없어서 **어디에도 안 보이는데, 계산은 1.0 으로 된다**(실측). 이 탭이 그 상태를 보여 주고 고친다.

| 기능 | 하는 일 |
|------|--------|
| Node 콤보 · `Filter` · `Missing weights only` · `<< Sel` | 씬의 blendWeighted 고르기 (레퍼런스 노드 포함) |
| 표 | Idx · 연결된 소스 · Weight(바로 편집) · Input × Weight · State. **`no weight element (= 1.0)` 는 빨강** |
| `Add` | Source(`node.attr`, `<< Sel Attr` = 선택 노드 + 채널 박스에서 고른 어트리뷰트) 를 **다음 빈 인덱스에 연결하고 weight 를 같이 만든다**. 이미 연결된 소스면 weight 만 바꾼다 |
| `Create Missing Weights (1.0)` | 빠진 weight 를 1.0 으로 만든다 — **결과는 그대로**, Node Editor 에 보이게만 |
| `Remove Selected` | input(연결 포함) 과 weight 를 **둘 다** 지운다 |
| `Select Source` | 고른 줄의 소스 노드 선택 |

`Refresh` 를 누르면 씬 전체에서 weight 가 빠진 노드 수를 로그에 알린다. 모든 편집 Undo 가능.

> ⚠️ 스크립트로 확인할 때 `getAttr bw.weight[5]` 를 **부르기만 해도 원소가 생긴다**(실측). 빠졌는지는 `getAttr bw.weight -mi` 로만 볼 것.

## 4. 씬에 만드는 노드

```
<prefix>pm_bw_<타겟>   blendWeighted   input[i] <- <source>.<음소>, weight[i] = 포즈 / Ref
<prefix>pm_jb_<타겟>   blendTwoAttr    (축이 있을 때) input[0] = 1, input[1] <- ratio, attributesBlender = Strength
<prefix>pm_jm_<타겟>   multDoubleLinear (축이 있을 때) bw.output x jb.output
<prefix>pm_cl_<타겟>   clamp 0~1 (Clamp 0-1 켜면)  -> <target>.<타겟>
<prefix>pm_ratio_Jaw / _Lip  multDoubleLinear  <JaLi 노드>.<축 attr> x (1 / Neutral)   (노드망당 하나씩)
<prefix>pm_NET         network         message 로 source · target · JaLi 노드 · 체인 · ratio 를 묶음,
                                       pmLibrary · pmRef · pmClamp · pmJawAttr · pmLipAttr · pmNeutral
```

- 계산: `타겟 = clamp( Σ (음소값 / Ref) × 포즈[음소][타겟] )`. 예: Ref 10, AHH 포즈 jawOpen 0.8 → AHH = 10 일 때 jawOpen 0.8, AHH = 5 일 때 0.4.
- **weight 는 항상 input 과 같이 만든다** — Blend Weights 탭의 문제가 이 노드망에는 생기지 않는다.
- 같은 Source · Target 쌍을 다시 고르면 기존 `pm_NET` 을 찾아 **그 weight 를 라이브러리로 읽어 온다**(노드 이름을 바꿔도 message 로 따라간다).
- **같은 타겟을 노드망 두 개가 노리면** 나중에 Replace 로 연결한 쪽이 이긴다. 진 쪽 노드망을 고르면 상태 줄에 `[!] N not driving the target`,
  로그에 어느 노드망이 가져갔는지 경고가 뜬다(v01.04) — 그 슬라이더는 얼굴을 움직이지 않는다. 테스트 씬 16:20 저장본이 이 상태다
  (`pm_NET`: `JALI1:JALI_IN` → BS 가 `pm_NET1`: `JALI1:CNT_PHONEMES` → BS 에 밀림).
- `Remove Network` = 이 툴이 만든 노드만 삭제. Replace 로 끊었던 원래 연결은 되살리지 않는다(Undo 로는 돌아온다).
- 기본 라이브러리 `jali_arkit_0040_default` = JUN_JALI 0040 표(angela 리그 실측, 음소 10 · JaLi 9/9 기준). `tongueOut` 0.30 은 임시값.

## 5. 테스트 씬에서 쓰는 법 (`JP__CHN_Basic_1070_JALI_test.mb`)

이 씬은 `jali_arkit_mapping_ctl.ma` 를 `JALI1:` 로 레퍼런스하고, 블렌드셰이프 `CHN_n_Face_xx_bs`(ARKit 51개, `tongueOut` 없음)의
**타겟 51개가 전부 이미 `JALI1:ARKIT_OUT` 쪽에서 구동**된다.

0. (v01.05) JaLi 까지 쓰려면: Source `JALI1:CNT_PHONEMES`, JaLi `Node` = `JALI1:CNT_JaLi`(translateX / Y 자동), CNT_JaLi 를 9, 9 에 두고
   `Capture` → `JALI Defaults` → Replace 로 Build. 실측: CNT_JaLi (2, 9) · (9, 4) · (12, 6) 에서 원래 JALI 노드망과 같은 값.
1. Source `JALI1:JALI_IN`, Target `CHN_n_Face_xx_bs` → `Capture` (지금 노드망 결과가 포즈로 — AHH → jawOpen 1.0 등).
2. `If target is driven` = **Replace** → `Build / Update Network` (기본 Skip 이면 51개 전부 건너뛴다).
3. 음소를 고르고 `Solo preview` 를 켠 채 슬라이더로 다듬는다 → `Save As...`.
4. 지금 노드망(`JALI1:bw_*`)을 그대로 쓰고 싶으면 Pose Map 대신 **Blend Weights** 탭에서 weight 만 고쳐도 된다
   (이 씬의 `JALI1:bw_mouthFunnel` `[5] OHH` 는 weight 원소 없이 저장돼 있다 → 빨강 표시 → `Create Missing Weights` 또는 값 입력).
   주의: 이 노드망은 `md_<타겟>`(× Jaw/9 또는 Lip/9) 을 거치므로 weight = (원하는 값 ÷ 10) 이 JaLi 9/9 기준이다.

## 5-1. 자주 묻는 질문

### Q. AAA 를 고치고 싶으면 AAA 를 선택만 하면 되나, 아니면 다른 어트리뷰트를 다 체크 해제하고 AAA 만 체크해야 하나? (2026-10-19)

**AAA 줄을 클릭해서 고르기만 하면 된다.** 다른 어트리뷰트의 체크는 풀지 않는다.

Source 목록의 **고르기(줄 클릭)** 와 **체크(체크박스)** 는 하는 일이 다르다.

| | 하는 일 |
|---|---|
| **고르기** (줄 클릭) | 오른쪽 Target 슬라이더가 **고른 음소의 포즈**를 보여 주고, 슬라이더는 **그 음소만** 고친다. Solo preview 가 켜져 있으면 그 음소가 Ref 로 켜진다 |
| **체크** (체크박스) | 그 어트리뷰트를 **"음소로 다룰지"** 만 정한다 — Solo preview · Capture 가 **체크된 것만** 0 / Ref 로 바꾼다. 슬라이더가 무엇을 고치는지와는 무관 |

**AAA 를 고치는 순서**

1. Source 목록에서 `AAA` 줄을 클릭한다.
2. `Solo preview` 를 켠다 → AAA 만 Ref, **체크된** 다른 음소는 0 → 얼굴에 AAA 모양만 보인다.
3. 오른쪽 슬라이더로 타겟 값을 조정한다 → AAA 포즈에만 반영된다.
4. 다른 음소로 넘어가려면 그 줄을 클릭한다(Solo 는 켜진 채 따라 바뀐다).

**다른 음소의 체크를 풀면 오히려 안 좋은 이유** — Solo preview 는 체크된 음소만 0 으로 만든다. 다른 음소를 체크 해제하면
그 값이 **지금 값(키가 있으면 그 프레임 값) 그대로 남아** AAA 모양에 섞여 보인다. 체크를 풀어야 하는 것은 `Jaw` · `Lip` 처럼
**음소가 아닌 배율 입력**뿐이다(툴이 기본으로 풀어 둔다).

**여러 줄을 골랐을 때** — Shift / Ctrl 로 여러 줄을 골라도 슬라이더가 고치는 것은 **마지막에 클릭한 한 줄**(목록에 테두리로 표시)이다.
여러 줄 선택은 체크 / 해제를 한 번에 하기 위한 기능이다(`Check Sel` / `Uncheck Sel`).

## 6. 구조 (개발자용)

```
A00550_PoseMapper/
├── __init__.py · launch.py · __dragDrop_A00550.py
├── app/config/version.py
├── app/core/
│   ├── blend_weights.py   rows · missing_weights(-mi 만 봄) · add_input(weight 같이) · create_missing · remove
│   ├── attrs.py           numeric_user_attrs · blendshape_targets(별칭) · incoming
│   ├── library.py         PoseLibrary(희소 poses · ref · clamp · jali 축 / 세기 / neutral) · load / save json (jun.posemap/1)
│   ├── network.py         build(jali_node) · sync(only_targets) · set_jali · chain_axis · detached · remove · read_library
│   └── capture.py         settable_plug(위쪽으로 최대 4단계) · PhonemeDriver(solo / restore) · capture
├── app/libraries/jali_arkit_0040_default.json
├── app/ui/{main_window.py, pose_map_tab.py, connect_dialog.py, blend_weights_tab.py}
├── icon/A00550_PoseMapper.svg / .png
└── tests/  (mayapy 로 실행, 테스트 씬은 열기만)
    test_blend_weights.py 13 · test_network.py 20 · test_capture.py 12 · test_ui_blend_weights.py 10 · test_ui_pose_map.py 19 ·
    test_ui_checks.py 12 (v01.01, 합성 씬 · QTest 클릭) · test_ui_solo.py 15 (v01.03, Solo 유지 경로 전부) ·
    test_ui_size.py 8 (v01.04, 자유 리사이즈 · 명령 뒤 크기 유지) · test_jali.py 24 · test_ui_jali.py 14 (v01.05).
    테스트 씬을 쓰는 시험은 `scene_fixture.py` 로
    이 툴의 노드망을 지우고 원래 배선(ARKIT_OUT → BS)으로 되돌린 뒤 돈다(메모리 안에서만 — 사용자가 씬을 다시 저장해도 같은 출발점)
```

**확인 기록 (2026-10-19, mayapy 2024 + 테스트 씬)**: 위 시험 전부 통과(v01.05 기준 147항목). **마야 GUI 에서 드롭 설치 · 실제 얼굴로 Solo preview 하며 조정은 사용자 확인 전.**
2단계 후보(계획서 §8): 이름이 다른 타겟 자동 대응, 코렉티브(음소 2개 조합), Blend Weights 자동 갱신(scriptJob).
