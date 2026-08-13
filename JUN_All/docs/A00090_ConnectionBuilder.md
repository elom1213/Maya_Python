# A00090_ConnectionBuilder — 사용 안내

MetaHuman 페이셜 셋업에서 **RBF solver 의 출력을 driver 노드(그리고 필요 시 blendShape)로
어트리뷰트 연결**하는 Maya 내 PySide 툴. `rules/<version>/*.json` 의 규칙(`mapping`)에 따라
여러 노드를 한 번에 batch 연결·해제·검증한다.

> Maya 안에서 도는 PySide 툴이다(`maya.cmds` 의존). `tools.A00090_ConnectionBuilder.run(True)` 로 실행.

---

## 1. 핵심 개념

| 개념 | 설명 |
|------|------|
| **Source** | 연결의 출발 노드(구 *Base*). 보통 RBF **solver** 노드. `Is Solver` 가 켜져 있으면 `Source.outputs[i]`, 꺼져 있으면 `Source.<attr>` 를 출처로 쓴다. |
| **Target** | 연결의 도착 노드(구 *Driver*). mapping 의 attr 이름으로 연결된다. |
| **Version** | 규칙 세트의 버전 폴더(`app/rules/v001`, `v002` …). 콤보에서 고른 버전의 json 만 쓴다. |
| **Rule** | `rules/<version>/<name>.json`. `mapping`(attr 이름 배열)이 어떤 어트리뷰트를 연결할지 정한다. |
| **Pair mode** | Source/Target 리스트를 어떻게 짝지을지. `1→n`(broadcast) 또는 `n→n`(index pair). |
| **Is Solver** | 꺼짐(기본): 출처를 `Source.<attr>` 로 본다. 켜면 `Source.outputs[i]` 로 본다. |

규칙 JSON 예시(`rules/v001/WRK_calf_l.json`):

```json
{
  "solver_node": "WRK_calf_l_UERBFSolver",
  "driver_node": "WRK_calf_l__null__",
  "blendshape_node": "",
  "mapping": ["calf_l_default", "calf_l_back_50", "calf_l_back_90"]
}
```

> UI 에서 Source/Target 를 직접 지정하므로 연결 동작은 json 의 `solver_node`/`driver_node` 대신
> 리스트에 담은 노드를 사용한다(`mapping` 만 json 에서 읽는다). `blendshape_node` 는 더 이상 쓰지 않는다.

### 1-1. 규칙 버전 (Rule version)

포즈 구성이 바뀌면 `mapping` 도 달라진다. 예전 규칙을 덮어쓰지 않도록 규칙 json 은
**버전 폴더** 안에 둔다.

```
app/rules/
├── v001/          # 현재 배포 규칙
│   ├── WRK_calf_l.json
│   └── ...
└── v002/          # 수정한 규칙 (포즈 추가/이름 변경 등)
    └── ...
```

- **새 버전 추가 방법**: `app/rules/` 아래에 폴더(`v002`, `v003` … 이름은 자유)를 만들고 수정한
  json 을 넣는다. 보통 이전 버전 폴더를 통째로 복사한 뒤 고치는 게 빠르다.
- UI 의 **`Version` 콤보**에서 폴더를 고르면 그 버전의 json 만 `Rule` 콤보에 채워지고,
  **모든 동작(Create / Connect / Connect All / Connect Intermediate)이 선택한 버전만 사용**한다.
- 창을 띄운 뒤 폴더를 추가했다면 **`Refresh`** 로 다시 스캔한다(창을 다시 열 필요 없음).
- 콤보는 폴더 이름 **정렬 순서의 첫 항목**으로 시작한다(`v001` → `v002` … 이면 `v001`).
  `.` / `_` 로 시작하는 폴더는 목록에서 제외된다(작업용 폴더 보관 가능).
- 버전 폴더가 하나도 없으면 로그에 `[ERROR] No rule version folder in : ...` 를 남긴다.

---

## 2. 화면 구성

```
┌───────────────────────────────────────────────────────────┐
│ Mesh / Node [__________]  [Get] [Create] [Create All]      │
├──────────────────────────┬────────────────────────────────┤
│ [ ] Is Solver            │                                 │
│ Source                   │ Target                          │
│  [Select Objects]        │  [Select Objects]               │
│  ┌────────────────────┐  │  ┌───────────────────────────┐  │
│  │ (node list)        │  │  │ (node list)               │  │
│  └────────────────────┘  │  └───────────────────────────┘  │
│  [Add][Del][Up][Down]    │  [Add][Del][Up][Down]           │
│  [Set Attr][Del Attr]    │  [Set Attr][Del Attr]  [Sort]   │
│  [Sort]                  │                                 │
├──────────────────────────┴────────────────────────────────┤
│ Version [ v001 ▾ ]  Rule [ WRK_calf_l ▾ ]        [Refresh] │
│ [ ] n->n (index pair) [Connect All][Connect][Disconnect][Validate] │
│ [Connect Intermediate]                                     │
│ ┌ Log ──────────────────────────────────────────────────┐ │
│ └────────────────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────────┘
```

- Source / Target 은 좌·우로 나란히 배치된 재사용 리스트 위젯(`JUN_mod_tsl_qt_v01`)이다.
  `Select Objects`(현재 선택으로 교체) / `Add`(중복 없이 추가) / `Del` / `Up` / `Down` / `Sort` 내장.

---

## 3. 연결 모드 (Pair mode)

`n->n (index pair)` 체크박스가 Source/Target 리스트를 짝짓는 방식을 정한다. **Connect All / Connect /
Disconnect / Validate 모두 이 모드를 따른다.**

| 모드 | 체크박스 | 동작 |
|------|----------|------|
| **1→n (broadcast)** | 해제(기본) | **첫 번째 Source** 를 선택된 **모든 Target** 에 연결. Source 가 2개 이상이면 첫 번째만 쓰고 경고 로그. |
| **n→n (index pair)** | 체크 | `Source[i] → Target[i]` 로 인덱스 짝짓기. **개수가 다르면** `[ERROR]` 로그만 남기고 아무것도 하지 않는다. |

n→n 일 때도 mapping 은 **콤보박스에서 선택한 rule 1개**를 모든 쌍에 동일 적용한다.

---

## 4. 버튼 동작

| 버튼 | 동작 |
|------|------|
| **Get** (Mesh / Node) | 현재 Maya 선택을 Mesh / Node 칸에 넣는다(콤마 구분 다중 가능). |
| **Create** | 칸의 노드 + **선택한 rule 1개**로 생성. 노드가 **mesh** 면 `mapping` 이름으로 target 복제 + blendShape(§4-1), **그 외(joint/transform/control)** 면 `mapping` 이름의 double attr 생성(`TargetBuilder` 가 타입 판단). |
| **Create All** | 칸의 노드 + **선택 버전의 모든 rule** 로 생성. mesh 는 모든 rule 의 target 을 한 blendShape 에 누적, 노드는 모든 rule 의 attr 를 누적 생성. |
| **Set Attr** (Source/Target) | 해당 리스트의 **모든 노드**에 선택 rule mapping 의 double attr 를 생성. |
| **Del Attr** (Source/Target) | 해당 리스트의 **모든 노드**에서 mapping attr 를 삭제. |
| **Connect** | 선택 rule + 현재 Source/Target + Pair mode 로 짝을 만들어 연결. |
| **Connect All** | **선택 버전의 모든 rule** × 현재 짝을 연결(전체 rule 순회). |
| **Disconnect** | 선택 rule + 짝의 연결 해제. |
| **Validate** | 선택 rule + 짝의 연결 상태를 로그로 보고(`[OK]`/`[ERROR]`). 짝마다 결과 출력. |
| **Refresh** | `app/rules` 를 다시 스캔해 Version / Rule 콤보를 갱신. |
| **Connect Intermediate** | **선택 버전의** 모든 solver `outputs[i]` 를 공통 null `WRK_intermediate.<mapping[i]>` 로 연결(없으면 `WRK_All` 아래에 null·attr 생성). |

### 4-1. blendShape target 이 만들어지는 방식 (v01.06)

여기에는 **꼭 구분해야 하는 두 가지 이름**이 있다.

| | 무엇 | 예 |
|---|------|-----|
| **타겟 메시의 노드 이름** | 씬에서 **유일**해야 한다 | `SIN_Set007_Top2_calf_l_default` |
| **blendShape 웨이트 별칭(alias)** | `Connect` 가 쓰는 주소. **rule 의 mapping 이름 그대로** | `calf_l_default` |

rule 의 mapping 이름은 **포즈 이름**이라 옷이 몇 벌이든 똑같다. 그래서 타겟 메시 이름에는
**메시 이름을 접두사로** 붙여 유일하게 만들고, blendShape 의 alias 는 mapping 이름으로 되돌린다.
alias 는 노드 단위라 blendShape 가 여럿이어도 각각 `calf_l_default` 를 가질 수 있고,
`Connect` 가 쓰는 주소(`<blendShape>.<mapping이름>`)는 예전과 똑같이 유지된다.

- **기존 타겟 재사용**: `<메시>_<이름>` 또는 예전 방식의 `<이름>` 노드가 있고 **토폴로지가 base 와
  같으면** 그것을 그대로 쓴다(손으로 조각해 둔 타겟이 보존된다). 토폴로지가 다르면 건드리지 않고
  새로 만든다.
- **부분 실패를 감춘 채 넘어가지 않는다**: 타겟 하나가 실패해도 나머지는 계속 진행하고,
  로그에 `N created, M reused, K already there` 와 실패한 이름·이유가 남는다.

> **v01.05 이하에서 나던 오류** — 타겟 메시 이름을 mapping 이름 그대로 썼기 때문에, 옷 A 에
> 타겟을 만든 뒤 옷 B 에 같은 rule 을 돌리면 **A 의 타겟을 B 것으로 재사용**해 이렇게 죽었다:
> ```
> [Create] SIN_Set007_Top2 : Target calf_l_defaultShape does not match with base SIN_Set007_Top2Shape.
> No deformable objects selected.
> ```
> 그 이름이 조인트 등 다른 노드에 이미 쓰이고 있으면 `More than one object matches name` 이 됐다.
> 어느 쪽이든 `blendShape` 호출 하나가 통째로 실패해 **타겟이 아예 안 생기거나 일부만 생겼다.**

---

## 5. 사용 순서 (예)

1. `Source` 에 RBF solver 노드(들)를, `Target` 에 driver null 노드(들)를 `Select Objects`/`Add` 로 담는다.
2. `Version` 콤보에서 규칙 세트 버전을 고르고, `Rule` 콤보박스에서 적용할 규칙을 고른다.
3. 필요하면 `Set Attr` 로 Target 에 mapping attr 를 먼저 만든다.
4. Pair mode 선택 — 1개를 여러 개에 뿌리면 **체크 해제(1→n)**, 1:1 로 줄지으면 **체크(n→n)**.
5. `Connect` (또는 전체 규칙 일괄은 `Connect All`).
6. `Validate` 로 확인, 필요 시 `Disconnect`.

---

## 6. 구조 (개발 참고)

```
A00090_ConnectionBuilder/
├── launch.py                   # run(): MainWindow → red 테마 → show
└── app/
    ├── config/version.py       # VERSION / LAST_UPDATE
    ├── rules/<version>/*.json  # 연결 규칙(solver/driver/mapping). 버전 폴더 단위
    ├── core/                   # 로직 (maya.cmds)
    │   ├── rule_loader.py      # RuleLoader: 버전 스캔 / json 로드 / 전체 스캔
    │   ├── connection_rule.py  # ConnectionRule (solver/driver/mapping)
    │   ├── connection_manager.py  # connect/disconnect/validate (단일 rule)
    │   ├── attribute_manager.py   # attr 생성/삭제
    │   ├── blendshape_manager.py  # blendShape target 생성/누적(append)
    │   ├── target_builder.py      # 노드 타입 판단 → target 또는 attr 디스패치
    │   └── intermediate_manager.py# solver outputs → WRK_intermediate
    └── ui/main_window.py       # PySide UI (Source/Target 리스트 + batch 루프)
```

- UI 는 노드 리스트를 Pair mode 로 `(source, target)` 짝으로 펼친 뒤 **짝마다 core 의 단일 rule
  로직을 루프 호출**한다(core 는 단일 rule 단위 그대로 재사용).
- 리스트 위젯은 Framework 공용 `Framework/qt/MOD_tsl_qt_v01.py`(`JUN_mod_tsl_qt_v01`) 재사용.

---

## 7. 변경 이력 (요약)

- **v01.06** — **`Is Solver` 기본값을 꺼짐으로** 변경(출처를 `Source.<attr>` 로 본다).
  **blendShape target 생성 버그 수정**(§4-1). 타겟 메시를 `<메시>_<mapping이름>` 으로
  유일하게 만들고 blendShape **alias 를 mapping 이름으로 되돌려**, 메시가 여러 개여도 같은 rule 을
  각각 적용할 수 있다(`Connect` 주소는 그대로). 기존 타겟은 **토폴로지가 맞을 때만** 재사용.
  추가 수정: 타겟을 지워 웨이트 인덱스가 듬성해진 blendShape 에 append 할 때 `size` 를 다음 인덱스로
  쓰다 **기존 타겟을 덮어쓰던 것**을 `max(인덱스)+1` 로, 이름이 중복된 메시를 조용히 잘못 잡던 것을
  거부로, 셰이프 해석을 공용 `Framework.core.maya_shape` 로. 로그가 생성/재사용/실패를 각각 보고한다.

- **v01.05** — **규칙 버전 폴더 지원**. `app/rules_v01/*.json` → `app/rules/<version>/*.json`
  (기존 규칙은 `rules/v001` 로 이동). Rule 행에 **`Version` 콤보 + `Refresh`** 추가 —
  버전을 바꾸면 Rule 목록이 갱신되고 모든 동작이 선택 버전의 json 만 사용한다.
  `RuleLoader` 에 `find_versions()` / `get_version()` / `set_version()` / `rule_dir()` 추가,
  `load` · `load_solver_rule` · `find_all_json` · `load_all` 에 `version` 인자 추가.
- **v01.04** — 단일 창 강제(`objectName` 으로 기존 창 닫기, 창 누적 방지). `Mesh for blendShape` →
  **`Mesh / Node`** 로 확장: 노드가 mesh 면 blendShape target, joint/transform 등이면 attribute 를
  생성(`TargetBuilder`). 버튼을 **`Create`**(선택 rule 1개) / **`Create All`**(모든 rule)로 분리.
  blendShape 누적(append) 지원. 생성 작업을 `undo_chunk` 로 묶음.
- **v01.03** — BlendShape 입력행 제거(상단 Create targets 는 유지), 용어 *Base→Source* / *Driver→Target*,
  Source/Target 을 리스트 위젯(`JUN_mod_tsl_qt_v01`)으로 교체(좌·우 배치), Pair mode(1→n / n→n) 체크박스
  추가로 Connect/Disconnect/Validate batch 동작.
- v01.02 — Connect Intermediate(solver outputs → `WRK_intermediate`) 등.
