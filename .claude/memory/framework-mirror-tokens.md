---
name: framework-mirror-tokens
description: 좌/우 미러 토큰 규칙은 Framework/rules/mirror_tokens.json 공용 한 파일(Framework.core.mirror_tokens). 이름 미러링은 경계 매칭이라 arm_lower / sample_lip_l_ctl 오탐을 막는다
metadata: 
  node_type: memory
  type: project
  originSessionId: 8a1f639d-1fbe-4096-98f7-2265e5589a17
  modified: 2026-09-07T01:06:16.938Z
---

좌/우 미러 토큰 규칙(`_l`↔`_r` …)은 **모든 툴이 공유하는 한 파일**이다
(2026-09-07 에 `A00110_animTool_V02/app/config/` 에서 옮겼다).

- 모듈: `Framework/core/mirror_tokens.py` — `MirrorTokenStore`
- 규칙 파일: `Framework/rules/mirror_tokens.json`
- 쓰는 곳: `A00110_animTool_V02`(Mirror Key) · `A00145_RigConnect`(Mirror 탭,
  [[wip-a00145-mirror-tab]])
- A00110_V02 의 `app/core/mirror_token_store.py` 는 **기존 import 경로를 살리는 얇은
  재노출**만 남았다. 새 코드는 Framework 를 직접 쓴다.
- 문서: `docs/Framework_mirror_tokens.md`

**★ 이름 미러는 단순 substring 치환이면 조용히 틀린다.** `opposite_name()` 은
**토큰 경계에서 끝나는 occurrence 만** 인정한다(뒤가 `_`/문자열 끝/숫자/대문자,
앞이 비영숫자거나 camelCase 경계).

| 이름 | 단순 치환 | 경계 매칭 |
|---|---|---|
| `sample_lip_l_ctl` | `sample_rip_l_ctl` ❌ | `sample_lip_r_ctl` |
| `arm_lower` | `arm_rower` ❌ | 토큰 없음 |
| `jnt_lf_01` | `jnt_rf_01` ❌ (`_l` 이 먼저 걸린다) | `jnt_rt_01` (`_lf` 까지 내려간다) |
| `Leftover` | `Rightover` ❌ | 토큰 없음 |

`opposite_name()` 은 **씬을 보지 않는다**(아직 없는 반대쪽 이름을 만들어야 하니까).
씬에 있는 짝을 찾는 쪽은 A00110 의 `MirrorKeyManager._find_opposite`(objExists 로 거른다).
`mirror_node_name()` 은 DAG 경로의 마지막 조각만 바꾸고 **네임스페이스는 남긴다**
(짧은 이름으로 rename 하면 네임스페이스가 벗겨진다 — [[maya-set-rename-traps]]).
