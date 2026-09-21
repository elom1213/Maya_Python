---
name: release-layout-launch-py
description: 릴리즈본은 Framework 를 툴 폴더 안에 동봉하고 config.py / dev 는 싣지 않는다 — launch.py 가 두 배치를 스스로 구분해야 남의 PC 에서 열린다
metadata:
  type: project
---

`release_builder_QT`(= 옛 `dev/build_release.py`)가 만드는 릴리즈본은 dev 트리와 **배치가 다르다**.

| | dev 트리 | 릴리즈본 (`Maya_Tool_Release`) |
|---|---|---|
| 툴 | `JUN_All/tools/<툴>` | `<repo>/tools/<툴>` |
| `Framework` | `JUN_All/Framework` (공유) | `<툴 폴더>/Framework` (**툴마다 사본**) |
| `config.py` · `dev/` | 있음 | **없음** (`dev` 는 IGNORE_PATTERNS) |

그래서 `launch.py` 가 `../..` 하나만 `sys.path` 에 올리고 `import config` 를 하면
릴리즈본에서 `ModuleNotFoundError: No module named 'config'` 로 죽고, 그걸 넘겨도
다음 줄 `from Framework...` 에서 또 막힌다 (Framework 가 저장소 루트에 없으므로).

**고치는 법** — 경로를 단정하지 말고 있는 것을 본다:
`TOOL_ROOT/Framework` 가 있으면 릴리즈본 → `TOOL_ROOT`(Framework 용) + `ROOT`(`tools.*` 용) 를
둘 다 올리고 `DEV_MODE = False` 로 고정하며 **`import config` 를 아예 하지 않는다**
(`config` 는 흔한 이름이라 다른 툴 폴더의 `config.py` 를 집을 수 있다).
A00470 v01.08 이 이 형태다 (`JUN_All/tools/A00470_MaterialTool/launch.py`).

**2026-09-21 에 진입 파일 61개 전부에 같은 프리앰블을 넣었다**
(Qt `launch.py` 49 + standalone `launch.py` 5 + maya.cmds `launcher.py` 7).
`A00200_CSV_tool` 만 제외 — Framework 의존이 없다. 규약과 검증법은 `JUN_All/docs/Release_Layout.md`.

**maya.cmds 툴은 순서가 따로 문제였다** — 본체 모듈이 `from Framework...` 를 모듈 수준에서 하는데
`launcher.py` 는 `run()` **안에서야** `sys.path` 를 건드렸다. `from . import <본체>` 보다 **앞**에
둬야 한다. 본체의 최상위 `import config` 는 `from . import config` 로 (자기 폴더 설정을 집게).

검증은 [[mayapy-headless-verify]] 방식에 더해 **dev 트리 경로를 `sys.path` 에서 걷어내고**
`sys.modules` 의 `Framework`/`tools`/`config` 를 지운 뒤 import 해야 의미가 있다 —
안 그러면 dev 트리의 Framework 가 잡혀 통과한 것처럼 보인다.

> 곁가지: 툴마다 Framework 사본이라 한 세션에서 여러 툴을 열면 **먼저 열린 툴의 사본**이
> `sys.modules` 를 차지한다. 오래 묵은 툴이 있으면 옛 Framework 가 쓰인다.
