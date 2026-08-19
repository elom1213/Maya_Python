---
name: wip-a00145-match-one-to-many
description: "A00145_RigConnect v01.32 — Match tab gets a \"1 <- n\" checkbox (default ON) fanning one target out to every follower; pairing lives in one shared resolve_pairs() so UI log and behaviour cannot drift"
metadata: 
  node_type: memory
  type: project
  originSessionId: 5daa567a-aa4a-4115-99c6-ec8bdb8c00eb
  modified: 2026-08-19T01:21:35.602Z
---

`A00145_RigConnect` **v01.32** — Match 탭에 **`1 <- n`** 체크박스(**기본 ON**).
Targets 가 **정확히 하나**면 Followers **전부**를 그 하나에 매칭한다. Targets 가 2개 이상이면
켜져 있어도 평소대로 `n <- n`(인덱스 1:1) — 조용히 폴백한다.

**짝짓기는 `match_manager.resolve_pairs(targets, followers, one_to_many)` 하나에만 둔다.**
`(pairs, fan_out, unpaired)` 를 돌려주고 **`match()` 와 UI 가 같이 쓴다.** 모드 판정을 두 군데서
따로 하면 **로그에 찍히는 모드와 실제 동작이 어긋난다** — 여기는 로그·개수 불일치 경고·캐시 타겟
개수까지 전부 같은 판정을 봐야 해서 함수로 뽑는 편이 안전했다.
(같은 기능을 A00110 Copy Key([[wip-a00110-copykey-one-to-many]])에도 넣었는데 그쪽은 UI 가 조건을
따로 계산한다. 새로 손대면 이쪽 방식으로 통일할 것.)

**⚠️ `parent` 패스도 같은 `pairs` 를 써야 한다.** 예전 코드는 `for i in range(n): targets[i]` 였다 —
그대로 뒀으면 `1 <- n` 에서 팔로워 2번이 **없는 `targets[1]` 을 찾아 터진다.** 인덱스 루프를
짝 리스트 루프로 바꿀 때 이런 병렬 루프가 더 없는지 확인할 것.

**개수 불일치 경고는 `n <- n` 일 때만.** `1 <- n` 은 Targets 1 / Followers 4 가 정상이라 예전 경고를
그대로 두면 성공한 작업에 경고가 붙는다. 옵션이 켜진 채 `n <- n` 으로 떨어지면
`(1 <- n needs exactly 1 target, got 3)` 을 덧붙여 왜 안 펼쳐졌는지 알린다.

**타겟 종류별 규칙은 그대로다** — `1 <- n` 은 짝짓기만 바꾼다. 메시 타겟이면 팔로워 전부가
centroid 로 **위치만**(회전 안 함), 버텍스 타겟이면 전부가 같은 노말 정렬 회전까지 받는다.
> 테스트 함정: `polyCube` 를 타겟으로 쓰면 shape 가 `mesh` 라 **메시 타겟(위치만)** 으로 분류된다.
> 회전까지 보려면 `spaceLocator` 처럼 mesh 가 아닌 타겟을 써야 한다. 나는 이걸로 한 번 헛짚었다.

검증: mayapy 2024 코어 25 + UI 10 항목. UI 는 `MainWindow` 를 띄워 `tsl_match_tgt.set_items(...)`
로 채우고 **`on_match()` 실제 경로**로 세 모드를 확인했다([[qapplication-before-maya-standalone]]).

관련: [[wip-a00145-match-dootool-options]], [[wip-a00145-match-cache]], [[ui-text-english-only]],
[[mayapy-headless-verify]].
