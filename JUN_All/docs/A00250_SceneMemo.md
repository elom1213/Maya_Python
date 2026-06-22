# A00250_SceneMemo — 사용 가이드

마야 씬의 오브젝트(메시 / 커브 / 트랜스폼 등)에 **사용자 메모**를 남기고, 씬을 닫았다
다시 열어도 보존하며, 한국어 입력과 사후 편집이 가능한 in-Maya PySide 툴.

- 버전: v01.00 (2026-06-22)
- 아키텍처: B형 (PySide / Qt, in-Maya) — `A00110_animTool` 기반
- 설치/계획 상세: [A00250_SceneMemo_plan.md](A00250_SceneMemo_plan.md)

---

## 설치 / 실행

1. `JUN_All/tools/A00250_SceneMemo/__dragDrop_A00250.py` 를 Maya 뷰포트로 **드래그&드롭** →
   현재 셸프에 `SceneMemo` 버튼 생성.
2. 셸프 버튼 클릭(또는 `tools.A00250_SceneMemo.run(True)`) 으로 실행.

---

## 사용법

| 버튼 | 동작 |
|------|------|
| **Add Selected** | 씬에서 선택한 오브젝트들을 메모 목록에 추가(빈 메모) |
| **Remove** | 선택한 행(들)의 메모 삭제 |
| **Refresh** | 목록 새로고침 (노드명 다시 resolve) |
| **Save Memo** | 하단 에디터의 내용을 **선택한 행(들)에 저장** (사후 편집 / 일괄 작성) |
| **Select in Scene** | 선택 행(들)의 오브젝트를 씬에서 선택 (행 **우클릭 → Select in Scene** 메뉴로도 가능) |
| **Search** | 오브젝트명 / 메모 내용으로 필터 |
| **Clean Orphans** | 씬에 더 이상 없는(삭제된) 오브젝트의 메모 정리 |
| **Export** | 마야 파일 옆 `JUN_memo/<scene>_memo.json` 으로 내보내기 |
| **Import** | 같은 위치의 사이드카 json 을 읽어 병합 |

기본 흐름: 오브젝트 선택 → **Add Selected** → 행 클릭 → 에디터에 메모(한국어 가능) 작성 →
**Save Memo** → **씬 저장(Ctrl+S)**.

**여러 오브젝트에 하나의 메모**: 테이블에서 여러 행을 선택(Ctrl / Shift 클릭)한 뒤 메모를
작성하고 **Save Memo** 하면 선택한 모든 행에 같은 메모가 일괄 저장된다. (선택 행들의 기존
메모가 서로 다르면 에디터는 비워진 상태로 시작한다.) Remove / Select in Scene 도 선택한
행 전체에 적용된다.

---

## 저장 방식 (중요)

- 메모는 씬 내부 **`JUN_memo_store`** (network) 노드의 `junMemoData` (string, JSON) 에 저장된다.
  → 따라서 메모가 `.ma/.mb` 파일 **안에** 들어가며, Save As / 복사 / 이동에도 자동으로 따라간다.
- 키는 노드 **UUID** 라 리네임/부모변경에도 메모가 끊기지 않는다.
- **Save Memo 는 "씬 노드에 기록"까지만** 한다. 디스크에 영구 저장하려면 반드시 마야 파일을
  저장(Ctrl+S)해야 한다.
- 삭제된 노드의 메모는 자동 삭제되지 않고 `(missing)` 으로 남는다 → **Clean Orphans** 로 정리.

### 사이드카 (백업/공유)
- **Export** 는 마야 파일 옆 `JUN_memo/` 폴더에 `<sceneName>_memo.json` 으로 내보낸다(폴더 자동 생성).
- 사이드카는 정본이 아니라 백업/공유/버전관리용이다. (마야 파일만 복사되면 따라가지 않음)
- 씬이 미저장(Untitled)이면 Export/Import 불가.

---

## 참고
- UI 문자열은 영어, 메모 **내용**은 한국어 입력 가능.
- core(`app/core`, 로직) / ui(`app/ui`, 화면) 분리 구조.
- Maya 2023+ 호환 (특수 노드/플러그인 비의존).
