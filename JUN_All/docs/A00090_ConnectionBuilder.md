# A00090_ConnectionBuilder — 사용 안내

MetaHuman 페이셜 셋업에서 **RBF solver 의 출력을 driver 노드(그리고 필요 시 blendShape)로
어트리뷰트 연결**하는 Maya 내 PySide 툴. `rules_v01/*.json` 의 규칙(`mapping`)에 따라
여러 노드를 한 번에 batch 연결·해제·검증한다.

> Maya 안에서 도는 PySide 툴이다(`maya.cmds` 의존). `tools.A00090_ConnectionBuilder.run(True)` 로 실행.

---

## 1. 핵심 개념

| 개념 | 설명 |
|------|------|
| **Source** | 연결의 출발 노드(구 *Base*). 보통 RBF **solver** 노드. `Is Solver` 가 켜져 있으면 `Source.outputs[i]`, 꺼져 있으면 `Source.<attr>` 를 출처로 쓴다. |
| **Target** | 연결의 도착 노드(구 *Driver*). mapping 의 attr 이름으로 연결된다. |
| **Rule** | `rules_v01/<name>.json`. `mapping`(attr 이름 배열)이 어떤 어트리뷰트를 연결할지 정한다. |
| **Pair mode** | Source/Target 리스트를 어떻게 짝지을지. `1→n`(broadcast) 또는 `n→n`(index pair). |
| **Is Solver** | 켜짐(기본): 출처를 `Source.outputs[i]` 로 본다. 꺼짐: `Source.<attr>` 로 본다. |

규칙 JSON 예시(`rules_v01/WRK_calf_l.json`):

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

---

## 2. 화면 구성

```
┌───────────────────────────────────────────────────────────┐
│ Mesh for blendShape [____________]  [Get] [Create targets] │
├──────────────────────────┬────────────────────────────────┤
│ [x] Is Solver            │                                 │
│ Source                   │ Target                          │
│  [Select Objects]        │  [Select Objects]               │
│  ┌────────────────────┐  │  ┌───────────────────────────┐  │
│  │ (node list)        │  │  │ (node list)               │  │
│  └────────────────────┘  │  └───────────────────────────┘  │
│  [Add][Del][Up][Down]    │  [Add][Del][Up][Down]           │
│  [Set Attr][Del Attr]    │  [Set Attr][Del Attr]  [Sort]   │
│  [Sort]                  │                                 │
├──────────────────────────┴────────────────────────────────┤
│ Rule [ WRK_calf_l ▾ ]                                      │
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
| **Get** (Mesh) | 현재 Maya 선택을 Mesh 칸에 넣는다. |
| **Create targets** | 선택 rule 의 `mapping` 이름으로 mesh 를 복제해 blendShape target 을 만들고 blendShape 를 건다(`BlendShapeManager`). |
| **Set Attr** (Source/Target) | 해당 리스트의 **모든 노드**에 선택 rule mapping 의 double attr 를 생성. |
| **Del Attr** (Source/Target) | 해당 리스트의 **모든 노드**에서 mapping attr 를 삭제. |
| **Connect** | 선택 rule + 현재 Source/Target + Pair mode 로 짝을 만들어 연결. |
| **Connect All** | `rules_v01` 의 **모든 rule** × 현재 짝을 연결(전체 rule 순회). |
| **Disconnect** | 선택 rule + 짝의 연결 해제. |
| **Validate** | 선택 rule + 짝의 연결 상태를 로그로 보고(`[OK]`/`[ERROR]`). 짝마다 결과 출력. |
| **Connect Intermediate** | `rules_v01` 의 모든 solver `outputs[i]` 를 공통 null `WRK_intermediate.<mapping[i]>` 로 연결(없으면 `WRK_All` 아래에 null·attr 생성). |

---

## 5. 사용 순서 (예)

1. `Source` 에 RBF solver 노드(들)를, `Target` 에 driver null 노드(들)를 `Select Objects`/`Add` 로 담는다.
2. `Rule` 콤보박스에서 적용할 규칙을 고른다.
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
    ├── rules_v01/*.json        # 연결 규칙(solver/driver/mapping)
    ├── core/                   # 로직 (maya.cmds)
    │   ├── rule_loader.py      # RuleLoader: json 로드 / 전체 스캔
    │   ├── connection_rule.py  # ConnectionRule (solver/driver/mapping)
    │   ├── connection_manager.py  # connect/disconnect/validate (단일 rule)
    │   ├── attribute_manager.py   # attr 생성/삭제
    │   ├── blendshape_manager.py  # blendShape target 생성
    │   └── intermediate_manager.py# solver outputs → WRK_intermediate
    └── ui/main_window.py       # PySide UI (Source/Target 리스트 + batch 루프)
```

- UI 는 노드 리스트를 Pair mode 로 `(source, target)` 짝으로 펼친 뒤 **짝마다 core 의 단일 rule
  로직을 루프 호출**한다(core 는 단일 rule 단위 그대로 재사용).
- 리스트 위젯은 Framework 공용 `Framework/qt/MOD_tsl_qt_v01.py`(`JUN_mod_tsl_qt_v01`) 재사용.

---

## 7. 변경 이력 (요약)

- **v01.03** — BlendShape 입력행 제거(상단 Create targets 는 유지), 용어 *Base→Source* / *Driver→Target*,
  Source/Target 을 리스트 위젯(`JUN_mod_tsl_qt_v01`)으로 교체(좌·우 배치), Pair mode(1→n / n→n) 체크박스
  추가로 Connect/Disconnect/Validate batch 동작.
- v01.02 — Connect Intermediate(solver outputs → `WRK_intermediate`) 등.
