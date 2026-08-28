# A00130_ControlRig_V02 — Control Rig Tool (사용 안내)

`A00130_ControlRig` 의 **템플릿 조인트 패러다임 재작성판**이다. mgear 의 *Guide Template
Manager* · AdvancedSkeleton 의 *FitSkeleton* 처럼 — **씬에 템플릿 조인트를 놓고 눈으로 맞춘 뒤,
버튼으로 컨트롤러(cage)를 그 자리에 굽는다.**

- 버전: `v02.00` (`app/config/version.py`) — **Phase 1 (최소 기능 : Match)**
- 위치: `JUN_All/tools/A00130_ControlRig_V02`
- 형태: 아키텍처 (B) — Maya 내 PySide 툴
- 계획서: [A00130_ControlRig_V02 제작 계획서](plans/A00130_ControlRig_V02_plan.md)
- **`A00130_ControlRig`(V01)은 그대로 둔다** — 케이지 구조가 달라 호환되지 않는다.

> **지금은 Phase 1 이다.** 계획서의 6단계 중 **Match** 와 그 전제인 **템플릿 조인트 생성**만
> 들어 있다. Mirror · IK 세션 · Orient · Validate 는 다음 단계다(§6).

---

## 1. 설치 / 실행

### 드래그&드롭 설치
`__dragDrop_A00130_V02.py` 를 Maya 뷰포트로 드래그&드롭 → 현재 셸프에 **`CtrlRig2`** 버튼 설치.

### 코드로 실행
```python
import tools.A00130_ControlRig_V02 as A00130_ControlRig_V02
A00130_ControlRig_V02.run(True)   # True 면 DEV_MODE 에서 reload 후 실행
```

V01(`CtrlRig`)과 `WINDOW_OBJECT_NAME` 이 달라 **둘을 동시에 띄워도 서로를 닫지 않는다.**

---

## 2. 무엇이 V01 과 다른가

| | V01 | **V02** |
|---|---|---|
| 대상 지정 | Targets 리스트에 **손으로 순서대로** 담는다 | **매핑 표(json)** 가 짝을 갖는다 |
| 매칭 기준 | 아바타 조인트 (임시 조인트 체인을 만들어 orient 를 다시 잡는다) | **템플릿 조인트** — 사람이 눈으로 놓는다 |
| 실패 | `except: print` 로 삼킨다 | **세어서 보고**한다 |
| undo | 없다 | **한 스텝** |
| 부위 추가 | 코드 수정 | **json 한 줄** |

---

## 3. 작업 순서

1. **케이지를 레퍼런스로 불러온다.** `Source > Cage namespace` 에서 그 네임스페이스를 고른다.
   레퍼런스가 아니면 `(none)`.
2. **`Create Template Joints`** — 매핑 표의 이름·부모 관계대로 조인트를 만든다.
   **전부 원점에 쌓인다** — 위치는 사람이 놓는다. 이미 있는 조인트는 건드리지 않는다.
3. **템플릿 조인트를 아바타에 맞춰 손으로 옮긴다.**
4. **`Check`** — 없는 템플릿 조인트 / 없는 케이지 세트를 보고한다. **씬은 안 바뀐다.**
5. **`Match`** — 각 케이지 세트의 원소를 짝인 템플릿 조인트 자리로 옮긴다. **undo 한 스텝.**

---

## 4. 동작 규칙

### 4.1 무엇을 어디로 옮기나

매핑 표의 한 줄은 **`템플릿 조인트 ← 케이지 세트`** 다.
세트의 **원소 전부**가 그 조인트의 월드 트랜스폼으로 간다.

- **세트가 아니라 오브젝트**를 적어도 된다 — 그 오브젝트 하나만 옮긴다.
- **세트 안에 또 다른 세트가 있으면 통째로 무시**한다. 재귀하지 않으므로 **하위 세트 안의
  오브젝트도 건드리지 않는다.** 몇 개를 무시했는지 로그로 알린다.
- 한 조인트에 세트를 **여럿** 붙일 수 있다(예: `helper_foot_l`).

### 4.2 위치만 맞추는 세트

`match` 가 `["t"]` 인 세트는 **위치만** 옮기고 **회전은 그대로 둔다.** 지금 그런 세트는 6개다.

| 세트 | 왜 |
|---|---|
| `B01_Leg_L_ik_01_foot` · `B02_Leg_R_ik_01_foot` | 발 IK 컨트롤 — 회전은 리그가 정한다 |
| `A01_Arm_L_04_Pole` · `A02_Arm_R_04_Pole` | 폴 타깃 — `poleVectorConstraint` 는 **위치만** 쓴다 |
| `B01_Leg_L_06_pole` · `B02_Leg_R_06_pole` | 〃 |

### 4.3 없어도 멈추지 않는다

**템플릿 조인트가 없으면 그 짝만 건너뛰고 로그를 남긴 뒤 다음 매칭을 계속한다.**
케이지 세트가 없을 때도 같다(이때는 "네임스페이스를 확인하라" 고 덧붙인다).
한 짝이 없다고 전체가 멈추지 않는다.

### 4.4 잠기거나 구동되는 오브젝트는 **반쯤 옮기지 않는다**

**`matchTransform` 은 잠긴 채널을 조용히 건너뛴다**(실측: `translateX` 만 잠근 오브젝트가
X 만 안 움직이고 에러도 없었다). 그래서 쓰기 전에 **잠금과 입력 연결을 직접 보고**,
막힌 채널이 하나라도 있으면 **그 오브젝트를 통째로 건너뛰고** 어떤 채널이 막혔는지 알린다.
반쯤 옮겨진 상태가 제일 나쁘다.

> `getAttr(plug, settable=True)` 는 판정에 쓰지 않는다 — **컨스트레인트가 구동하는
> 트랜스폼에도 `True` 를 돌려준다**(A00060 에서 실측).

### 4.5 네임스페이스는 **골라 본 뒤 없으면 이름 그대로** 찾는다

이름 하나를 씬에서 찾을 때 **후보 두 개를 순서대로** 본다 — 조인트든 세트든 똑같다.

```
Cage namespace = CAGE   ->   1) CAGE:helper_pelvis      2) helper_pelvis
Cage namespace = (none) ->      helper_pelvis
```

그래서 세 경우가 전부 된다:

| 케이지를 어떻게 불러왔나 | Cage namespace | 찾히는 이름 |
|---|---|---|
| **레퍼런스** | 그 네임스페이스 | `CAGE:helper_pelvis` · `CAGE:A00_Spine_00` |
| **임포트** | `(none)` | `helper_pelvis` · `A00_Spine_00` |
| 조인트만 툴로 만들고 케이지는 레퍼런스 | 그 네임스페이스 | 조인트는 로컬, 세트는 `CAGE:` |

- **둘 다 있으면** 네임스페이스 쪽을 쓰고, `ambiguous joint - using CAGE:x (also found x)`
  라고 **알린다.** 어느 쪽을 골랐는지 감추지 않는다.
- **못 찾으면** 무엇을 찾아봤는지 적는다 — `looked for CAGE:x and x`.
- `Create Template Joints` 도 같은 방식으로 본다. 그래서 **레퍼런스 케이지가 이미 조인트를
  갖고 있으면 아무것도 새로 만들지 않는다** (로컬에 같은 이름을 하나 더 만들지 않는다).

매핑 json 에는 **양쪽 다 네임스페이스 없이** 적는다 — 붙이는 것은 실행 시점의 일이다.

> **2026-08-28** 이전 v02.00 은 네임스페이스를 **세트에만** 붙였다. 템플릿 조인트가 케이지
> 파일 안에 함께 들어 있어서, 케이지를 **레퍼런스**하면 `Check` 가 전부
> `joint missing` 이 됐다(임포트는 멀쩡했다). 지금은 위처럼 양쪽 다 본다.

---

## 5. 매핑 파일

`app/data/mapping/v001/template_map.json` — **조인트 하나가 한 항목**이다.

```jsonc
{
  "name":   "helper_foot_l",
  "parent": "helper_calf_l",
  "targets": [
    { "set": "B01_Leg_L_03" },                          // 기본 = 위치 + 회전
    { "set": "B01_Leg_L_ik_01_foot", "match": ["t"] }   // 위치만
  ]
}
```

| 필드 | 뜻 |
|---|---|
| `name` | 템플릿 조인트 이름 (네임스페이스 없음) |
| `parent` | 부모 조인트. 루트는 `null` |
| `targets[].set` | 짝인 케이지 세트(또는 오브젝트) 이름 (네임스페이스 없음) |
| `targets[].match` | `["t","r"]` 가 기본(생략 가능). `["t"]` 면 위치만 |
| `targets` 가 빈 목록 | **정상** — 배치·계층용 조인트(현재 10개) |
| `orient` | **아직 안 쓴다.** orient 규칙이 정해지면 이 자리에 들어간다 |

**짝이 늘거나 줄면 이 파일만 고치면 된다.** 케이지 버전이 갈리면
`app/data/mapping/` 아래에 폴더를 하나 더 만들면 `Mapping` 콤보에 뜬다.

> **값이 언제나 목록인 이유**: 원본 표에서 한 조인트가 세트 둘을 갖는 모양이 두 가지였다 —
> `helper_foot_l` 은 한 줄에 둘, `helper_ball_l` 은 **줄이 둘로 나뉘어** 있었다.
> `{조인트: 세트}` 로 만들면 **`helper_ball_l` 의 한쪽이 조용히 사라진다.**
> 로드할 때 같은 이름이 또 나오면 합친다.

**현재 데이터**: 조인트 **80** · 짝 **74** · 매칭 대상이 없는 조인트 **10** · 위치 전용 세트 **6**.

---

## 6. 아직 없는 것 (다음 단계)

| 단계 | 무엇 | 필요한 것 |
|---|---|---|
| **Mirror** | 왼쪽 템플릿 조인트의 트랜스폼을 오른쪽으로 | — (규칙은 정해졌다, 계획서 7-3) |
| **IK 세션** | `D01_IK_handle` 의 핸들을 `A00060` IK Edit 으로 편집 | FK/IK 스위치 어트리뷰트 이름 |
| **Orient** | 템플릿 조인트 orient 확정 → `rotate` 0 | **orient 규칙** (아직 안 받음) |
| **Validate** | 빌드 전 점검 | — |
| 길이 수치 | 옵션 컨트롤러 `Arm_L` 등에 거리 기록 | `Arm_r` 대소문자 확인 |

> **탭이 늘어나는 자리**는 `app/ui/main_window.py` 의 `STEPS` 표다. 줄 하나를 넣으면
> 탭이 붙는다. **Match 는 다른 단계가 돌았는지에 의존하지 않는다** — orient 규칙이 나중에
> 와도 지금 코드를 고칠 필요가 없게 해 뒀다.

---

## 7. 구조 (개발자용)

```
A00130_ControlRig_V02/
├── __dragDrop_A00130_V02.py     # 셸프 버튼 (CtrlRig2)
├── launch.py                    # run() → MainWindow → coral_dark 테마
├── icon/A00130_ControlRig_V02.svg|.png
├── .ref/ref_01.txt              # 사용자가 준 원본 자료 (매핑 json 의 출처)
└── app/
    ├── config/version.py
    ├── data/mapping/v001/template_map.json
    ├── core/
    │   ├── scene_utils.py       # 네임스페이스 · 세트 멤버 · 쓰기 가능 판정
    │   ├── mapping_data.py      # json 로드 · 병합 · 점검
    │   └── match_manager.py     # plan() / apply() / create_template()
    └── ui/main_window.py        # STEPS 표 + Source 그룹 + 공유 로그
```

**`plan()` 과 `apply()` 를 갈라 뒀다** — `plan()` 은 씬을 읽기만 하고, 목록과 상태를 돌려준다.
그래서 `Check` 버튼과 미리보기 표가 **아무것도 바꾸지 않고** 같은 계산을 쓴다.

### V01 에서 가져오지 않은 것

`MayaScene.match_transforms` 는 팔로워의 `rotateOrder` 를 타깃 것으로 잠깐 바꿨다가
되돌린다. 그런데 **`xform -rotateOrder` 는 방향을 보존하지 않는다**(실측: `rotate 30/40/50`
인 노드의 rotateOrder 만 바꾸면 월드 회전이 달라진다). 그래서 V02 는 그 방식을 쓰지 않고
마야 내장 **`matchTransform`** 을 쓴다 — rotateOrder · rotateAxis · 피벗을 마야가 처리한다.

---

## 8. 검증

`mayapy` headless **70항목**. 매핑 파일(개수·병합·위치 전용·구조 전용) · 템플릿 생성
(계층·멱등) · 네임스페이스가 세트에만 붙는가 · **하위 세트 무시와 비재귀** · 위치 전용에서
회전 불변 · **없는 조인트/세트 뒤에도 계속 도는가** · 세트가 아닌 오브젝트 · **잠김/구동
멤버를 반쯤 옮기지 않는가** · **undo 한 스텝** · UI 버튼 경로.
