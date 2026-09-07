---
title: Framework.core.mirror_tokens — 좌/우 미러 토큰 규칙(공용)
aliases: [mirror_tokens, MirrorTokenStore, mirror token, L/R token, 미러 토큰]
tags: [maya-python, framework, mirror, naming, rules]
updated: 2026-09-07
---

# `Framework.core.mirror_tokens`

이름의 **좌/우 토큰**(`_l` ↔ `_r` …)을 한 곳에서 관리한다. 규칙 파일은
**모든 툴이 공유하는 한 개**다.

- **모듈**: `JUN_All/Framework/core/mirror_tokens.py`
- **규칙 파일**: `JUN_All/Framework/rules/mirror_tokens.json`
- **쓰는 곳**: `A00110_animTool_V02`(Mirror Key), `A00145_RigConnect`(Mirror 탭)

---

## 1. 왜 Framework 로 올렸나

원래 이 규칙은 `A00110_animTool_V02/app/config/mirror_tokens.json` 안에 있었다.
미러가 필요한 툴이 늘면서 **툴마다 토큰 목록이 갈라지는** 문제가 생겼다 — animTool 에서
토큰을 추가해도 다른 툴은 모른다. 좌/우 이름 규칙은 리그 전체에 하나뿐인 약속이라
`Framework/rules/` 로 올려 한 파일만 읽고 쓴다.

기존 import 경로(`from .mirror_token_store import MirrorTokenStore`)는
A00110_V02 쪽에 **얇은 재노출 모듈**을 남겨 그대로 살아 있다.

---

## 2. 스키마

```json
{
  "version": 1,
  "token_pairs": [
    {"left": "_l",   "right": "_r",     "enabled": true},
    {"left": "_L",   "right": "_R",     "enabled": true},
    {"left": "_lf",  "right": "_rt",    "enabled": true},
    {"left": "Left", "right": "Right",  "enabled": true}
  ]
}
```

**위 → 아래 순서가 매칭 우선순위**다. 구체적인 토큰을 위에 둔다.
`load()` 는 `enabled` 인 쌍만 돌려주고, 파일 없음 / 파싱 실패 / 빈 목록이면
코드 내장 `DEFAULT_TOKEN_PAIRS` 로 폴백해 **언제나 동작한다**.

---

## 3. API

```python
from Framework.core.mirror_tokens import MirrorTokenStore

pairs, msg = MirrorTokenStore.load()            # [('_l','_r'), ...]
MirrorTokenStore.save(pairs)                    # UI 편집 결과 기록
MirrorTokenStore.json_path()                    # 규칙 파일 절대 경로

MirrorTokenStore.opposite_name("jnt_l_01", pairs)      # ('jnt_r_01', '_l')
MirrorTokenStore.mirror_node_name("|grp|jnt_l_01", p)  # ('jnt_r_01', '_l')
```

- `opposite_name()` 은 **씬을 보지 않는다**(순수 문자열). 아직 없는 반대쪽 이름을
  만들어야 하는 미러 툴이 쓰는 진입점이다.
- `mirror_node_name()` 은 DAG 경로의 **마지막 조각만** 바꾸고 짧은 이름을 돌려준다
  (`cmds.rename` 이 받는 형태). 네임스페이스는 남긴다 — 짧은 이름으로 rename 하면
  네임스페이스가 벗겨지기 때문이다.
- 토큰을 못 찾으면 `(None, None)`. 호출부가 "센터라서 미러 대상이 아니다" 를
  판단할 수 있다.

---

## 4. ★ 경계(boundary) 매칭 — 단순 치환의 함정

토큰 `_l` 을 그냥 substring 으로 바꾸면 이런 일이 난다:

| 이름 | 단순 치환 | 옳은 결과 |
|------|-----------|-----------|
| `sample_lip_l_ctl` | `sample_rip_l_ctl` ❌ | `sample_lip_r_ctl` |
| `arm_lower` | `arm_rower` ❌ | (토큰 없음) |
| `jnt_lf_01` | `jnt_rf_01` ❌ (`_l` 이 먼저 걸린다) | `jnt_rt_01` |
| `Leftover` | `Rightover` ❌ | (토큰 없음) |

이름 매칭이 **조용히 틀리는 것**이 제일 위험하다 — 미러 툴에서는 엉뚱한 노드에
웨이트를 얹거나 컨스트레인트를 잘못 건다. 그래서 `opposite_name()` 은
**토큰 경계에서 끝나는 occurrence 만** 인정한다.

- 뒤: 문자열 끝 · 비영숫자(`_`, `:`) · 숫자(토큰이 숫자로 안 끝날 때) ·
  대문자(토큰이 소문자로 끝날 때)
- 앞: 문자열 처음 · 비영숫자 · 토큰 자체가 구분자로 시작(`_l`) ·
  camelCase 경계(`armLeft`)

경계 매칭 덕분에 우선순위가 위인 `_l` 이 `jnt_lf_01` 을 삼키지 않고 `_lf` 쌍까지
내려간다. 경계를 만족하는 occurrence 는 **전부** 치환한다(`l_arm_l_01` → `l_arm_r_01`
— 앞의 `l_` 는 토큰이 아니라 그대로다).
