---
title: Framework 공용 위젯 — MOD_fileTree_qt (폴더 트리)
aliases: [JUN_mod_fileTree_qt, 폴더 트리 위젯, file tree, Path Tree]
tags: [framework, qt, widget, tree, file, maya-python]
updated: 2026-10-12
---

# `JUN_mod_fileTree_qt_v01` — 폴더 트리 위젯

`JUN_All/Framework/qt/MOD_fileTree_qt_v01.py` (+ `Framework/core/tree_scanner.py` · `Framework/core/prefetcher.py`)

**A00240_PathTool 의 Tree 탭을 그대로 Framework 로 올린 것**이다 (2026-10-12, A00240 v01.20).
A00210_FileManager 의 Maya 탭이 같은 트리로 마야 파일을 고르기 때문에 한 벌만 둔다 — 릴리즈본은
툴마다 Framework 사본만 동봉하므로 툴 간 import 는 남의 PC 에서 열리지 않는다.
A00240 의 `tree_tab.py` · `core/tree_scanner.py` · `core/prefetcher.py` 는 re-export 한 줄만 남았다.

기능 자체(Browse · Build · Adaptive · Depth · Show files · File Types · Refresh(Selected / Recursive) · Omit ·
Filter · Expand · 우클릭 Reveal / Copy file path · 더블클릭 · 정션 연한 빨강 · 선읽기)는
[`A00240_PathTool.md` 10장](A00240_PathTool.md#10-tree-탭--경로를-트리뷰로-보기) 그대로다. 여기는 **위젯으로 쓸 때의 API** 만 적는다.

```python
from Framework.qt.MOD_fileTree_qt_v01 import JUN_mod_fileTree_qt_v01

tree = JUN_mod_fileTree_qt_v01()                                   # A00240 과 같은 기본
tree = JUN_mod_fileTree_qt_v01(checkable_files=True,               # 파일 행에 체크박스
                               default_types=("ma", "mb", "fbx"))  # 처음 체크해 둘 확장자
tree.ipf_path.setText(path); tree.on_build()
tree.checksChanged.connect(lambda paths: ...)                      # 체크된 절대경로 목록
tree.checked_paths()  /  tree.set_checked_paths(paths, True)  /  tree.clear_checks()
```

## 옵션 (기본값은 전부 꺼져 있어 A00240 은 그대로)

| 옵션 | 뜻 |
|------|----|
| `checkable_files=True` | **파일 행에만** 체크박스. 폴더 · `...` 행에는 없다(기본 플래그의 `ItemIsUserCheckable` 을 벗긴다). Shift / Ctrl 로 여러 행을 고른 뒤 체크 하나로 전부 체크/해제 — 공용 [`JUN_mod_checkTree_qt_v01`](Framework_MOD_checkTree_qt.md) 동작 |
| `default_types=(...)` | 처음 발견된 확장자 중 **File Types 에서 체크해 둘 것**(점 없는 소문자). 나머지는 메뉴에 보이되 꺼진다. `None` 이면 지금처럼 전부 체크 |

## 체크 상태는 경로로 기억한다

Build · Refresh · 필터 · File Types · Show files 로 행이 **다시 만들어져도** 체크가 남고, Expand 창(큰 트리)과도
공유된다 — 펼침 · 선택을 경로로 적어 뒀다 되입히는 것과 같은 자리에서 `_checked`(경로 집합) 를 본다.
`checked_paths()` 는 캐시에서 사라진 경로를 뺀 목록(대소문자 무시 정렬)이다.

## 우클릭 · 더블클릭은 공용 헬퍼

`Framework/qt/path_context.py` — `attach_path_context(view, path_of_item, title)` 가 `Reveal in File Explorer` /
`Copy file path` 메뉴와 더블클릭(= Reveal) 을 QListWidget · QTreeWidget 에 붙인다. 경로가 **정션을 거치면**
(`origin_of(path)` — `realpath` 가 다른 곳을 가리킴) Reveal 이 `(Junction)`(보이는 경로) / `(Origin)`(실제 폴더)
둘로 갈린다(2026-10-12, A00240 v01.21). `build_path_menu(view, path)` 는 메뉴를 만들기만 한다(테스트 · 항목 추가용). A00210 Maya 탭의
Maya File 리스트 · Reference 트리도 같은 헬퍼를 써서 문구 · 실패 안내가 같다.

## 쓰는 곳

- `A00240_PathTool` Tree 탭 (re-export, 옵션 없음)
- `A00210_FileManager` Maya > Reference (`checkable_files=True, default_types=("ma","mb","fbx")`)

## 검증 (오프스크린 PySide6 QTest, 2026-10-12)

체크박스 클릭 → 체크 · Shift 범위 선택 뒤 체크 하나로 3행 전부 · 선택 유지 · 안 고른 행은 그 행만 ·
Refresh / File Types 변경 뒤 체크 유지 · `set_checked_paths` / `clear_checks` · Space · 기본 생성은 체크박스 없음
· `default_types` 밖 확장자는 꺼짐 — 21 항목. A00240 창 생성 · Build · 필터 · Refresh 재확인.
