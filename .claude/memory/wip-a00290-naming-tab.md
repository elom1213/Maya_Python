---
name: wip-a00290-naming-tab
description: A00290 Edit BS > Naming 탭 — 타겟 이름(weight 별칭) 일괄 변경. FBX/언리얼 모프 타겟 이름이 곧 별칭이고, aliasAttr 은 같은 이름·맞바꾸기를 거절한다
metadata:
  type: project
---

**A00290_BSTool `Edit BS` 하위 탭 `Naming`**(v01.21, 2026-09-11) — blendShape 타겟 이름을
Set Name(`#` 번호) · Search & Replace · Prefix/Suffix 로 한꺼번에 바꾼다. 미리보기 트리
(Current/New/Note)가 즉시 따라오고, 빨간 줄이 하나라도 있으면 **아무것도 적용하지 않는다**.
코어는 `app/core/naming_manager.py`(`build_names` → `plan_renames` → `apply_renames`).

**Why**: 목적은 씬 정리가 아니라 **언리얼 모프 타겟 이름**이다.

- **★ FBX 에 나가는 이름은 weight 별칭뿐이다** (Maya 2024 + FBX 2020.3.4 실측, ASCII 익스포트).
  `Geometry::<별칭>` 과 `SubDeformer::<blendShape>.<별칭>`(BlendShapeChannel) 만 있고,
  **타겟 메시의 노드 이름은 파일 안에 한 번도 나오지 않는다** — 구운 타겟이든 라이브로
  연결된 타겟이든 같다. 언리얼은 채널 이름에서 `<blendShape>.` 접두사를 떼어 모프 타겟
  이름으로 쓴다. 그래서 **`cmds.aliasAttr` 만 바꾸면** 재익스포트가 새 이름으로 임포트된다.
  (타겟 메시 이름 변경은 순전히 씬 정리용 옵션 — [[blendshape-target-name-vs-alias]])
- **마야 기본 기능은 하나씩만 있다** — Shape Editor 에서 **타겟 이름 더블클릭** = `aliasAttr`.
  규칙 · 여러 개 · 미리보기가 없어서 탭으로 만들었다.

**How to apply** — `aliasAttr` 함정(전부 mayapy 2024 실측):

- **같은 이름으로 다시 rename 하면 `RuntimeError`** ("이미 그 이름의 어트리뷰트가 있다").
  안 바뀌는 항목은 **호출 자체를 건너뛴다.**
- **이름 맞바꾸기(A↔B)·돌려쓰기(A→B→C→A)는 한 번에 안 된다** → 바뀌는 전부를
  **임시 이름 → 최종 이름 2단계**로 넘긴다(임시 이름은 `objExists` 로 비었는지 확인).
- 허용 모양은 사실상 `[A-Za-z_][A-Za-z0-9_]*`. 공백 · `.` · `[]` · 숫자로 시작 ·
  한글(비 ASCII)은 마야가 `Warning` 뒤 `RuntimeError`. **`-` 는 마야가 받아 주지만**
  `bs.a-b` 가 표현식에서 뺄셈으로 읽혀 툴이 막는다.
- 별칭은 **blendShape 노드 안에서만** 유일하면 된다. 단 같은 노드의 실제 어트리뷰트
  (`envelope`, `weight`, 짧은 이름까지)와는 못 겹친다 — 판정은 `objExists(bs+"."+name)`.
- **값 · 키/연결 · lock 은 그대로 살아 있다**(연결은 별칭이 아니라 실제 plug 에 붙어 있다).
  구동하던 애님 커브의 노드 이름은 안 따라 바뀐다. `aliasAttr` 은 undo 되므로
  `undo_chunk()` 로 묶으면 Ctrl+Z 한 번.
- **베이스 지오메트리가 여럿이면 한 타겟에 라이브 메시가 여러 개다**(`inputTarget[b]` 마다).
  별칭은 인덱스 하나에 하나라 그대로 바뀌지만, 메시 이름은 전부 같게 만들 수 없어 손대지 않는다.
  (같은 인덱스에 두 번째 베이스의 타겟을 붙이면 **별칭이 나중 타겟 이름으로 덮인다**)

관련: [[wip-a00290-target-order-tab]], [[framework-filter-widget]], [[mayapy-headless-verify]]
