---
name: wip-a00110-layer-key-copy
description: A00110_animTool_V02 Transfer > Layer 탭 - 애님 레이어 사이 키 복사/잘라내기 (v02.13)
metadata: 
  node_type: memory
  type: project
  originSessionId: c9193b2f-22fa-4f73-9fcb-d5a3af9da721
  modified: 2026-08-31T01:24:27.865Z
---

`A00110_animTool_V02` **Transfer > Layer** (v02.13, 2026-08-31). 리스트업한 오브젝트의 키를
**한 애니메이션 레이어에서 다른 레이어로** 복사(Copy)하거나 옮긴다(Cut).
`app/core/layer_key_manager.py` + `main_window._build_layer_key_tab` / `on_lk_*`.

**Why:** 마야의 `Ctrl+C` / `Ctrl+V` 는 붙여넣기가 **지금 선택된 레이어**로 가 버려서, 오브젝트
여러 개의 레이어 간 키 복사가 온전히 되지 않는다(어떤 채널이 어디로 갔는지 확인할 방법도 없다).
그래서 **From / To 를 명시**하고 채널을 골라 한 번에 처리하는 경로를 따로 뒀다.

**How to apply:**
- 마야 명령의 실제 동작은 [[animlayer-copy-cut-traps]] 에 따로 적어 뒀다 — 이 탭의 구현이
  통째로 그 위에 서 있다(특히 `cutKey` 에 `animLayer` 가 없다는 것).
- **Copy Key 탭의 "9축 전부 ON = 필터 없음" 을 여기서는 쓸 수 없다.** 레이어 이동은 채널(plug)
  하나씩 copy/paste 해야 하고(노드 단위 `pasteKey` 는 클립보드 커브를 **이름이 아니라 순서로**
  맞춘다 — [[wip-a00110-copykey-custom-attrs]]), 그러면 언제나 명시 목록이 필요하다.
  대신 **`All Keyed Channels`** 체크박스가 그 역할을 한다(오브젝트마다 소스 레이어에 커브가
  있는 채널 전부). **9축을 다 켜도 "전부" 가 아니라 TRS 뿐**이라는 걸 UI 툴팁·문서에 적었다.
- **Custom Channels 는 소스 레이어에 키가 있는 채널만 나열**하고, **From 이 바뀌면 목록을 비운다** —
  남겨 두면 지금 소스에 없는 채널을 고른 채 실행하게 된다.
- **Cut 은 붙여넣기에 성공한 채널만 지운다.** 실패한 자리에서 원본이 사라지면 안 된다.
- 기본 Paste Option 은 **`replace`**(Copy Key 탭의 `insert` 와 다르다) — 레이어를 옮길 때
  원하는 건 "그 구간을 이 커브로 바꿔라" 이지 기존 키를 시간축으로 밀어내는 게 아니다.
- 로그에서 **키 없는 9축은 개수로만**, 사용자가 고른 커스텀 채널은 이름으로 적는다(9축이 기본
  전부 켜져 있어 이름을 다 적으면 한 줄이 안 읽힌다 — Copy Key 의 `_brief` 와 같은 취지).
- 검증은 mayapy headless 로 Qt 창을 실제 빌드해서 했다([[qapplication-before-maya-standalone]]) —
  비멤버 오브젝트 · DAG 긴 이름 · 네임스페이스까지 포함.
