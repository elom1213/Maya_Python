---
name: no-history-rewrite-master-on-request
description: git 히스토리 재작성 금지, master 최신화는 사용자가 그 턴에 요청할 때만
metadata:
  node_type: memory
  type: feedback
---

**히스토리 재작성은 하지 않는다.** `git filter-repo` / `filter-branch` / `rebase` 로 과거 커밋을
다시 쓰거나, 이미 push 된 것을 `--force` 로 덮는 제안·실행 모두 금지. 사용자가 직접 지시하지 않는 한
"공개 저장소 과거 커밋에 남은 문서를 지우려면 히스토리를 고쳐야 한다" 같은 상황에서도 실행하지 않는다.
남아 있다는 **사실만 보고**하고 판단은 사용자에게 넘긴다.

**`master` 브랜치 최신화(dev → master 병합/푸시)는 사용자가 그 턴 메시지에서 명시로 요청할 때만** 한다.
`dev` 가 `origin/master` 보다 100+ 커밋 앞서 있는 게 정상 상태다 — 뒤처진 걸 보고 알아서 따라잡히지 말 것.
[[push-only-when-asked]] 와 같은 규칙이며, 앞 턴의 요청은 이어지지 않는다.

**Why:** 2026-08-21 학습 노트를 JUN_Study 로 분리하면서, public 인 `elom1213/Maya_Python` 의
`origin/master` 에 옛 study 문서(서드파티 역분석 노트 포함)가 남는 문제를 보고했다. 사용자는
"히스토리 재작성은 하지 마. master 최신화는 나중에, 내가 요청할 때까지 하지 마" 라고 명시했다.
되돌리기 어렵고 공개 저장소에 영향을 주는 작업이라 타이밍을 본인이 정하겠다는 뜻.

**How to apply:** Maya_Python 의 push 대상은 계속 `Dnable_repo/dev`([[push-target-dnable-dev]]).
`origin`(public) 으로는 요청 없이 push 하지 않는다. 관련: [[study-docs-number-prefix]], [[jun-mgear-vault]]
