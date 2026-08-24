---
name: wip-a00110-copykey-custom-attrs
description: A00110_V02 Copy Key 에 Custom Channels 목록 — 9축 필터가 커스텀 어트리뷰트를 조용히 버리던 문제 (v02.12)
metadata: 
  node_type: memory
  type: project
  originSessionId: 1297e1ce-ccdd-4239-b26f-c343d3aee025
  modified: 2026-08-24T00:11:33.197Z
---

A00110_animTool_V02 `Transfer > Copy Key` v02.12 (2026-08-24).

**원래 문제**: v02.08 의 Attributes 9축 체크박스가 **전부 켜져 있을 때만** `copyKey` 에
필터를 안 걸어(= 커스텀 채널까지 통째로 복사) 동작했다. **하나라도 체크를 풀면** 필터가
`translateX ... scaleZ` 로 좁혀져 `ikBlend` · 페이셜 슬라이더 키가 **조용히 빠졌다**.
"회전 + `ikBlend`" 처럼 TRS 일부와 커스텀을 함께 고를 길이 없었다.

**Why:** 기본값(9축 전부 ON)에서는 멀쩡해 보여서, 사용자는 "TRS 만 복사된다" 로 인지한다.

**How to apply:** Attributes 그룹 안 `Custom Channels` 목록(`List Attributes` + 공용 Filter +
Select All/Clear)에서 고른 채널이 체크된 9축과 합쳐진다. 채널 판정은 Fill Keys 와 같은
`listAttr(keyable=True, visible=True, unlocked=True)` — 툴 전체에서 "채널박스에서 키 찍을 수
있는 것" 의 뜻을 하나로 통일. **아무것도 안 고르면 예전 경로(필터 없음) 그대로**라 회귀 없음.
명시 필터 경로는 채널 단위 copy/paste 로 돌린다 — 이유는 [[pastekey-attribute-matches-by-order]].

관련: [[wip-a00110-copykey-one-to-many]], [[wip-a00110-fill-keys]], [[wip-a00110-tab-taxonomy]]
