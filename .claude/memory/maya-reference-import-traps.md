---
name: maya-reference-import-traps
description: "디스크의 마야 파일 레퍼런스를 읽고 임포트해 저장할 때의 함정 — loadReferenceDepth none 으로 열어 저장하면 언로드가 굳는다, 언로드는 import 불가, 부모 import 시 중첩이 최상위로 올라온다, .ma 헤더 file 문장은 여러 줄"
metadata:
  node_type: memory
  type: project
  originSessionId: 9851bc3c-33e0-43d3-9d39-fe7b39c172be
  modified: 2026-10-12T01:59:01.168Z
---

mayapy 2024 실측 (2026-10-12, A00480 Maya > Reference 만들며). 코드는 `tools/A00480_FileTool/app/maya/core`.

- **`file -o -loadReferenceDepth none` 으로 연 씬을 저장하면 레퍼런스가 전부 언로드로 굳는다** — 다음에 기본 열기 해도
  안 보인다. 기본 열기는 저장된 로드 상태를 지킨다(A 로드 · B 언로드 → 그대로). 그래서 **읽기만 할 때(스캔)는 none,
  저장할 작업(임포트)은 기본 열기.** `topOnly` · `all` 은 언로드였던 것도 로드한다.
- `none` 으로 열면 최상위 레퍼런스 노드와 `referenceQuery -filename` 은 되지만 **`-namespace` 는 에러**("Cannot find the
  associated namespace"), **중첩 레퍼런스 노드는 없다**(부모가 로드돼야 생긴다).
- **언로드 레퍼런스는 `importReference` 가 에러** → 먼저 `file -loadReference`.
- **부모 레퍼런스를 임포트하면 그 중첩 레퍼런스가 씬 최상위 레퍼런스로 올라온다**(`referenceQuery -parent` 가 None).
  중첩까지 임포트하려면 올라온 노드를 (load →) import 반복. 임포트 전후 최상위 노드 집합의 차로 잡는다.
- 임포트한 노드 이름은 네임스페이스가 그대로(`A:B:cube`). `namespace -removeNamespace -mergeNamespaceWithRoot` 를
  **깊은 것부터**. 로드된 레퍼런스의 네임스페이스는 못 지운다 — 남는 레퍼런스 것은 건너뛸 것. 이름이 겹치면 마야가
  끝 숫자를 올린다(`cube02` → `cube03`).
- **`.ma` 머리글의 `file -r` / `file -rdi N`(중첩, 깊이 포함) 문장은 `-op "..."` 때문에 여러 줄**이라 `;` 까지 이어 붙여
  파싱. `createNode` 가 나오면 머리글 끝. 씬을 열지 않아도 직접 레퍼런스를 안다. `.mb` 는 열어야 한다.
- FBX 는 `file -r -type FBX` 로 레퍼런스가 되고 importReference 도 된다(fbxmaya 플러그인 필요). 레퍼런스를 가질 수 없는 잎.
- `file -q -type` 이 `mayaAscii`/`mayaBinary` → 그 타입으로 제자리 저장. `-executeScriptNodes false` 로 남의 파일 스크립트 실행 방지.
- mayapy 배치에서 실제 리그 파일을 열면 renderSetup 콜백 트레이스백 · 레거시 렌더 레이어 경고가 뜨지만 작업엔 영향 없다.

관련: [[wip-a00480-maya-reference-tab]], [[mayapy-headless-verify]]
