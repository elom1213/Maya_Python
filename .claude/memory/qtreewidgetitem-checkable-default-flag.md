---
name: qtreewidgetitem-checkable-default-flag
description: "QTreeWidgetItem/QListWidgetItem 은 ItemIsUserCheckable 이 기본 ON — 플래그로 '체크 가능' 판정 금지"
metadata: 
  node_type: memory
  type: reference
  originSessionId: 85c8852e-52d8-4514-9afa-b44bf5d7ef96
  modified: 2026-08-03T00:35:58.319Z
---

`QTreeWidgetItem` / `QListWidgetItem` 은 **`Qt.ItemIsUserCheckable` 을 기본으로 켠 채** 생성된다.
체크박스가 안 보이는 건 플래그가 꺼져서가 아니라 **`setCheckState()` 를 안 불러서**일 뿐이다.

**Why:** 그래서 `item.flags() & Qt.ItemIsUserCheckable` 로 "이 항목이 체크 가능한가"를 판정하면
**체크박스가 없는 항목까지 전부 통과**한다. A00210 Path Structure 에서 루트·표시전용 파일이
제외(exclude) 대상으로 잘못 잡힐 뻔했다(테스트가 잡음).

**How to apply:**
- 판정은 플래그가 아니라 **직접 저장한 데이터 롤**(`Qt.UserRole+n` 에 넣은 rel/recorded 같은 의미값)로.
- 체크박스를 주지 않을 항목은 **명시적으로 플래그를 끄자**: `item.setFlags(item.flags() & ~Qt.ItemIsUserCheckable)`.
  안 끄면 키보드/뷰 설정에 따라 원치 않게 체크 상태가 생길 수 있다.
- 반대로 체크박스를 **보이게** 하려면 플래그만으로는 부족하고 `setCheckState(col, Qt.Checked/Unchecked)`
  를 반드시 호출해야 한다.

관련: [[wip-a00210-pathstructure-files]], [[wip-tsl-uuid-selection]]
