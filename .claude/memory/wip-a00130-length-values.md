---
name: wip-a00130-length-values
description: A00130_ControlRig_V02 Length 탭 — 템플릿 조인트 거리를 옵션 컨트롤러 12개 어트리뷰트에. total 은 직선이라 up+low 와 다르다, min/max 는 안 자르고 예외, ls 와일드카드는 네임스페이스를 안 넘고 셰이프를 잡는다 (v02.01)
metadata:
  type: project
---

**`A00130_ControlRig_V02` 의 `Length` 단계** (v02.01, 2026-08-28) —
템플릿 조인트 사이 거리를 재서 **옵션 컨트롤러 어트리뷰트에 쓴다.**
계획서: `JUN_All/docs/plans/A00130_ControlRig_V02_length_plan.md`.
V01 근거: `A00130_ControlRig/app/core/rig_matcher.py:255 · 293 · 306 · 319`.

**V01 은 아바타 본을 쟀고 그 본을 TSL 에 손으로 순서대로 담아야 했다.**
V02 는 **템플릿 조인트**를 재고 짝은 `length_map.json` 이 갖는다 — 값은 같고
아바타의 조인트 이름에 의존하지 않는다. [[wip-a00130-v02-match]] 와 같은 패러다임.

**어트리뷰트는 12개다** — 부위(팔 좌우·다리 좌우)마다 `total`·`_up`·`_low` 셋.
V01 툴과 아카이브 전 버전(`01_Modules` · `03_Modules_Test`)을 훑어 **12개가 전부**임을 확인했다.
**`Arm_L` ↔ `Arm_r` 로 좌우 표기가 깨져 있어**(대문자 vs 소문자) **대칭으로 유도하지 않고
json 에 전부 적는다** — 유도하면 한쪽이 조용히 틀린다.

> **요약이 오해를 만든 사례.** 계획서에는 12개가 다 있었는데, 내가 채팅 요약 표에서
> Leg 두 줄을 한 줄로 합치고 위/아래 칸을 `…` 로 줄여 **8개가 빠진 것처럼 읽혔다.**
> → 계획서에 **낱개로 번호 매겨 못박고**, 검증이 **개수를 세도록** 했다.
> **표를 줄일 때는 "무엇을 줄였는지" 가 보이게 줄인다.**

**실측 네 가지** ★

- **`total` 은 `up + low` 가 아니라 직선 거리다** — 세 조인트가 직렬이라 가운데를 무시한다.
  30° 굽으면 **3.4 % 짧고** 5° 면 0.10 %. IK 스트레치 기준이면 보통 **합**이 맞지만
  **조용히 바꾸지 않고** 기본값은 V01 그대로(`straight`) 두고 `Total` 콤보로 고르게 했다.
  0.5 % 넘게 벌어지면 표에 `bent - straight ... vs sum ...`.
- **`min`/`max` 는 자르지 않고 예외를 낸다** (`past its maximum value of 10`, 값은 그대로 0).
  → **잘라 쓰지 않고 거부한다.** 잘린 길이는 틀린 리그를 조용히 만든다.
  ([[addattr-min-max-raises-not-clamps]] 와 같은 함정)
- **거리는 씬 선형 단위를 탄다** — 같은 두 점이 `cm` 10 · `m` 0.1 · `mm` 100.
  **단위를 바꾸지 않고 `Measured in cm` 로 표시만** 한다. 미리보기 값이 100배 다르면 이것.
- **없는 어트리뷰트에 `setAttr` 은 `RuntimeError`** 이고 **V01 은 그 자리를 안 감쌌다**
  (`try/except` 는 임시 조인트 삭제 자리에만). 예외가 `on_match` 밖으로 올라가
  **Match 전체가 멈춘다** → 그래서 **`.Arm_r` 은 오타가 아니라 실제 이름일 가능성이 높다.**
  V02 는 쓰기 전에 **존재·잠금/연결·범위를 전부 미리 보고** 막힌 것만 건너뛴다
  (판정은 `su.plug_writable`, [[getattr-settable-lies-for-constrained]]).

**옵션 컨트롤러 찾기 — 세 함정이 겹쳐 아무것도 못 찾았다** ★ (사용자 보고)

1. **V01 의 `TKN_OPTION_CTL` 은 전체 이름이 아니라 토큰이었다.**
   실제 이름은 **`CH_n_OptionAll_xx_ctl`**, 상수는 `OptionAll_xx_ctl`, V01 은
   `if self.tkn_optionCtl in obj` 로 **부분 매칭**했다. 상수 이름의 **`TKN`** 이 이미
   말해 주고 있었는데 쓰는 쪽을 안 봤다.
   → **상수를 새 툴로 옮길 때는 "그 상수가 어떻게 쓰이는지" 를 함께 옮긴다.**
2. **`cmds.ls("*tok*")` 는 네임스페이스를 넘지 않는다** — 노드가 `CAGE:...` 면
   **빈 목록**. `recursive=True` 라야 한다. (레퍼런스 케이지에서 폴백조차 못 갔다)
3. **`ls` 가 셰이프까지 잡는다** — 컨트롤러는 nurbsCurve 라 `...ctlShape` 동반 →
   후보 2개 → **"여럿이면 멈춘다" 에 잘못 걸린다.** `type="transform"` 필요.

**자동 3단계 + 수동 보장**: `수동 지정 > su.resolve(정확한 이름) > token_search(부분 매칭)`.
`how` 를 UI 에 항상 표시한다(`set by hand` / `found by name` / `matched by name - check...`).
**`Get Selected`**(셰이프면 트랜스폼으로 올림) · **`Auto`** · 이름 직접 입력.
**여럿이면 여전히 고르지 않는다** — V01 은 `rnm_optionCtl[0]` 으로 첫 개를 골랐다.

> **리그 이름 규칙은 프로젝트마다 다르다 — 자동 탐지는 편의고, 수동 지정이 보장이다.**
> 이름으로 노드를 찾는 기능에는 **처음부터 수동 지정 경로를 같이 만든다.**

**부위 추가는 json 한 항목** — 코드를 안 고친다. `chain` 은 2개 이상, `upper`/`lower` 는
**정확히 3개일 때만** 뜻이 있다. `chain` 의 조인트 이름은 **로드 시** `template_map.json` 과
대조해 오타를 잡는다(씬에서 조용히 0 이 되지 않는다).

**검증 Length 126 + Match 88 = 214항목.**
**변이 테스트로 검증을 검증했다** — `_up`/`_low` 8개를 빼면 **27항목**, `option_ctl` 을
옛 토큰으로 되돌리면 **3항목**이 실패한다.
**누락을 실제로 잡는지 확인하지 않은 테스트는 통과해도 의미가 없다.**
[[mayapy-headless-verify]] · [[qapplication-before-maya-standalone]] · [[undo-chunk-by-default]]
