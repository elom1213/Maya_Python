# Changelog — A00250_SceneMemo

## v01.00 (2026-06-22)
- 최초 버전.
- 씬 오브젝트(메시/커브/트랜스폼 등)에 사용자 메모를 남기는 in-Maya PySide 툴.
- 메모는 씬 내부 `JUN_memo_store` (network) 노드의 `junMemoData` (string, JSON) 에 저장 →
  씬 저장 후 닫았다 다시 열어도 보존. UUID 키로 리네임/부모변경에도 유지.
- 한국어(유니코드) 메모 입력/저장 지원.
- 기능: Add Selected / Remove / Save Memo(사후 편집) / Select in Scene / Search /
  Clean Orphans / Export·Import (마야 파일 옆 `JUN_memo/<scene>_memo.json` 사이드카).
