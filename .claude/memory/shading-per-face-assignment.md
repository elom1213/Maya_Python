---
name: shading-per-face-assignment
description: "머티리얼을 새 메시로 옮길 때 listConnections(shadingEngine) 로는 면별 배정이 사라진다 — MFnMesh.getConnectedShaders 를 써야 한다"
metadata:
  node_type: memory
  type: reference
---

**`cmds.listConnections(shape, type="shadingEngine")` 는 "이 메시에 어떤 셰이딩 엔진들이
붙어 있나" 만 알려 준다 — 어떤 면에 무엇이 붙었는지는 없다.** 그래서 그 목록의 첫 번째를
새 메시 전체에 거는 코드는 **머티리얼이 하나인 메시에서만** 맞고, 면마다 다른 메시(캐릭터는
대개 그렇다)에서는 **나머지가 통째로 사라져 한 벌만 입은 메시**가 나온다.

2026-09-16 에 `A00275_skinTool_V01` Layer > Create 가 정확히 이 모양이었다 — 원본에
머티리얼 5개가 붙어 있어도 `M_new` 는 1개였다(v01.25 수정).

**면별 배정은 `MFnMesh.getConnectedShaders(instanceNumber)`** 가 돌려준다.

```python
sel = om.MSelectionList(); sel.add(shape)
dag = sel.getDagPath(0)
engines, face_index = om.MFnMesh(dag).getConnectedShaders(dag.instanceNumber())
names = [om.MFnDependencyNode(e).absoluteName() for e in engines]
# face_index[f] = 그 면이 쓰는 engines 인덱스. 배정이 없으면 -1.
```

옮길 때 지킬 것:

- **면을 연속 구간(`f[0:511]`)으로 묶어** 엔진당 `cmds.sets` 를 한 번만 부른다. 면을 하나씩
  이름으로 만들면 잔 메시에서 문자열이 수만 개가 된다.
- **머티리얼이 하나면 셰이프째** 건다 — 면 단위 멤버를 남기지 않는다.
- `-1` 인 면은 건너뛴다(아무 머티리얼도 없는 면).
- **면 개수가 다르면 옮기지 말고 경고만.** 통째로 하나를 거는 것은 틀린 답이지 안전한
  폴백이 아니다.

토폴로지가 같아야 면 번호가 맞는다. skinCluster 의 **입력(rest) 형상**은 디포머가 토폴로지를
바꾸지 않으므로 보이는 셰이프와 면 번호가 그대로 맞는다.

**그 밖의 함정 (2026-09-17, A00470 Copy Material 에서 실측)**

- **면 하나를 `sets -remove` 해서는 비워지지 않는다** — 오브젝트째 배정이면 조용히 무시, 면별이면 마야가
  `initialShadingGroup` 으로 되돌린다. 빈 면을 만들려면 셰이프의 멤버십을 전부 걷어낸 뒤 필요한 면만 건다.
- **그렇게 걷어낸 메시에서 `getConnectedShaders` 는 어느 세트에도 없는 면을 `initialShadingGroup` 으로 보고한다**
  (`sets -q` 로는 멤버 아님). 빈 면 판정은 `listSets(object="shape.f[i]", type=1)` 로.
- 마야 2024 기본 머티리얼은 `standardSurface1` (`lambert1` 아님).

**머티리얼 → 페이스 선택 (2026-10-12, A00470 v01.10 Select Faces 에서 실측)**

- **`sets -q <SG>` 의 면별 멤버는 트랜스폼에 붙어 나온다**(`sphere.f[0:199]`, 셰이프 아님). 연속한 면은 구간으로
  압축돼 있고, 체커보드처럼 안 이어지면 면 하나씩(4만 면에 2만 항목). 셰이프 집합과 비교하려면 노드를 셰이프로
  풀어야 하고, 그 조회는 **노드별 캐시**로(멤버마다 조회하면 2만 개에 2.3초).
- **`cmds.select` 는 컴포넌트 문자열 개수에 비례해 느리다**(2만 개 1.4초). 인덱스를 `MFnSingleIndexedComponent`
  (`kMeshPolygonComponent`) 에 담아 `MGlobal.setActiveSelectionList` 로 넘기면 0.001초. 단 **undo 큐에 안 들어간다.**
- **면을 전부 다른 SG 로 재배정한 메시는 `initialShadingGroup` 연결이 그대로 남는다** — `listConnections(shape,
  type="shadingEngine")` 에 보이지만 `listSets(object=shape, type=1)` 엔 없다. "붙은 머티리얼" 을 셀 땐 멤버십으로 걸러야
  쓰지 않는 `standardSurface1` 이 끼지 않는다.
- 셰이프 둘인 트랜스폼에 `t.f[0:2]` 를 배정하면 **두 셰이프 모두**에 들어가고, 멤버는 셰이프 기준으로 나온다.

관련: [[wip-a00470-materialtool]], [[framework-log-widget]], [[utility-nodes-inherit-shadingdependnode]],
[[wip-a00275-layer-tab]]
