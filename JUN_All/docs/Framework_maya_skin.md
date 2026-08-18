---
title: Framework.core.maya_skin — skinCluster 웨이트 인덱스(물리 vs 논리)
aliases: [maya_skin, setWeights, getWeights, influence index, kInvalidParameter]
tags: [maya-python, framework, skincluster, weights, undo, gotcha]
updated: 2026-08-18
---

# `Framework.core.maya_skin`

`MFnSkinCluster` 의 웨이트 API 에는 **인덱스가 두 종류**라는 함정이 있다. 이 모듈은 그 둘을
이름으로 갈라 놓아 헷갈릴 수 없게 한다.

- **모듈**: `JUN_All/Framework/core/maya_skin.py`
- **형제 문서**: [Framework.core.maya_shape](Framework_maya_shape.md) — "어느 셰이프인가" 쪽 함정

---

## 1. 물리 인덱스 vs 논리 인덱스

| | 뜻 | 얻는 법 | 쓰는 곳 |
|---|---|---|---|
| **물리(physical)** | `influenceObjects()` 가 돌려준 배열에서의 **자리**(0,1,2,…). `getWeights` 웨이트의 **열 순서**가 이것이다 | `range(len(fn.influenceObjects()))` | **`getWeights` / `setWeights`** |
| **논리(logical)** | `.matrix[]` · `.weightList[].weights[]` 의 실제 **첨자** | `fn.indexForInfluenceObject(dag)` | `.matrix[i]` / `.bindPreMatrix[i]` 처럼 **플러그를 직접** 만질 때 |

```python
from Framework.core import maya_skin

fn = maya_skin.skin_fn(sc)
cols = maya_skin.influence_paths(fn)              # getWeights 의 열 순서(롱네임)
idx  = maya_skin.weight_indices(len(cols))        # get/setWeights 용 물리 인덱스
weights, n_inf = fn.getWeights(dag, comp)
...
fn.setWeights(dag, comp, idx, new_weights, False)

logical = maya_skin.logical_indices(fn)           # .matrix[] 를 직접 만질 때만
```

---

## 2. 왜 오래 살아남는 버그인가

`skinCluster` 를 만든 직후에는 **논리 = 물리**(0,1,2,…)다. 그래서 아래처럼 잘못 써도 **한동안 잘 된다**:

```python
idxs = om.MIntArray()
for d in fn.influenceObjects():
    idxs.append(fn.indexForInfluenceObject(d))    # <- 논리 인덱스
fn.setWeights(dag, comp, idxs, weights, False)    # 지금은 우연히 동작
```

둘이 어긋나는 순간 이렇게 죽는다:

```
# Warning: (kInvalidParameter): Object is incompatible with this method
```

> [!warning] 이 메시지는 [maya_shape](Framework_maya_shape.md) 의 "엉뚱한 셰이프" 문제와 **문구가 같다**.
> 셰이프를 확정했는데도 계속 난다면 인덱스 쪽을 의심할 것.

---

## 3. 어긋나는 대표 상황 — **undo**

인플루언스를 추가한 뒤 `Ctrl+Z` 로 되돌리면 논리 인덱스는 회수되지 않는다. 다시 추가하면 **새 번호**가
붙는다(Maya 2024 실측):

```
바인드 전        matrix mi = [0]            (jRoot 만)
인플루언스 추가   matrix mi = [0, 1, 2]      (+ j1, j2)   <- 논리 == 물리, 잘 된다
Ctrl+Z          matrix mi = [0]
다시 추가        matrix mi = [0, 3, 4]      <- 논리 != 물리, 여기서 터진다
```

사용자 눈에는 **"Ctrl+Z 한 번 하면 그 뒤로는 바인드가 안 된다"** 로 보인다.
인플루언스를 지웠다 다시 넣은 씬(다른 툴·스크립트 포함)도 같은 상태가 된다.

물리 인덱스로 넘기면 마야가 알아서 올바른 논리 슬롯에 쓴다 — 듬성한 상태에서 값을 써 넣고
되읽어 확인했다: `weightList[0].weights` 가 `{0: 0.2, 3: 0.3, 4: 0.5}` 로 정확히 들어간다.

---

## 4. 적용된 곳 (2026-08-18, 같은 실수 5곳)

| 툴 | 위치 |
|----|------|
| `A00275_skinTool_V01` | `expand_bind_manager._influence_columns` (**신고된 증상**: Expand Bind 후 Ctrl+Z → 재바인드 실패) |
| `A00275_skinTool_V01` | `weight_transfer_manager._get_all_weights` |
| `A00275_skinTool_V01` | `skin_migrate_manager._native_move_columns` |
| `A00270_skinMigrate` | `skin_migrate_manager._native_move_columns` |
| `A00430_DemBone` | `skin_writer.apply_weights` / `read_weights` |

`A00430_DemBone` 의 `scene_sampler.bind_pre_from_skin` 은 `.bindPreMatrix[i]` 플러그를 직접 읽으므로
**논리 인덱스가 맞다** — 그대로 두었다.

---

## 5. 검증 메모 (mayapy 2024)

- 듬성한 인덱스(`[0,3,4]`)에 **논리** 인덱스로 `setWeights` → `kInvalidParameter`,
  **물리** 인덱스(`[0,1,2]`) → 정상. 조밀할 때는 둘 다 정상(그래서 안 드러난다).
- 물리 인덱스로 쓴 값이 **올바른 조인트**에 들어가는지 `skinPercent` 로 되읽어 확인.
- Expand Bind 를 **바인드 → Ctrl+Z → 다시 바인드** 했을 때 웨이트가 **첫 바인드와 완전히 동일**한지
  조인트 이름 기준으로 비교(인덱스와 무관한 비교라 이 버그를 정확히 잡는다).
