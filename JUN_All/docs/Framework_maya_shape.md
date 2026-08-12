---
title: Framework.core.maya_shape — 트랜스폼 → 셰이프 확정 헬퍼
aliases: [maya_shape, shape_path, extendToShape]
tags: [maya-python, framework, shape, skincluster, gotcha]
updated: 2026-08-12
---

# `Framework.core.maya_shape`

트랜스폼에서 **어느 셰이프를 만질지** 확정하는 공용 헬퍼. 여러 툴이 각자 복붙하던
`MDagPath.extendToShape()` 패턴을 대체한다.

```python
from Framework.core import maya_shape

maya_shape.shape_path(node, deformer=None, type_="mesh")  # 롱네임 or None
maya_shape.shape_dag(node, deformer=None, type_="mesh")   # MDagPath (없으면 ValueError)
maya_shape.vertex_count(node, deformer=None)              # int (셰이프 기준)
maya_shape.deformed_shapes(deformer)                      # 그 디포머가 변형하는 셰이프 집합
maya_shape.drives_shape(deformer, node)                   # (셰이프, 변형하는가)
```

---

## 왜 필요한가 — `extendToShape()` 의 함정

`MDagPath.extendToShape()` 는 **첫 번째 non-intermediate 셰이프**를 고를 뿐이다
(Orig/intermediate 는 알아서 건너뛴다 — Maya 2024 실측). 그런데 한 트랜스폼 아래에 메시
셰이프가 **여럿**인 씬이 드물지 않다.

- blendShape 타겟 셰이프를 같은 트랜스폼 아래로 정리해 둔 리그
- 머지/임포트 잔재, 셰이프를 부모로 끌어다 붙인 씬

이때 "첫 번째" 가 우리가 원하는 셰이프라는 보장이 없다. 그러면:

| 어디에 쓰였나 | 증상 |
|---------------|------|
| 디포머 웨이트 API (`MFnSkinCluster.get/setWeights`) | **`(kInvalidParameter): Object is incompatible with this method`** 로 죽는다 |
| 지오메트리 읽기/쓰기 (`MFnMesh`) | 예외 없이 **엉뚱한 셰이프**를 읽고 쓴다(조용히 틀린다 — 더 위험) |
| `cmds.polyEvaluate(<트랜스폼>, v=True)` | 정수가 아니라 요약 **문자열**을 돌려줘 호출부가 `TypeError` |
| `cmds.copySkinWeights` (선택 기반) | `A skinCluster node should be specified with the -destinationSkin/-ds flag.` |

## 어떻게 고르는가

1. 이미 셰이프면 그대로.
2. `deformer` 를 주면 **그 디포머가 실제로 변형하는 셰이프**(`cmds.deformer -q -g`).
   skinCluster / blendShape / lattice 등 모든 디포머에서 동작한다(실측).
3. 안 주면 히스토리에서 `geometryFilter` 를 찾아 같은 방식으로.
4. 그래도 못 정하면 non-intermediate 셰이프의 첫 번째.

셰이프가 하나뿐이면 2~3단계를 건너뛴다(질의 비용 없음).

> **웨이트를 읽고 쓰는 코드는 `deformer=` 를 넘길 것.** 그래야 "그 디포머가 변형하는
> 셰이프" 라는 뜻이 명확해지고, `drives_shape()` 로 사전 검증까지 할 수 있다.

## 쓰는 곳

| 툴 | 어디 |
|----|------|
| `A00275_skinTool_V01` | Expand Bind / Transfer / Migrate 의 웨이트 IO 와 지오메트리 읽기 |
| `A00270_skinMigrate` | 네이티브 조인트 이동(`_native_move_columns`) |
| `A00145_RigConnect` | Match 탭의 메시 좌표 읽기 |
| `A00180_abSymMesh` | 정점 읽기/쓰기(엉뚱한 셰이프에 쓰기 방지) |
| `A00280_correctiveFromCache` | 토폴로지 비교·정점 읽기 |
| `A00300_meshDoctor` | 스캔/수정 대상 셰이프 |

## 검증

mayapy 2024 headless — 헬퍼 12항목 + 호출부 회귀 10항목:

- 셰이프가 여럿인 트랜스폼(비스킨 셰이프가 **첫 번째**여도) 에서 **스킨이 걸린 셰이프**를 고른다
- 디포머를 명시하면 그것이 우선(skinCluster / blendShape 둘 다)
- 셰이프 이름·컴포넌트 이름 입력도 그대로 처리, 메시가 없으면 `None` / `ValueError`
- 그 위에서 A00275 Transfer 부분 전이 · A00275/A00270 네이티브 조인트 이동이 **웨이트까지 정상**
- A00300 스캔 / A00180 정점 수 / A00280 토폴로지 / A00145 메시 좌표가 올바른 셰이프를 읽는다
