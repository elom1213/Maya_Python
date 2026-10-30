---
name: maya-surface-cmd-not-undoable
description: cmds.surface(CV·노트로 NURBS 서피스 직접 정의)는 undo 큐에 오르지 않는다 — Ctrl+Z 가 뒤따른 명령만 되돌려 반쪽 상태. 서피스는 curve 둘 + loft(ch 없음) 로 만들 것
metadata:
  type: reference
---

`cmds.surface(du, dv, fu, fv, ku, kv, p, name)` 은 서피스를 만들지만 **undo 큐에 아무것도 남기지
않는다**(mayapy 2024 실측: 실행 직후 `undoInfo -q -undoName` 이 빈 문자열, `undo` 뒤에도 서피스가 남음).
`undoInfo(openChunk/closeChunk)` 로 감싸면 청크 안의 **다른** 명령(rename · sets)만 되돌아가
"이름만 원래대로 돌아간 서피스" 가 남는 반쪽 상태가 된다. [[maya-toggle-cmd-not-undoable]] 과 같은 종류.

덤으로 `cmds.surface` 는 **셰이프 이름**을 돌려주고(`surfaceShapeN`), `name` 은 트랜스폼에만 붙으며,
`initialShadingGroup` 에도 안 넣는다.

**Why:** A00400 Create > Ribbon(2026-10-30) 에서 서피스를 한 번에 정의하려다 회귀 T7(undo) 이 잡았다.

**How to apply:** CV · 노트가 손에 있어도 서피스는 **undo 되는 명령 조합**으로 만든다 —
`cmds.curve(p=, k=, per=)` 로 커브 둘(이 명령은 undo 된다, `k` 는 `MFnNurbsCurve.knots()` 형식 그대로) →
`cmds.loft(ch=False, autoReverse=False)` → 임시 커브 `delete`. loft 는 커브 노트를 U 로 그대로 쓴다.
`loft -d 1` 의 V 범위는 `0..2` 라 필요하면 `rebuildSurface(dir=1, kcp=True, kr=0)`. 구현: [[wip-a00400-ribbon]].
