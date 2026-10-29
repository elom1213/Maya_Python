---
name: wip-a00110-layer-key-copy
description: A00110_animTool_V02 Transfer > Layer 탭 - 애님 레이어 사이 키 복사/잘라내기 (v02.13) · v02.28 Move 는 월드 결과 보존(Keep Result)
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

**v02.28 (2026-10-29) — Move(Cut) 는 최종 평가값(월드 위치·회전)을 보존한다(`Keep Result`, 기본 ON).**
사용자 관찰("Base 에만 키가 있는 ctl 을 Base → a 로 옮기면 월드가 달라진다")이 사실이었고, 실측으로는
a → b · a → Base 도 같은 이유로 어긋난다. 원인·처방은 [[animlayer-copy-cut-traps]] §5·§6.
- 구현: `transfer_keys(keep_result=True)` → `_blend_chain` · `_move_info`(붙여넣기 **전에** 대상 정적값과
  소스 blend 입력을 읽는다 — 붙여넣으면 `inputB` 가 커브에 연결돼 정적값을 잃는다) · `_compose_destination`
  (대상 정적값을 붙여넣은 키에 합성) · `_neutralize_source`(커브 사라짐 → 입력에 identity, 남음 → `s` step ·
  `e` identity 키, override 소스 → `removeAttribute`).
- 구간 이동은 Merge Layers 의 경계 규칙을 그대로(소스 `s-1`·`s`·`e`·`e+1` insert fixed + **바로 바깥 이웃 키도
  fixed**(auto 는 이웃이 바뀌면 재계산), 대상 `s-1`·`e+1` 에 대상의 옛 정적값 키). 정수 프레임 · 구간 안팎
  반 프레임 1e-15.
- 정확히 안 되는 경우는 로그 `Not exact:` 로만(거부하지 않는다): 대상에 이미 키(replace) · weight≠1 ·
  by-layer 회전에 0 아닌 회전 합성(0.30 근사) · override 소스 구간 · 키 없는 override 멤버 대상 · 비수치 채널.
- Copy 는 예전처럼 값 그대로. 회귀 `tests/test_layer_key_move.py` 68/68(UI 스모크 포함). **GUI 실기 확인 아직.**
- 테스트 씬 함정: **키 없는 override 멤버는 정적값으로 아래를 전부 덮는다** — override 대상 시험은 멤버로
  넣지 않은 채널로 해야 뜻이 있다.
