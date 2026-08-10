---
name: wip-a00145-target-replace
description: A00145 Constrain 탭 Target Replace — 컨스트레인트의 타깃(드라이버)을 다른 오브젝트로 일괄 교체 (v01.20)
metadata: 
  node_type: memory
  type: project
  originSessionId: ee81a66a-5136-4bb8-b44a-7fa187164cdb
  modified: 2026-08-07T09:06:42.409Z
---

A00145_RigConnect **Constrain 탭 5번째 접이식 박스 `Target Replace`** (v01.19→**01.20**, 2026-08-07).

여러 컨스트레인트가 공유하는 **타깃(드라이버)** 하나를 씬의 다른 오브젝트로 일괄 교체한다.
그 타깃을 쓰지 않는 컨스트레인트는 **방치**. (Constraint Transfer 는 driven 을 옮기는 반대 기능)

- `List Targets` → 타깃 **합집합** + `[n/m]`(m개 중 n개가 사용) + 툴팁에 사용 컨스트레인트 목록.
  검색은 공용 Filter, 표시 텍스트에 `[n/m]` 이 붙으므로 **실제 이름은 `Qt.UserRole` 데이터**에서 꺼낸다.
- 옵션: `Keep driven objects in place`(기본 ON, offset 재계산) /
  `Rename the weight attribute to the new target`(기본 OFF).
- 매핑 규칙은 이 툴의 다른 탭과 동일 — 새 타깃 1개면 전부 그것으로, 개수 같으면 1:1.

**핵심 설계: 재생성이 아니라 연결 rewire.** 컨스트레인트를 지웠다 다시 만들면 노드 이름,
**weight 에 물린 연결(IK/FK 스위치 등)**, 커스텀 어트리뷰트가 날아간다. 그래서 노드는 그대로 두고
`target[i]` 의 입력 연결만 갈아끼운다. 대응 입력을 하나라도 못 만들면 **아무것도 건드리지 않고**
경고만 남긴다(부분 파괴 방지).

Maya 쪽 함정(연결 열거 / offset 공간·오일러 순서)은 [[constraint-target-plugs-and-offset-spaces]] 참고.

부수 변경: Constrain 탭이 접이식 박스 5개로 늘어 QScrollArea 로 감쌌다.
→ **v01.22 에서 접이식을 걷어내고 하위 탭 5개로 바꿨다** ([[prefer-subtabs-over-stacked-collapsibles]]). 스크롤도 하위 탭별로 옮김.

검증: mayapy 헤드리스 — 타입 5종 × rotateOrder 3종 keep-in-place, weight 연결 보존, joint 왕복,
셰이프 교체, 동명 노드, 방어 케이스 + UI 스모크 전부 통과 ([[mayapy-headless-verify]]).
