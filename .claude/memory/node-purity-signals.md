---
name: node-purity-signals
description: "노드가 '아무것에도 안 엮였나' 를 판정할 때의 함정 — listHistory 는 짧은 이름, 깨끗한 메시에도 initialShadingGroup 이 붙어 있다"
metadata:
  node_type: memory
  type: reference
---

"연결도 히스토리도 없는 깨끗한 노드" 를 고르는 판정을 짤 때 mayapy 로 실측해 얻은 것들이다
(2026-09-16, `A00310_SearchTool` Search > Rules 의 `Standalone` 규칙).

**★ `listHistory` 는 짧은 이름을 돌려준다.** `listRelatives(fullPath=True)` 는 롱네임을 주므로
그대로 비교하면 **자기 셰이프조차 걸러지지 않는다** — 히스토리가 전혀 없는 폴리큐브가
"히스토리 있음(자기 셰이프)" 으로 판정된다. 양쪽을 `cmds.ls(x, long=True)` 로 **정규화한 뒤**
비교한다. (겉보기에 멀쩡히 도는 코드라 테스트 없이는 못 잡는다.)

**★ 히스토리 없이 만든 메시에도 `initialShadingGroup` 이 붙어 있다.** 머티리얼 배정을 "연결" 로
세면 **어떤 메시도 깨끗할 수 없다.** 무시해야 하는 것들 —

- `shadingEngine` · `materialInfo` (머티리얼 배정. 면 단위 여러 벌도 같다)
- `displayLayer` · `layerManager` (디스플레이 레이어 멤버십은 `listHistory` **와** `listConnections`
  양쪽에 나온다)
- `objectSet` (평범한 셋 멤버십)
- `groupId` (면 단위 머티리얼 배정에 딸려 온다)
- `nodeGraphEditorInfo` · `hyperLayout` 등 그래프 편집기 부산물

**★ `shadingEngine` 은 `objectSet` 의 하위 타입이다.** `nodeType(inherited=True)` 로 판정하면
둘이 같이 걸린다. 무시 목록은 `objectType()` 이 주는 **정확한 타입 이름**으로 본다
([[utility-nodes-inherit-shadingdependnode]] 와 같은 부류의 함정).

**부모-자식은 DG 연결이 아니다.** 그룹 밑에 넣었다고 그 노드가 구동되는 것은 아니므로
`listHistory` / `listConnections` 어디에도 안 나온다 — 부모가 있다고 실격시키면 안 된다.

**양방향을 봐야 한다.** 어트리뷰트를 **내보내기만** 하는 노드(다른 노드를 구동하는 쪽)는
`listHistory` 가 비어 있고 `listConnections` 에만 나온다. 컨스트레인트의 **드라이버**도 마찬가지다.

종류별로 사유를 말해 주려면 `nodeType(node, inherited=True)` 에 `constraint` / `geometryFilter`
가 있는지로 가른다 — `skinCluster` · `blendShape` 는 전부 `geometryFilter` 상속이다.

관련: [[shading-per-face-assignment]], [[wip-a00310-searchtool-rules]]
