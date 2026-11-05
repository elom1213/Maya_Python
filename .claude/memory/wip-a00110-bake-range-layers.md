---
name: wip-a00110-bake-range-layers
description: A00110_V02 v02.51 Bake > Bake 구간만 구울 때 구간 밖 키 보존 — 레이어 멤버에서 bakeResults 가 Base 키를 지우고 이중 계산, -smart 도 구간 밖을 바꿈
metadata:
  type: project
---

2026-11-05 v02.51 (`core/bake_manager.py`, 시험 `tests/test_bake_layers.py` 19).

- **★ 애니메이션 레이어 멤버 채널**에 `bakeResults -time s:e -preserveOutsideKeys` 를 쓰면 (mayapy 실측)
  ① Base 커브가 [s, e] 의 키만 남은 새 커브로 바뀐다(구간 밖 키 소실) ② 최종 합성값을 Base 에 써 넣어 위 레이어가 한 번 더 더해진다.
  keep / bake down 둘 다 컨스트레인트는 남긴다(blendParent 에도 키 없음). 레이어 없으면 정상.
- 해법 `bake_layered`: 컨스트레인트 켠 채 매 프레임 샘플 → 채널마다 대상 레이어(덮는 맨 위 **override**(뮤트 제외), 없으면 Base) 커브의
  [s, e] 만 cutKey(먼저 이웃 키 탄젠트 fixed + s-1 / e+1 `_insert_fixed` — 듬성한 커브는 안 하면 구간 밖 보간이 바뀐다) →
  `setKeyframe -animLayer 대상 -value` (마야가 위 레이어를 빼서 역산; pairBlend 가 끼어 있어도 맞다).
- **★ `bakeResults -smart` 는 레이어 없이도 구간 밖 값을 바꾼다**(preserveOutsideKeys 무시). **`filterCurve -simplify` 는 -tolerance 를 안 지킨다**
  (값과 무관하게 2 키 + spline 이 크게 벗어남). → smart = dense + 구간 안 Douglas-Peucker(`reduce_keys`) + cutKey 한 번(time 여러 개) + linear.
- 한계: **키가 없던 채널**의 원래 정적 값은 컨스트레인트를 거는 순간 pairBlend `inTranslate*1` 이 0 이 되어 못 되살린다 → 마야 기본(구간 밖에서 구운 끝값).

**Why:** 사용자는 구간만 구워도 나머지 애니메이션(레이어 포함)이 그대로이길 원한다. **How to apply:** 레이어 오브젝트를 구간 굽기 하는 다른 기능도
bakeResults 대신 이 경로를 쓸 것. 관련 [[wip-a00110-layer-range-merge]](같은 경계 처리), [[wip-a00110-hold-layer-blend]](setKeyframe -animLayer 역산).
