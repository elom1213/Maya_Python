---
name: wip-a00330-insert-tab
description: "A00330_NamingTool v01.09 (2026-09-23) — Quick Rename 을 Selection / Insert 하위 탭으로, Insert = TSL 이름 n 번째 자리에 글자 삽입(0 앞 · -1 끝) + 라이브 미리보기 + Apply"
metadata:
  type: project
---

`A00330_NamingTool` **v01.09 Quick Rename > Insert** (2026-09-23). 코어 `app/core/insert_ops.py`,
문서 `docs/A00330_NamingTool.md` §6.3.1.

- Quick Rename 을 하위 탭 **Selection**(기존 ref_01.mel 버튼, 현재 선택 기준) / **Insert**(리스트 기준)로 나눴다.
- Position 규칙: `0` 맨 앞, 양수 n = 앞 n 글자 뒤, `-1` 맨 끝, `-n` = 뒤 (n-1) 글자 앞. **0 과 -1 이 짝.**
  이름 밖은 끝/앞으로 당기고 Status 노트에 적는다(길이 제각각인 이름에 한 번에 쓰므로 막지 않음).
  처음에 `-4` 예시를 `armX_jnt` 로 잘못 적었다 — 맞는 값은 `arm_Xjnt`(뒤 3 글자 앞). 테스트가 잡았다.
- 짧은 이름만 센다. DAG 경로·네임스페이스는 떼었다가 다시 붙인다([[maya-set-rename-traps]]).
- 상태는 Set Rename(`set_rename_ops`) 상수를 재사용 + `default node` / `not a node`. `OK`·`name taken` 만 적용.
  충돌 판정: DAG 는 `parent|새이름` 존재, DG 는 전역 이름.
- 적용은 **깊은 노드부터**, 부모를 바꾼 뒤 그 아래 행 경로의 앞부분을 고쳐 쓴다(UUID 불필요).
- `cmds.rename` 은 트랜스폼을 바꾸면 셰이프도 따라 바뀐다(`arm_jntShape` → `arm_jnt_LShape`, 실측).
- 미리보기는 TSL `list_widget.model()` 의 rowsInserted/Removed/Moved/modelReset 에 걸어 자동 갱신.
- New name 의 **삽입 글자만 초록**: 표 칸은 한 색뿐이라 리치 텍스트 QLabel 을 `setItemWidget` 으로 얹는다.
  칸 글자는 비우고(겹쳐 그려짐) 이름은 `UserRole` 에. `resizeColumnToContents` 는 얹은 위젯 폭도 센다(실측).
  코어 행의 `insert_span` = new_name 안의 [start, end), 네임스페이스 길이+1 포함.
- 검증 mayapy 39항목 통과. **마야 UI 실사용 확인은 아직.**
