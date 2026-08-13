---
name: wip-a00170-lip-seal
description: A00170 Seal 탭 — 입술 지퍼(끝에서 중앙으로 다물기). pairBlend 삽입 + u 는 POCI 파라미터에서 (v01.16)
metadata:
  node_type: memory
  type: project
---

A00170_driverTool **`Seal` 탭** (v01.15→**01.16**, 2026-08-13). 계획서: `docs/plans/A00170_Seal_plan.md`.
AttachCrv > Edge Loop 로 만든 위/아래 입술 리그를 **지퍼처럼** 다문다.

**구조**: 조인트 쌍의 커브 위 두 점을 `blendColors(sealBias)` 로 섞은 점 = 다물리는 자리(라이브).
조인트별 가중치 `w = clamp01( ramp(sealR - u(1-band)) + ramp(sealL - (1-u)(1-band)) )` 를
**기존 `decomposeMatrix → null.translate` 사이에 끼운 `pairBlend`** 의 weight 로 쓴다.
`sealR`/`sealL` 이 독립이라 양 끝에서 중앙으로 동시에 닫힌다.

**설계 판단**
- 조인트를 건드리지 않고 **널 단계**에서 해결한다 — 조인트는 널을 따라가므로 스킨까지 그대로 온다.
- `pairBlend` 를 쓴 이유: translate/rotate 를 한 노드에서 가중 블렌드하고, **끼웠다 빼기가 쉽다**
  (Remove 가 in1 의 소스를 다시 널에 이어 준다). 2023 에도 있다([[maya-2023-compat]]).
- band 를 라이브로 두려고 `1-band` 를 한 번만 만들어 모든 쌍이 공유한다.
- 생성 노드를 `<prefix>_seal_SET` 에 담아 Remove 가 정확히 되돌린다.

**함정**
- **`u` 를 생성 순서로 잡으면 지퍼가 뒤집힌다.** Edge Loop 가 만든 `up_null_01..09` 의 커브
  파라미터가 이름 순서와 **역순**이었다(실측). POCI `.parameter` 를 `minValue/maxValue` 로 정규화하고,
  위/아래 커브 방향이 반대면 월드 축 기준으로 뒤집어 맞춘다.
- `blendColors` 의 출력 성분은 **`outputR/G/B`** 다(X/Y/Z 아님).
- 코너(입 끝)는 두 입술이 공유하므로 기본 제외.

검증: 코어 26 + UI 20 항목([[mayapy-headless-verify]]). v1 은 **위치만** 블렌드(회전은 후속).
