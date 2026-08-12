---
name: wip-a00145-target-edit
description: A00145 Target Edit 탭 — 컨스트레인트 타깃 추가/삭제 (Maya 명령의 add/remove, 마지막 타깃 삭제 = 노드 삭제, remove 후 offset 재베이크) (v01.26)
metadata:
  node_type: memory
  type: project
---

A00145_RigConnect `Target Replace` 하위 탭을 **`Target Edit`** 으로 확장 — 교체에 **추가/삭제**를 더했다
(v01.25→**01.26**, 2026-08-12). 교체 쪽 설계는 [[wip-a00145-target-replace]].

**탭을 새로 만들지 않고 합쳤다** — 세 동작이 `Constraints` + `Targets` + `New Target` 이라는 같은 입력을
쓴다. 작업 범위는 **Constraints 리스트에서 고른 항목**(없으면 전체)이고 `List Targets`/자동 갱신도 같은
범위를 따른다 → 목록이 곧 "버튼이 건드릴 범위".

**Maya 명령을 쓴다 (연결을 직접 끊지 않는다)** — 손으로 `target[i]` 연결을 끊으면 weight 별칭과 빈 멀티
인덱스가 남는다. Maya 2024 실측([[mayapy-headless-verify]]):

- `cmds.<type>Constraint(newTgt, driven, mo=True)` → **기존 노드에 타깃 추가**(새 노드 아님),
  weight 별칭 `<tgt>W<n>` 자동 생성, `weight=` 플래그로 값 지정, driven 안 움직임.
  **aim 의 aim/up/worldUp 설정도 보존**된다. 이미 있는 타깃이면 무시(우리는 미리 걸러 경고).
- `cmds.<type>Constraint(tgt, driven, e=True, remove=True)` → 타깃 슬롯 삭제. parent/point/orient/
  scale/aim/geometry/normal/pointOnPoly/poleVector 전부 지원.
- **마지막 타깃을 지우면 Maya 가 constraint 노드까지 지운다.** driven 은 마지막 값을 유지한 채 연결만
  끊긴다. 실수 방지로 기본은 건너뛰고 경고(`delete_empty_constraint` 옵션으로 허용).

**remove 후 keep-in-place (parentConstraint)** — 옛→새 타깃 델타가 없어 교체용 보정을 못 쓴다. 대신
남은 **모든** 타깃의 `targetOffsetTranslate/Rotate` 를 현재 포즈로 다시 굽는다: 각 타깃이 *혼자서도*
삭제 전 월드 행렬을 만들도록 맞추면, **동일한 행렬끼리의 블렌드는 weight 가 어떻게 섞이든 그 행렬**이라
정확하다(= maintainOffset 으로 다시 건 상태). offset 두 개의 공간 규약은
[[constraint-target-plugs-and-offset-spaces]]. point/scale/orient 는 공유 `.offset` 이라 기존 보정 함수
재사용. **add 는 Maya 의 `maintainOffset` 이 이미 같은 일을 한다**(실측).

검증: 코어 30 + UI 14 항목 헤드리스 통과. (UI 테스트에서 `Qt.UserRole` 은 **256**, 32 아님)
