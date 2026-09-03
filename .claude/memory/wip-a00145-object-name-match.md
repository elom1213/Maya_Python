---
name: wip-a00145-object-name-match
description: "A00145 Connect > Pair (구 Connect Closest) — 오브젝트를 이름으로 짝짓기. 경로/네임스페이스를 떼고 비교하되 반환은 전체 경로, Connect 는 거리로 다시 짝짓던 것을 Pairing 옵션으로 (v01.37)"
metadata: 
  node_type: memory
  type: project
  originSessionId: eed8b93d-9d98-420a-85c3-532581f77463
  modified: 2026-09-03T07:10:17.123Z
---

A00145_RigConnect `Connect > Connect Closest` 하위 탭을 **`Pair`** 로 바꾸고 **`Match by
Name`** 추가 (v01.36→**01.37**, 2026-09-03). Driver 와 이름이 비슷한/같은 Driven 을 찾아
**driver 순서로** 세우고, 짝이 없는 자리는 `(Null)`. 어트리뷰트 쪽 규칙과 같다
([[wip-a00145-match-null-placeholder]], [[wip-a00145-attr-name-matching]]).

**어디에 둘 것인가를 먼저 정했다.** 사용자는 이 탭을 통째로 `A00310_SearchTool` 로 옮기는
안을 제시했다(옮기면 constraint 는 빼도 된다고). **옮기지 않기로 했다** — 정렬된 짝은
**순서가 곧 의미**인데 툴 사이로 짝을 넘길 수단이 씬 선택뿐이라 **넘기는 순간 순서가
사라진다.** 짝을 세우는 자리는 그 짝을 **소비하는 자리(연결)** 옆이어야 한다.

**점수 엔진은 새로 만들지 않았다.** `attr_match` 는 애초에 **이름 리스트만 받는 순수
파이썬**이라 오브젝트에도 그대로 쓴다. 새 모듈 `object_match.py` 가 더하는 것은 이름을
비교 가능하게 만드는 일뿐이다.

- **★ 경로·네임스페이스가 점수를 망친다.** `|grp|rig:jnt_L_arm` 을 통째로 토큰화하면
  `grp`·`rig` 가 토큰으로 섞여, **한쪽 리스트에만 경로가 붙어 있으면 같은 오브젝트인데
  문턱을 못 넘는다.** → 비교는 **말단 이름**(`|` 뒤), 네임스페이스는 옵션(기본 뗀다).
- **★ 반환은 언제나 원래(전체) 이름.** 말단 이름을 돌려주면 동명 노드 씬에서 엉뚱한 노드를
  잡는다. 비교용 키와 실제 이름을 갈라 두고 매칭 결과의 **인덱스**로 되짚는다.
- 후보 풀 규칙은 `Get Closest` 와 공유한다 — Driven 이 비면 씬 선택, **driver 자신은 제외**
  (거리로는 자기가 최단, 이름으로는 자기가 만점).

**★ 짝을 세워도 `Connect` 가 거리로 다시 계산하고 있었다.** 기존 `connect_closest` 는
리스트 순서를 아예 보지 않는다(`Get Closest` 로 채워도 연결 때 최근접 재계산). 그대로면
이름으로 세운 짝이 **연결 순간 조용히 뒤집힌다.** → `Pairing` 라디오
(`Closest distance` / `List order`)를 꺼내고 Match by Name 이 자동으로 `List order` 로
돌린다. `List order` 는 **거르기 전에 짝을 만든다** — 없는 항목을 먼저 빼면 그 자리가
사라져 뒤가 한 칸씩 밀린다.

파일: `app/core/object_match.py`(신규) · `closest_connector.py`(`pairs_by_order`,
`PAIRING_*`) · `app/ui/main_window.py`.
