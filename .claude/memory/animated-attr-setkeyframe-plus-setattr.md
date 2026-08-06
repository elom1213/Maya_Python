---
name: animated-attr-setkeyframe-plus-setattr
description: 애니메이션 걸린 attr 을 UI 로 조절하려면 setKeyframe 뒤에 setAttr 까지 내야 값이 즉시 반영된다 (undo 1회 유지 효과도 있음)
metadata: 
  node_type: memory
  type: reference
  originSessionId: bd9316fd-23fb-411b-9399-46ea0f0d81be
  modified: 2026-08-06T02:17:06.819Z
---

키(animCurve)나 애니메이션 레이어가 걸린 attr 을 슬라이더/스핀박스로 조절할 때 (mayapy 2024 실측,
DG · EM parallel 동일):

1. **`setKeyframe` 만으로는 값이 그 자리에서 안 바뀐다.** 커브에는 키가 들어가지만 plug 값은
   **시간이 다시 흐르거나 강제 재평가(dgeval/currentTime)** 가 있어야 갱신된다. → 드래그해도
   뷰포트가 꿈쩍 안 하고, 폴링으로 되읽는 UI 는 옛 값을 보여 슬라이더가 튕겨 돌아간다.
2. **키 걸린 plug 에 `setAttr` 은 에러를 내지 않는다.** 연결돼 있어도 값이 **즉시** 바뀐다
   (다음 재평가 전까지 유효한 미리보기 — 마야 채널박스에서 autokey 없이 키 걸린 값 만지는 것과 동일).
   애니메이션 레이어(`animBlendNode*`)로 구동되는 plug 도 같다.
3. **Auto Keyframe 이 켜져 있으면 마야가 `setAttr` 마다 자체 키를 찍는데, 그 키는 내가 연
   undo 청크 밖에 별도 항목으로 쌓인다** → Ctrl+Z 두 번 필요. 키를 **내가 먼저** 찍어 두면
   뒤따르는 `setAttr` 이 같은 값이라 마야의 자동 키가 개입하지 않아 제스처 1개 = undo 1개.

**Why:** A00290 Shape Editor 에서 "키 걸린 타겟은 슬라이더가 반응만 하고 조절이 안 된다" 는
버그의 원인(v01.07~v01.13). v01.14 에서 `setKeyframe → setAttr` 순서로 고쳤다.

**How to apply:**
- 순서를 고정: `if autokey: cmds.setKeyframe(plug, value=v)` → `try: cmds.setAttr(plug, v)`.
  autokey 가 꺼져 있으면 setAttr 만(= 미리보기, 스크럽하면 커브로 복귀).
- "드래그 중엔 미리보기, 놓을 때 한 번만 키" 최적화는 **하지 말 것** — 위 3번 때문에 오히려
  undo 가 2회가 되고, 어차피 마야가 매 setAttr 마다 키를 찍는다.
- **애니메이션 레이어에 들어간 attr 은 소스가 `animCurve*` → `animBlendNode*` 로 바뀐다.**
  `listConnections(scn=True)` 로 소스 타입을 볼 때 `animBlendNode` 접두사를 따로 인정하지 않으면
  "다른 노드가 구동 중 = 조절 불가" 로 오분류된다.

관련: [[wip-a00290-shape-editor-tab]], [[mayapy-headless-verify]], [[undo-chunk-by-default]]
