---
name: wip-a00330-set-rename
description: A00330_NamingTool Set Rename 탭 — 세트 이름 찾아 바꾸기 + 미리보기. 공용 Filter 위젯에 QTreeWidget 모드 추가 (v01.02)
metadata:
  type: project
---

`A00330_NamingTool` **v01.02 `Set Rename` 탭** (2026-08-27). 4번째 탭.
코어는 `app/core/set_rename_ops.py`, 문서는 `docs/A00330_NamingTool.md` §6.4.

**요청은 "마야 Search Replace 가 세트엔 안 되니 만들어 달라" 였는데, 원인이 예상과 달랐다.**
`searchReplaceNames` 는 **`"all"` 모드로 돌리면 세트도 잘 바꾼다.** 막힌 것은 명령이 아니라
**세트를 선택하는 방법**이었다 — `cmds.select(set)` 이 멤버를 펼친다.
→ **그래서 이 탭이 하는 일은 문자열 치환이 아니라 "세트를 고르게 하고 미리 보여 주는 것"** 이다.
마야 함정 6종은 [[maya-set-rename-traps]] 에 따로 적었다.

**UI 구성** — `Refresh`(전체) / `From Selection`(**선택한 오브젝트가 속한** 세트, `listSets`) →
공용 Filter 로 좁히기 → 하이라이트 → `Search`/`Replace` 를 치면 `New name`·`Status` 열이
**즉시** 갱신 → `Rename Selected Sets`(undo 한 스텝).
상태 7종(`OK` / `name taken` / `no change` / `invalid name` / `locked` / `referenced` /
`default set`)이고 **`OK`·`name taken` 만 실행된다.**

**설계에서 고른 것**: 마야는 잘못된 문자를 조용히 고치고 충돌엔 번호를 붙인다.
**그 동작을 흉내 내지 않는다** — 잘못된 이름은 이유를 붙여 **건너뛰고**, 충돌은 미리 표시한 뒤
실행 후 **실제로 붙은 이름**을 `[Warning]` 으로 보고한다. "조용히 다른 이름이 생기는 것" 이
이 작업의 진짜 위험이다.

**Framework 확장**: 공용 Filter `JUN_mod_filter_qt_v01` 에 **`tree_widget` 모드**를 더했다
(컬럼 있는 목록용, `tree_column` 으로 필터 열 지정, 기존 호출부 무영향).
[[framework-filter-widget]] · `docs/Framework_MOD_filter_qt.md` 5장.

> **여기서 버그를 하나 심었다가 테스트가 잡았다** —
> **`QTreeWidget.selectedItems()` 는 숨긴 항목을 빼고 주는데 `QListWidget` 은 그대로 준다**(실측).
> 그대로 `selectedItems()` 를 썼더니 `visible_selected()` 의 **"가려진 선택 수" 가 늘 0** 이 되어
> "보이는 것이 작업 대상" 경고가 조용히 사라졌다. 트리 모드는 최상위 항목을 훑어
> **`isSelected()` 로 직접 판정**한다. (`item.isSelected()` 는 숨겨도 `True` 로 남는다.)
> **컬럼 목록에 필터를 붙일 때마다 다시 밟을 함정이다.**

**검증** (mayapy headless **92항목 전부 통과**): 순수 이름 헬퍼(치환 문자열이 정규식으로
해석되지 않는지 포함) · 열거 · `select(set)` 확장 거동과 `noExpand` 대조 ·
**미리보기가 씬을 안 바꾸는지** · 상태 7종 · **네임스페이스 보존과 벗겨지는 대조군** ·
충돌 시 실제 이름 · **undo 한 스텝** · Filter 두 모드 · UI 버튼 경로.
`QApplication` 은 `standalone.initialize()` **앞에** ([[qapplication-before-maya-standalone]]).

**v01.03 (같은 날)** — 목록에 `Add`/`Del`, `Copy Name` 이 세트도 대상으로.
- `Del` 은 **목록에서만** 빼고 씬의 세트는 그대로 둔다(툴팁·로그에 명시). `Add` 는 중복을 건너뛴다.
- 세트에 이름을 복사할 땐 **접미사가 필수다** — 세트는 이미 쓰이는 이름을 못 쓰고 마야가 조용히
  `name1` 로 바꾼다. **DAG 는 부모만 다르면 같은 이름을 가질 수 있어** 문제가 없다
  → 접미사는 **세트 대상에만**. 자세한 건 [[maya-set-rename-traps]] ⑦.
- **[Fix] `copy_name` 이 네임스페이스를 벗기고 있었다** — 세트만이 아니라 **트랜스폼도** 그렇다.
  요청 범위 밖이었지만 **안 고치면 세트 지원이 레퍼런스 씬에서 깨져서** 같이 고쳤다.
  반환이 `(new_names, warning)` → `(new_names, warning, notes)` 로 늘었다.
- 세트를 리스트에 담는 경로가 없어 공용 TSL 의 `add_button()` 으로 **`Add Sets`** 를 붙였다.
- 검증 92 → **124항목**.

> **테스트가 틀렸던 것 하나**: 필터 토큰으로 `"a_set"` 을 썼는데 `beta_set` 에도 들어 있어
> 3개가 다 남았다. 부분 일치 필터를 테스트할 땐 **판별력 있는 토큰**을 골라야 한다.
