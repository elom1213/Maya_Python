---
name: maya-codepage-nonascii-traps
description: Maya 2024 on Korean Windows (cp949) cannot load texture paths or keep .ma strings with characters outside the code page; getVertexNormal ignores locked normals
metadata:
  node_type: memory
  type: project
  originSessionId: a9d7bd20-6410-453e-9d1a-03779fdc3ff3
  modified: 2026-11-09T01:04:46.419Z
---

mayapy 2024 실측(2026-11-09, 한국어 Windows = `cmds.about(codeset=True)` → `949`):

- **file 노드 경로에 cp949 밖 글자(`颜` · `体` 같은 간체자)가 있으면 이미지를 못 읽는다.** `cmds.setAttr` / MEL 은 글자를 `?` 로 바꾸고,
  API `MPlug.setString` 은 글자는 남지만 `outSize = 0`. 일본 가나 · `髮` 처럼 cp949 에 있는 글자는 괜찮다.
  8.3 짧은 경로는 읽히지만 이식성이 없다. 해법 = `path.encode("cp" + codeset)` 가 실패하는 경로만 ASCII 이름으로 **복사**해 연결.
- **`.ma` 는 시스템 코드페이지로 저장**되어 문자열 어트리뷰트의 cp949 밖 글자가 `?` 로 깨진다(`.mb` 는 유지). 열 때
  `Error: This file contains data that cannot be converted to the encoding of the current locale` 가 뜬다.
  해법 = 커스텀 문자열 어트리뷰트는 ASCII 로만(이름 = FBXASC, JSON = `ensure_ascii=True`).
- `MFnMesh.getVertexNormal(i, angleWeighted)` 는 **잠긴(사용자) 노멀을 무시**하고 기하 평균을 준다 — 노멀을 확인할 땐
  `getFaceVertexNormal` 또는 `polyNormalPerVertex -q -xyz`.
- 트랜스폼을 `cmds.createNode` 로 만들고 그 아래 `MFnMesh.create(parent=...)` 로 셰이프를 만들면 **undo 청크 하나에 같이 사라진다**
  (API 로 쓴 웨이트 · 노멀 · blendShape 타깃도 노드째 사라짐). redo 는 보장 안 됨.

**Why:** A00610_PmxImporter 에서 PMX 텍스처(`tex\颜.png`)가 안 보이고, 원본 이름 어트리뷰트가 `.ma` 왕복에서 깨졌다.
**How to apply:** 외부(일본 · 중국) 에셋 경로나 이름을 마야에 넣는 툴은 위 두 가지를 먼저 막는다. 관련 [[wip-a00610-pmximporter]], [[mayapy-headless-verify]].
