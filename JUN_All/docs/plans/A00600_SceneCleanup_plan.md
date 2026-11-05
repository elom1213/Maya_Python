---
title: A00600_SceneCleanup 계획서
tags: [maya-python, plan, scene-cleanup, display-layer, anim-layer, hypershade]
updated: 2026-11-05
---

# A00600_SceneCleanup 계획서

열린 마야 씬을 **체크한 항목대로 한 번에 정리**하는 in-Maya PySide 툴(arch B).
항목은 계속 늘어난다 — **항목 추가 = 클래스 하나 + 등록 한 줄**, UI 는 손대지 않는다.

## 1. 요구 (2026-11-05 사용자)

| # | 요구 | 결정 |
|---|------|------|
| 1 | 레이어 모두 제거 | 디스플레이 레이어 전부(`defaultLayer` 제외) |
| 2 | 애니메이션 레이어 모두 제거 | **`BaseAnimation` 도 마야에 보이지 않게** — 루트를 지운다 |
| 3 | 안 쓰는 머티리얼 제거 | **Hypershade 의 "Delete Unused Nodes" 와 같게** = 마야 MEL `MLdeleteUnused` 그대로 호출 |
| 4 | 셋을 체크박스로, **기본 모두 체크** | 창을 열 때마다 전부 체크(기억하지 않는다 — "모두 체크" 가 기본이어야 하므로) |
| 5 | 항목이 계속 늘어난다 | 항목 레지스트리(§3) |

기존 툴에 넣지 않고 새 툴로 한다(판단 근거는 이 계획 전 대화: A00480 = 파일 입출력, A00470 = 머티리얼만,
A00110 = 애니메이션 · 이미 큼, A00030 = 단발 버튼 모음, A00210 = 마야 밖 mayapy 일괄 처리).

## 2. 마야 동작 실측 (mayapy 2024, 2026-11-05)

- **Hypershade > Edit > Delete Unused Nodes** = `hyperShadePanelMenuCommand(..., "deleteUnusedNodes")` → **`MLdeleteUnused;`**
  (`scripts/others/hyperShadePanel.mel` 6789행). `MLdeleteUnused.mel` 의 3 단계:
  빈 셰이딩 그룹 → 그룹에 안 물린 머티리얼 → 출력이 안 쓰이는 텍스처 · 유틸리티(반복). 기본 머티리얼 · **레퍼런스 노드는 지우지 않는다**
  (`deleteIfNotReferenced`). 반환 = 지운 개수.
  - 실측: 안 쓰는 blinn + 거기 물린 file + 외톨이 multiplyDivide → 3 개 삭제, 쓰는 lambert · SG 는 그대로.
  - **undo 청크 하나로 완전히 되돌아간다**(노드 목록 동일).
  - mayapy 에서는 `source "MLdeleteUnused.mel"` 이 먼저 필요했다 → `exists` 로 확인하고 없으면 source.
- **애니메이션 레이어**: `delete <root>` (루트 = `animLayer -q -root`, 이름 `BaseAnimation` 을 박지 않는다) →
  `ls -type animLayer` 가 **빈 목록** = Layer Editor 의 Anim 탭에 `BaseAnimation` 도 없다.
  - 마야가 Base 커브를 어트리뷰트에 다시 꽂는다 → **Base 레이어 애니메이션만 남고 다른 레이어 키는 사라진다**(툴팁 · 로그에 밝힌다).
  - **`BaseAnimation` 만 남은 씬**(자식 레이어를 손으로 다 지운 상태)도 루트 삭제로 사라진다 — 레이어를 하나씩 지우면 이 경우가 남는다.
  - 지운 뒤 새 키를 찍어도 `BaseAnimation` 이 다시 생기지 않는다.
  - 한 undo 로 되돌아간다.
  - 레퍼런스 레이어가 있으면 루트를 못 지운다 → 로컬 레이어만 하나씩 지우고 `BaseAnimation` 이 남는다는 **경고**(마야 한계).
  - GUI 에서는 지운 뒤 `updateAnimLayerEditor("AnimLayerTab")` (`startup/layerEditor.mel`) 로 Anim 탭을 다시 그린다(있을 때만).
- **디스플레이 레이어**: `defaultLayer` · 레퍼런스 레이어 제외하고 `delete`(잠긴 노드는 `lockNode -l 0` 후). 멤버 노드는 그대로.
  (A00210 `ref_importer.delete_display_layers` · `delete_animation_layers` 와 같은 규칙 — v01.43 에서 쓰는 중)

## 3. 구조

```
Framework/core/maya_cleanup.py          # 정리 함수 (DCC 동작만, UI 없음) - 다른 툴도 쓸 수 있게 공용
    delete_display_layers(log) -> CleanupResult
    delete_animation_layers(log) -> CleanupResult
    delete_unused_nodes(log) -> CleanupResult      # MLdeleteUnused
    refresh_layer_editors()

tools/A00600_SceneCleanup/
├─ __init__.py · launch.py · __dragDrop_A00600.py · icon/A00600_SceneCleanup.svg(+png)
├─ app/config/version.py
├─ app/core/cleanup_items.py   # CleanupItem 기반 클래스 + ITEMS 레지스트리
├─ app/core/cleanup_runner.py  # 체크한 항목을 순서대로, undo 청크 하나, 결과 요약
├─ app/ui/main_window.py       # 체크 목록 · Check All / Uncheck All · Run Cleanup · 로그
└─ tests/test_scene_cleanup.py   # 코어 · runner · UI(오프스크린) 한 파일
```

### 3-1. 항목(CleanupItem)

```python
class CleanupItem(object):
    key = "display_layers"        # 고유 키
    label = "Delete all display layers"
    tooltip = "..."
    default = True                # 창을 열 때 체크 상태
    def run(self, log): -> CleanupResult(removed=[...], warnings=[...])

ITEMS = [DisplayLayersItem(), AnimLayersItem(), UnusedNodesItem()]   # 이 순서로 실행
```

- **새 항목 = 클래스 하나 + `ITEMS` 에 한 줄.** UI 는 `ITEMS` 를 읽어 체크 행을 만든다.
- 실행 순서 = 목록 순서. 애니메이션 레이어를 지운 뒤 Unused Nodes 를 돌린다(레이어가 남긴 고아 노드가 있으면 함께 정리되도록 맨 뒤).

### 3-2. 실행(runner)

- 체크한 항목만, **undo 청크 하나**(`Framework.core.maya_undo.undo_chunk`) — Ctrl+Z 한 번에 전부 되돌린다.
- 한 항목이 예외로 실패해도 나머지는 돈다(로그에 `[ERROR]`).
- 끝나면 Layer Editor 를 다시 그린다.
- 로그: 항목마다 `Display layers: removed 2 (L_geo, L_rig)` · 경고는 `[WARN]` · 끝에 합계.

### 3-3. UI (영어)

- 상단: 메뉴 바(공용 `JUN_mod_menuBar_qt_v01`, Help > About) + Pin.
- `Cleanup Items` 체크 목록(QListWidget + 공용 `JUN_mod_checkList_qt_v01`) — **열 때 전부 체크**, 항목 툴팁.
- `Check All` · `Uncheck All` · **`Run Cleanup`**(아무것도 체크 안 했으면 안내만).
- 실행 전 확인 창 1 번(되돌리기는 Ctrl+Z 라는 안내 포함) — 씬을 지우는 툴이라.
- 공용 로그 위젯 `JUN_mod_log_qt_v01`.

## 4. 이번에 하지 않는 것

- **Scan(미리보기 개수)** — `MLdeleteUnused` 에는 "지우지 않고 세기" 가 없다. 지우고 undo 하는 방식은 가능하지만(실측 OK)
  undo 가 꺼진 씬에서는 되돌릴 수 없어 위험 → 1 차에서 뺀다. 실행 로그에 지운 이름을 전부 남긴다.
- 체크 상태 기억 — 요구 #4.
- A00210 `ref_importer` 를 이 공용 모듈로 옮기기 — 다른 툴 수정이라 따로 요청 시. (규칙은 같게 맞춰 둔다)

## 5. 시험 (mayapy 헤드리스)

- `test_scene_cleanup.py`
  - 레이어 2 개 · 애니메이션 레이어(Base + AL1) · 쓰는/안 쓰는 머티리얼 · 텍스처 · 유틸리티 씬
  - 전부 실행 → 디스플레이 레이어 `defaultLayer` 만 · **`ls -type animLayer` 빈 목록** · 안 쓰는 노드 삭제 · 쓰는 머티리얼 · SG 유지 · Base 키 유지
  - **undo 한 번** → 노드 목록 원래대로
  - 체크 안 한 항목은 안 돈다
  - **`BaseAnimation` 만 남은 씬** → 사라짐
  - **Unused Nodes 결과 = Hypershade 와 같은지** — 같은 씬을 복제해 `MLdeleteUnused` 직접 호출 결과와 지운 노드 목록 대조
  - 레퍼런스 애니메이션 레이어 → 로컬만 지우고 경고
  - 한 항목 예외 → 나머지는 돈다
- 같은 파일 UI 부분(오프스크린) — 행 3 개 = `ITEMS` 순서 · 전부 체크 · Uncheck/Check All · 체크 안 한 항목은 runner 에 안 넘어감.

## 6. 문서 · 기록

- `docs/A00600_SceneCleanup.md` 사용 안내(항목 표 · 실측 근거 · 항목 추가 방법)
- `docs/WORKLOG.md`, 메모리 `wip-a00600-scenecleanup.md`
- 아이콘 32x32 svg + png(빗자루)
