---
name: wip-a00110-copykey-one-to-many
description: "A00110_animTool_V02 v02.06 — Copy Key gets a \"1 -> n\" checkbox (default ON) that fans one Base out to every Target, silently falling back to n->n (unlike Follow's 1<-n which errors)"
metadata: 
  node_type: memory
  type: project
  originSessionId: 5daa567a-aa4a-4115-99c6-ec8bdb8c00eb
  modified: 2026-08-19T00:50:33.871Z
---

`A00110_animTool_V02` **v02.06** — `Transfer > Copy Key` 에 **`1 -> n`** 체크박스(**기본 ON**).
Base 가 **정확히 1개**면 그 키를 **모든 Target** 에 복사한다. 예전에는 `Base[i] → Target[i]` 뿐이라
Base 1 / Target 3 이면 **첫 타깃 하나만** 받고 개수 불일치 경고만 떴다.

`copykey_manager.copy_keys(..., one_to_many=True)` — `fan_out = one_to_many and len(base)==1`
일 때만 `[(base[0], t) for t in tgt]`, 아니면 예전대로 `zip` (짧은 쪽 기준).

**⚠️ Follow 탭의 `1<-n` 과 동작이 다르다.** `follow_match_manager` 는 개수가 안 맞으면
`[Warning]` 을 내고 **아무것도 하지 않는다**. Copy Key 는 옵션이 켜져 있어도 Base 가 여러 개면
**조용히 `n->n` 으로 폴백**한다 — 사용자가 명시한 요구 사항이고, 그래야 **늘 켜 둔 채로**
기존 n->n 작업이 그대로 된다(그래서 기본 ON 이 안전하다). 두 탭 중 하나를 고칠 때 다른 쪽 규칙을
그대로 가져오지 말 것.

부수 규칙 둘:
- 로그에 **어느 모드로 처리했는지**(`1->n` / `n->n`) 를 찍는다. 폴백이 조용하므로 이게 유일한 단서다.
- **개수 불일치 경고는 `n->n` 일 때만.** `1->n` 은 Base 1 / Target 4 가 정상이라 예전 경고를 그대로
  두면 성공한 작업에 경고가 붙는다. 대신 옵션이 켜진 채 `n->n` 으로 떨어지면
  `"1->n needs exactly 1 Base, got 3"` 을 덧붙인다.

**헤드리스 UI 테스트 팁**: TSL 위젯은 `set_items([...])` 로 직접 채운다(`select_objects` 같은 건
없다). `MainWindow` 는 [[qapplication-before-maya-standalone]] 순서만 지키면 mayapy 에서 뜬다 —
[[wip-a00110-windtool]] 계열 메모에 적힌 "headless 로 못 만든다" 는 그 순서 전의 이야기.

검증: mayapy 2024 코어 30 + UI 8 항목 통과(1->n 전 타깃 동일 키, OFF 면 옛 동작, Base 3 면 인덱스
매칭, Reverse 축 적용, **undo 한 번에 전 타깃 복귀**, 가드 유지, 체크 상태가 매니저 인자까지 도달).

관련: [[wip-a00110-tab-taxonomy]], [[undo-chunk-by-default]], [[ui-text-english-only]],
[[mayapy-headless-verify]].
