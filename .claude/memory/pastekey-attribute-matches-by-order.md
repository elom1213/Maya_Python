---
name: pastekey-attribute-matches-by-order
description: "노드 단위 cmds.pasteKey(attribute=[...]) 는 클립보드 커브를 이름이 아니라 순서로 맞춘다 — 채널(plug) 단위로 돌려야 안전"
metadata: 
  node_type: memory
  type: reference
  originSessionId: 1297e1ce-ccdd-4239-b26f-c343d3aee025
  modified: 2026-08-24T00:11:17.506Z
---

`cmds.copyKey(node, attribute=[...])` + `cmds.pasteKey(node, attribute=[...])` 조합은
클립보드 커브를 **어트리뷰트 이름이 아니라 순서(인덱스)로** 붙인다.

mayapy 2024 확인: `src.myFloat` 에만 키가 있는 상태에서
`copyKey(src, attribute=["translateY","myFloat"])` → 커브 1개 복사 →
`pasteKey(dst, attribute=["translateY","myFloat"])` 하면 그 커브가 **`dst.translateY` 에
들어간다**. 목록에 키 없는 채널이 섞이는 건 흔한 일이라 실제로 터진다.

**How to apply:** 복사할 채널을 명시할 때는 노드+attribute 대신
`copyKey(node + "." + attr)` / `pasteKey(node + "." + attr)` 로 **채널 하나씩** 돈다.
덤으로 일부 채널이 없거나 잠겨 있어도 나머지는 붙고, 채널별로 실패 사유를 로그에 남길 수 있다
(없는 plug 는 `objExists` 로 미리 거르고, 잠긴 타깃은 `RuntimeError: Nothing to paste to`).

관련: [[wip-a00110-copykey-custom-attrs]], [[list-attrs-multi-detection]]
