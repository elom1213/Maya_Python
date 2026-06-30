# A00040_file_exporter 사용법

## 1. 개요

Maya 의 **selection set(objectSet)** 단위로 오브젝트를 묶어, 세트마다 하나의
**FBX 파일**로 일괄 내보내는 maya.cmds 툴이다. 파일 이름은 토큰 조합으로 규칙적으로
생성할 수 있다.

- DCC: Autodesk Maya (maya.cmds UI). 아키텍처 (A) 타입.
- 설치: `__dragDrop_A00040.py` 를 뷰포트에 드래그&드롭 → 셸프 버튼 생성.
  이후 셸프 버튼 또는 `tools.A00040_file_exporter.run(True)` 로 실행.
- 본체: `file_exporter_v01.py` (`class JUN_ToolUI_file_exporter`), 로직: `utility.py`.

## 2. 화면 구성

| 섹션 | 내용 |
|------|------|
| **Brows path** | `Export path` 필드 + **Brows** 버튼 — FBX 를 저장할 폴더 선택 |
| **Set Up** | 두 개의 TSL: `Set's Name`(내보낼 objectSet 목록) / `File name`(각 세트의 결과 파일명) |
| **Naming** | 토큰 6개(SK / MANU / CH / Name / Type / Version)로 파일명을 조립. 각 토큰은 `Custom`(직접 입력) 또는 `Set's Name`(세트/오브젝트 이름 사용) 모드 |
| **버튼** | **Set name**(토큰 → File name TSL 생성) / **Export**(세트별 FBX 내보내기) |

## 3. 사용 흐름

1. **Brows** 로 내보낼 폴더를 지정한다.
2. 씬에서 내보낼 오브젝트를 묶은 objectSet 들을 `Set's Name` TSL 에 추가한다.
3. 필요하면 **Naming** 토큰을 설정하고 **Set name** 으로 `File name` 을 자동 생성한다
   (또는 파일명을 직접 입력).
4. **Export** — 각 세트의 멤버를 모아 `{export_path}/{file_name}.fbx` 로 내보낸다.
   - 파일명이 겹치면 `_000`, `_001` … 식으로 **고유 경로**(`get_unique_filepath`)를 붙인다.
   - 파일명의 `:`(네임스페이스 구분자)는 `_` 로 치환된다.

## 4. 내보내기 동작 (unparent → export → reparent)

FBX 로 깔끔하게 내보내기 위해, 내보내기 직전 각 멤버를 **월드(최상위)로 빼냈다가**
(`cmds.parent(world=True)`) 내보낸 뒤 **원래 부모로 복원**한다.

- 원래 부모(`get_parents`)를 멤버별로 기록 → 내보낸 뒤 그대로 되돌려 씬 계층을 보존한다.

## 5. 버전 이력

- **V01.02** (2026-06-30)
  - **버그 수정**: 내보낼 오브젝트가 **다른 오브젝트의 차일드가 아닐 때**(월드 최상위)
    `get_parents()` 에서 `cmds.listRelatives(..., parent=True)` 가 `None` 을 반환해
    `'NoneType' object is not subscriptable` 에러로 내보내기가 실패하던 문제 해결.
    부모가 없으면 `None` 으로 표시하고, 복원 단계에서 월드 최상위 오브젝트는 그대로 둔다.
  - **인덱스 정렬 수정**: `cmds.parent(members, world=True)` 가 *이미 월드 최상위인*
    오브젝트를 반환 리스트에서 제외해 `objs_out` ↔ `parents_origin` 인덱스가 어긋나던 문제를,
    멤버를 하나씩 처리하며 `(새 이름 ↔ 원래 부모)` 짝(`zip`)으로 유지하도록 변경.
  - **정리**: 재부모 루프가 바깥 루프와 같은 변수 `i` 를 쓰던 섀도잉 제거,
    `len(...) is 0` → `== 0` 비교 정정.
- **V01.01**: unparent / 복원(parenting) 로직 추가.
- **V01.00**: 최초 작성.
