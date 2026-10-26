# A00580_FacialBoardBuilder — ARKit 52 페이셜 컨트롤 보드 빌더 (사용 안내)

ARKit 52 블렌드셰이프 값을 애니메이터가 **컨트롤러로** 다루는 2D 보드(`Ctl_Only_V05`)를 **명세 json 하나**에서 만든다.
손으로 만들지 않는다 — 자리 · 이름 · 범위를 바꾸려면 json 을 고치고 다시 돌린다. 같은 json 으로 뒤에 Unreal Control Rig
보드를 만들 계획이라(2단계) Maya 와 UE 의 UI 가 같아진다. 계획 · 결정 · 실측은
[`plans/Facial_ARKit52_Ctl_V05_plan.md`](plans/Facial_ARKit52_Ctl_V05_plan.md).

- **버전**: v01.00 (2026-10-26) — 헤드리스 패키지(`launch.py` 없음). 빌드 · 검증은 mayapy, 베이크 · 재연결은 Maya 안에서 함수로.
- **산출물**: `0035_maya_src_rig\01_Module_01_Facial\Ctl_Only_V05.ma` · `.mb` · `Ctl_Only_V05_board.png`(미리보기). V04 는 그대로 둔다.
- **전례**: JUN_JALI `examples/build_jali_slider_ctl.py`(명세 → 리그 → 검증, `bake_ctl_keys`).

---

## 1. 보드 한눈에

```
CTRL_<L|R|C>_<region>_<motion>   35 개 (연결 33 + 예비 2)  →  BS_Face_Connect_01 (attr 52)     # 앞으로 : 늘 켜져 있다
BS_Face_CSV (blendShape, 별칭 52)  →  컨트롤 tx / ty                                            # 뒤로   : CSV 를 받을 때만
```

| 종류 | 축 | 범위 | 예 |
|------|----|------|----|
| 슬라이더 0~1 | ty | `[0, 1]` (끌어내리는 표현은 `[-1, 0]`) | `CTRL_L_brow_raiseOut`, `CTRL_L_brow_down`(−ty = browDownLeft) |
| 슬라이더 ±1 | ty | `[-1, 1]` — 반대 표현 둘 | `CTRL_L_eye_blinkWide`(−blink / +wide), `CTRL_C_mouth_upperLip`(+shrug / −roll) |
| 좌우 슬라이더 | tx | `[-1, 1]` | `CTRL_C_mouth_move`(+ mouthLeft / − mouthRight) |
| 2D 패드 | tx · ty | `[-1, 1]` (턱은 ty `[-1, 0]`) | `CTRL_L_eye`(look), `CTRL_L_mouth_corner`(smile/frown · stretch/dimple), `CTRL_C_jaw` |

- 값은 늘 −1 ~ 1 / 0 ~ 1 이고 **`transformLimits` 가 손 조작과 연결값 둘 다 자른다**(실측). 값 1 이 보드에서 몇 cm 움직이는지는
  `board.unit`(0.8) 이 정한다 — 컨트롤을 담은 `FRM_<ctl>` 의 scale 이다.
- 보드를 마주보는 사람 기준 **오른쪽이 캐릭터 Left**(`CTRL_L_*`, 빨강). R 은 파랑, 중앙 C 는 노랑, **연결 안 된 예비 컨트롤은 회색**
  (`CTRL_L/R_cheek_puff` — 지금은 `CTRL_C_cheek_puff` 하나가 `cheekPuff` 를 맡는다, 사용자 결정).
- 부위: 눈썹 5 · 눈 6 · 광대 3(+예비 2) · 코 2 · 입 14 · 턱 2 · 혀 1. 52 attr → 컨트롤 매핑표는 계획서 §2-1.
- 루트 `CTRL_faceGUI`: 보드 이동 · **`Head` / `Global` / `World`** 가중치(0~1) · `boardSpec`(명세 json 전체, 잠김) · `boardVersion`.
  `GRP_faceGUI` 가 `FOLLOW_Head_loc` / `FOLLOW_Global_loc` / `FOLLOW_World_loc`(`GRP_faceGUI_follow` 아래) 에 parentConstraint 되어 있고
  가중치가 그 attr 을 따른다. **Head 로케이터를 머리 조인트에, Global 을 아바타 루트 본에 constraint 하면** 보드가 그것을 따라간다
  (World 는 어디에도 붙이지 않는다). 기본 Head 1.

### 더미 노드 (V04 와 이름 · 어트리뷰트 · 순서가 같다 — 바꾸지 말 것)

| 노드 | 역할 |
|------|------|
| `BS_Face_CSV` | blendShape, weight 별칭 52 (인덱스 0 = eyeBlinkLeft … 51 = mouthDimpleRight, V04 실측과 같음). **A00480 FileTool `Import > CSV` 가 별칭 이름으로 키를 넣는 자리** |
| `BS_Face_CSV_geo` | 숨긴 4점 평면. **지오메트리 없는 blendShape 는 연결된 애님커브 · 노드를 지우거나 `cutKey` 만 해도 Maya 가 노드째 지운다**(실측) — 이 평면이 그것을 막는다. V04 의 글자 메시(`FaicalMesh_geo`)가 하던 역할. 건드리지 말 것 |
| `BS_Face_Connect_01` | transform, attr 52 (ARKit 순서). 컨트롤이 늘 이 값을 민다 → A00145 RigConnect `Apple ARKit 52 Facial Target` 규칙으로 블렌드셰이프 · 다른 노드에 연결 |

---

## 2. 사용 흐름 (Maya 안)

```python
from tools.A00580_FacialBoardBuilder import bake
bake.csv_connected()        # 뒤로 경로가 걸려 있나
bake.bake_csv_to_ctl()      # CSV 키 -> 컨트롤러 tx/ty 키, 뒤로 경로 떼기
bake.reconnect_csv()        # 다음 CSV 를 받기 전에 뒤로 경로 다시 걸기 (키가 남은 축은 건너뛴다)
bake.clear_ctl_keys()       # 컨트롤러 키 지우기 (그 뒤 reconnect_csv)
bake.disconnect_csv()       # 키 없이 그냥 떼기
```

1. `Ctl_Only_V05.mb` 를 열거나 레퍼런스한다 (네임스페이스 OK — 함수가 루트의 네임스페이스를 따른다).
2. **A00480 FileTool › Import › CSV** 로 `BS_Face_CSV` 에 키를 넣는다 → 컨트롤러가 따라 움직인다.
3. `bake.bake_csv_to_ctl()` — 0~1 직결 축은 커브를 **통째 복사**(키 수 · 탄젠트 그대로), ± 축은 두 커브 키 시각의 합집합마다
   `a₊ − a₋` 를 키로(자동 탄젠트), 커브가 없는 축은 지금 값 하나. 뒤로 경로가 떼어지고 **키는 컨트롤러에 남는다**.
4. 손 애니 · 클린업. `BS_Face_Connect_01` 은 늘 컨트롤러를 따른다.
5. 다음 CSV 전에 `bake.clear_ctl_keys()` → `bake.reconnect_csv()`.

> ± 한 축으로 합쳐진 표현(blink/wide, shrug/roll, smile/frown, stretch/dimple, mouthLeft/Right, jawLeft/Right, eyeLook 4 방향)은
> CSV 에서 **둘이 같은 프레임에 함께 켜져 있던 값이 합(차)으로만** 남는다. ARKit 캡처에서 반대 표현이 동시에 뜨는 일은 드물지만
> 0 이 되는 것은 아니다 — 계획서 M0-4.

---

## 3. 빌드 · 검증 · 미리보기 (mayapy / python)

```
mayapy build.py   [spec.json] <out.ma> [--mb]                    # 새 씬에 만들어 저장 (.mb 도)
mayapy verify.py  <board.ma> [--v04 Ctl_Only_V04.mb]            # T1~T8 (같은 이름 .mb 가 있으면 왕복까지)
python preview.py [spec.json] <out.png>                          # PIL, Maya 없이 자리 확인
python migrate.py                                                # spec/migrate_v04.json 다시 만들기
```

- 명세 `spec/arkit52_board_v05.json` — `board`(unit · 반지름 · 틀 · 라벨 · 기본 위치) · `names` · `colors` · `arkit52` · `csv_alias_order`
  · `controls[]`. L 컨트롤에 `"mirror": true` 만 적으면 R 은 빌더가 만든다(x 반전 · Left→Right · **tx 부호 거울** — 양쪽 다 "바깥으로 끌면 Out").
- `board_spec.check_spec()` 이 52 attr 가 정확히 한 번씩 나오는지 · 리밋과 축 부호가 맞는지 먼저 본다.
- 검증 **1582 항목 통과**(2026-10-26, mayapy 2024): T1 구조 · 더미 이름 · 별칭↔인덱스 = V04 · T2 리밋/잠금 · T3 앞으로(축마다 그 attr 만 1)
  · T4 뒤로 · T5 왕복 + ± 상쇄 + 범위 밖 클램프 · T6 베이크 → 프레임별 출력 동일 → 재연결 · T7 거울 · Head/World 따라가기 · T7b V04 키 →
  이관표 → 동치 · T8 .ma/.mb 왕복 · unknown 0. **실제 Maya GUI 눈 확인 아직.**
- `spec/migrate_v04.json` — V04 `ctl.axis` → V05 `CTRL.axis` + 부호(`v05 = v04 × multiplier`). 한 V05 축으로 모이는 V04 플러그 묶음은
  `merged_v05_plugs`(합으로 옮긴다). A00110 Copy Key · A00145 Connect by Rule 로 옛 애니를 옮길 때 쓴다.

---

## 4. 구조

```
A00580_FacialBoardBuilder/
├── board_spec.py      # 명세 읽기 · 좌우 전개 · 축 해석 · 정합성 (maya 비의존)
├── build.py           # 보드 · 더미 · 앞으로/뒤로 연결 · 저장 (connect_backward / disconnect_backward 는 bake 가 재사용)
├── bake.py            # bake_csv_to_ctl · reconnect_csv · disconnect_csv · clear_ctl_keys (in-Maya)
├── verify.py          # T1 ~ T8
├── preview.py         # png (PIL)
├── migrate.py         # V04 -> V05 이관표
└── spec/              # arkit52_board_v05.json · v04_backward_table.json(실측) · migrate_v04.json(생성)
```

노드 이름 규칙: 컨트롤 `CTRL_<L|R|C>_<region>_<motion>` · 틀 `FRM_<같은 이름>` · 부위 `GRP_<region>GUI` · 앞으로 `FWD_<attr>_neg` / `FWD_<attr>_clamp`
· 뒤로 `BWD_<CTRL>_<axis>`(plusMinusAverage) · 따라가기 `FOLLOW_<Head|Global|World>_loc`.

### 실측으로 정한 것 (mayapy 2024, 2026-10-26)

- `transformLimits` 는 **연결된 입력값도** 자른다 (2.0 → 1.0, −1 → 0). 그래서 뒤로 경로에 clamp 가 없어도 된다.
- 지오메트리 없는 blendShape: 별칭은 저장 왕복에서 살지만 **연결된 노드를 지우면(animCurve delete · `cutKey -clear` · pma delete) 노드째 사라진다**
  → 숨긴 평면에 붙였다. pma 는 입력을 먼저 떼고 지운다(`disconnect_backward_plug`).
- `aliasAttr -q` 의 순서는 저장 뒤 plug 문자열 순(`weight[0]`, `weight[10]` …)으로 바뀐다 — 순서가 아니라 별칭↔인덱스 대응을 비교한다.
- 색(`overrideColorRGB`) · 리밋 · lock/keyable · `textCurves` 는 `.ma` ↔ `.mb` 왕복에서 보존된다.
