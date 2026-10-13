---
name: wip-a00240-junction-tab
description: "A00240 Junction 탭(v01.19~22) — mklink /J 를 UI 로, 정션 판별은 lstat 리파스 태그, 삭제는 is_junction 확인 후 os.rmdir(빈 실제 폴더도 지우는 명령), Tree 는 정션 연한 빨강 + 순환 가드, 끝 이름 같은 소스는 unique_names 로 상위 폴더 접두"
metadata:
  node_type: memory
  type: project
  originSessionId: f332ff00-a691-4c0f-97a1-ab3bba2197bb
  modified: 2026-10-12T00:29:35.375Z
---

A00240_PathTool v01.19 (2026-10-12) **Junction** 탭 — Create / Remove 하위 탭, `core/junction.py` + `ui/junction_tab.py`.

**윈도우 정션 함정 (실측):**
- `os.path.islink` 는 정션에 **False**. 판별은 `os.lstat().st_file_attributes & REPARSE_POINT` 이고
  `st_reparse_tag == stat.IO_REPARSE_TAG_MOUNT_POINT`. `os.path.isjunction` 은 3.12+ 라 Maya 2024(3.10) 에 없다.
- `os.scandir` 엔트리의 `stat(follow_symlinks=False)` 는 Windows 에서 목록 데이터로 답해 **추가 디스크 접근 없이**
  리파스 태그를 준다 — Tree 스캐너가 이걸로 `junction`/`target` 을 노드에 적는다.
- `os.readlink(정션)` 은 `\\?\` 접두사가 붙어 온다 → 벗겨서 보여 준다.
- `os.rmdir(정션)` 은 링크만 걷어내고 타깃 내용은 남는다. **그러나 빈 실제 폴더도 지운다** → 지우기 직전
  `is_junction` 확인이 안전장치의 전부. 툴은 표에 담을 때(빨강 `(not a junction)`) 와 지우기 직전 두 번 본다.
- `cmd /c mklink /J` 는 `subprocess.run(..., creationflags=CREATE_NO_WINDOW)`, 출력은 OEM 코드페이지(cp949) →
  `decode("oem")`. 성공은 반환 코드가 아니라 **만든 뒤 정션인지** 로 판정.

**설계 결정 (사용자가 안 정한 것):**
- 요청 번호 배치 "1·2 = Create, 3 = Remove" 는 오타로 보고 1·2·3(생성) = Create, 4(삭제) = Remove 로 했다.
- 타깃 리스트 행은 **만들 폴더**(정션 이름 = 원본 폴더 이름). n->1 은 첫 행만. n->n 에서만
  `Target row is the junction path` 로 행을 정션 경로 자체(mklink `<Link>`)로 쓸 수 있다.
- 파일은 정션이 안 된다(mklink /J 는 폴더만) — 미리보기에서 사유로 걸러진다. 하드링크(/H)는 안 다룬다.
- 만든 정션은 Remove 탭에 자동으로 담긴다(되돌리기).
- Tree: 정션은 아이콘을 `QPainter.CompositionMode_SourceAtop` 으로 물들이고 글자 `#f08a8a`, 툴팁 `Junction -> 타깃`.
  Depth 탐색 `_walk` 는 **실제 위치**(정션을 타면 타깃 기준, realpath 호출 없이 이름을 이어 붙임)를 넘기며
  타깃이 실제 위치 자신/조상이면 안 내려간다 — 안 그러면 `A/self->A` 가 경로 길이 한계까지 내려간다.

**How to apply:** 정션을 다루는 다른 툴(A00210 · A00220)도 판별/삭제는 `tools.A00240_PathTool.app.core.junction`
을 그대로 가져다 쓰면 된다(UI 비의존). 검증은 오프스크린 PySide6 + 임시 폴더에 실제 mklink.
관련: [[wip-a00240-tree-omit]] · [[framework-tsl-attach-uuids]](경로 리스트는 `attach_uuids=False`).

**v01.21 (2026-10-12, 사용자 요청)** — Tree 정션 우클릭 `Reveal in File Explorer (Junction)` / `(Origin)`.
공용 `Framework/qt/path_context.py` 에 `origin_of(path)`(= `realpath` 가 다르면 실제 경로; 정션을 **거친** 하위 경로도 잡힘)
와 `build_path_menu` 를 두어 Tree · Expand · A00210 Maya 탭이 함께 받는다. 더블클릭은 보이는 경로 그대로(사용자 제안대로).
검증은 오프스크린 PySide6 + 실제 mklink /J, `file_opener.open_path` 를 가로채 어느 경로가 열리는지 본다.

**v01.22 (2026-10-13, 사용자 버그 신고)** — n -> 1 에서 서로 다른 소스가 `same junction path as an earlier row` 로 막힘.
원인은 정션 이름이 **끝 폴더 이름만**이라 `ProjA/Content` · `ProjB/Content` 가 겹친 것(상태 문구 자체는 맞았다).
`core/junction.unique_names(sources)` — 같은 폴더에 만들 소스 중 **겹치는 것만** 상위 폴더 이름을 `_` 로 앞에 붙임
(`ProjA_Content`; 더 겹치면 한 단계 더, 다 써도 같으면 `_2`). 같은 소스 중복 행은 이름 계산에서 빼고
`same source as an earlier row` 로 거른다 — 안 빼면 둘을 가르려고 이름이 전체 경로까지 길어진다.
드라이브 루트 `D:\` 는 이름 `D`(전엔 `D:` 가 나와 폴더 이름으로 못 쓰는 꼴이었다). 검증은 plan 시나리오 + 실제 mklink 왕복 + 오프스크린 Create 탭.

**v01.23 (2026-10-13, 사용자 요청) — Create `Tree...`**: Tree 탭과 같은 트리 팝업(`_TreePickDialog`)에서 폴더를 체크해 Sources / Create In 에 담는다.
공용 `JUN_mod_fileTree_qt_v01` 에 **`checkable_folders=True`** 를 더했다(폴더 행에 체크박스, `checkable_files` 와 같은 기억/신호, 함께 켤 수 있음).
설계: 두 리스트가 팝업 하나를 공유(트리 유지) · 처음 열 때 Tree 탭 경로로 시작 · Add 뒤 체크 비우고 닫음 · 파일은 체크 없음 + 기본 감춤.
**테스트 함정**: 공용 checkTree 는 마우스를 viewport 필터로 먹어 `item.setCheckState` 로는 위젯에 알려지지 않는다 → `tree._check_behaviors[0].set_checked(items, Qt.Checked)` 로
사용자 클릭을 흉내낸다. 모달 `exec_()` 는 `QTimer.singleShot` 드라이버 + 워치독(`os._exit`)으로 돌리고, 드라이버가 `accept()` 에 못 가면 영원히 멈춘다.
