---
name: wip-a00090-posewrangler-bundle
description: "A00090 이 Pose Wrangler export json 하나를 규칙으로 바로 읽는다(솔버당 파일 불필요). 파일 이름은 rules_<폴더>.json 이지만 판정은 내용(solvers 키), 중립 포즈 `default` 는 이름이 겹쳐 <driver>_default 로 바꿔야 한다 (v01.07)"
metadata: 
  node_type: memory
  type: project
  originSessionId: eed8b93d-9d98-420a-85c3-532581f77463
  modified: 2026-09-04T01:38:07.313Z
---

A00090_ConnectionBuilder 가 **마야 Pose Wrangler 에서 export 한 json 하나**를 규칙으로 바로
읽는다 (v01.06→**01.07**, 2026-09-04). 예전에는 포즈를 고칠 때마다 `WRK_calf_l.json` …을
**솔버 수만큼 손으로 다시 써야** 했다. 버전 폴더 구조 자체는 [[wip-a00090-rule-versions]].

**파일 이름 규칙: `rules_<폴더이름>.json`** (`v004/rules_v004.json`). 파일만 떼어 놔도 출처가
읽힌다. **다만 코드는 이 이름에 기대지 않는다** — 최상위 `solvers` 키가 있으면 번들로 읽으므로
Pose Wrangler 가 지어 준 이름 그대로 둬도 되고, 한 폴더에 두 방식을 **섞어도** 된다. 이름은
사람을 위한 규약이지 동작 조건이 아니다.

**★ 그대로 못 쓰는 이름이 딱 하나 있다.** Pose Wrangler 는 중립 포즈를 **언제나 그냥 `default`**
로 부른다. 그대로 mapping 에 넣으면 솔버 8개가 전부 `WRK_intermediate.default` 라는 **같은
어트리뷰트 하나로 몰려 서로를 덮어쓴다**(에러 없이 조용히). 손글씨 규칙이 쓰던
**`<driver>_default`** 로 되살린다 — 드라이버 이름은 번들의 `drivers[0]` 에 있다. 나머지 포즈는
사용자가 이미 드라이버 이름을 붙여 짓기 때문에 손대지 않는다.

풀어 읽는 규칙:
- **규칙 이름** = 솔버 이름에서 `_UERBFSolver` 를 뗀 것(`WRK_calf_l`). v002 의 **파일 이름과
  같아서** 버전을 바꿔도 `Rule` 콤보 목록이 그대로다.
- **mapping** = `poses` 의 **키 순서**(json 은 순서 보존, 그 순서가 `outputs[i]` 순서).
  v003 번들 8솔버를 v002 손글씨 mapping 과 대조해 **전부 일치** 확인.
- 색인은 폴더 안 json 의 (이름·mtime·크기)를 기억해 **파일이 바뀌면 `Refresh` 없이 다시 읽는다.**
  `Refresh` 는 폴더를 더하거나 지웠을 때 쓴다.

**undo**: 씬을 바꾸는 버튼 6개(`Connect`/`Connect All`/`Disconnect`/`Set Attr`/`Del Attr`/
`Connect Intermediate`)를 `undo_chunk()` 로 묶었다([[undo-chunk-by-default]]). 그 전에는
`Connect Intermediate` 뒤 `Ctrl+Z` 가 **연결을 하나씩 끊다가 마지막에야 노드를 지웠다**
(사용자 보고). `Validate` 는 읽기만 해서 뺐다.

파일: `app/core/rule_loader.py`(색인·두 포맷) · `app/ui/main_window.py`.
