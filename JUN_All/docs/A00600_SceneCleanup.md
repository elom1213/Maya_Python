---
title: A00600_SceneCleanup 사용법
aliases: [Scene Cleanup, SceneCleanup, A00600]
tags: [maya-python, tool-guide, scene-cleanup, display-layer, anim-layer, hypershade]
updated: 2026-11-05
---

# A00600_SceneCleanup 사용법

열린 마야 씬을 **체크한 항목대로 한 번에 정리**하는 in-Maya PySide 툴(arch B).
창을 열 때마다 **모든 항목이 체크**되어 있고, `Run Cleanup` 한 번 → 확인 → 위에서부터 순서대로 실행한다.
**Ctrl+Z 한 번**에 정리 전체가 되돌아간다.

- **버전**: `app/config/version.py` (v01.00)
- **설치**: `__dragDrop_A00600.py` 를 Maya 뷰포트로 드래그&드롭 → 셸프 버튼 **Cleanup** → `tools.A00600_SceneCleanup.run(True)`
  (ToolLauncher `UTIL` 프로파일 `Scene` 칸에도 있다)
- **계획서**: [`plans/A00600_SceneCleanup_plan.md`](plans/A00600_SceneCleanup_plan.md) (마야 실측 근거 §2)

## 1. 항목

| 순서 | 항목 (UI) | 하는 일 |
|------|-----------|---------|
| 1 | `Delete all display layers` | 디스플레이 레이어 전부. `defaultLayer` 는 마야 내부 노드라 남는다. 멤버 오브젝트는 그대로. |
| 2 | `Delete all animation layers (incl. BaseAnimation)` | 애니메이션 레이어 전부 — **루트 `BaseAnimation` 까지 지워 Layer Editor 의 Anim 탭에 아무것도 안 보이게** 한다. |
| 3 | `Delete unused nodes (Hypershade)` | **Hypershade > Edit > Delete Unused Nodes 와 똑같다** — 마야 MEL `MLdeleteUnused` 를 그대로 부른다. |

### 애니메이션 레이어 — 주의

- 루트를 지우면 마야가 Base 커브를 어트리뷰트에 다시 꽂는다. **Base 레이어 애니메이션만 남고 다른 레이어의 키는 사라진다.**
  다른 레이어 동작이 필요하면 먼저 합친다(A00110 `Merge Layers` 등).
- 자식 레이어를 하나씩 지우면 `BaseAnimation` 이 홀로 남는다 → 이 툴은 항상 **루트를 지운다**(이름을 박지 않고 질의).
  `BaseAnimation` 만 남은 씬도 사라진다. 지운 뒤 새 키를 찍어도 다시 생기지 않는다(실측).
- 잠긴 레이어 · 중첩 레이어도 지운다.
- **레퍼런스에서 온 애니메이션 레이어가 있으면 루트를 지울 수 없다**(마야 한계) → 로컬 레이어만 지우고
  `[WARN] BaseAnimation stays visible : ...` 경고를 낸다. 레퍼런스를 임포트한 뒤 다시 돌리면 사라진다.

### Unused nodes — Hypershade 와 같은 것

마야 `MLdeleteUnused.mel` 의 3 단계: 빈 셰이딩 그룹 → 그룹에 안 물린 머티리얼 → 출력이 안 쓰이는 텍스처 · 유틸리티(반복).
기본 머티리얼(`lambert1` 등)과 레퍼런스 노드는 지우지 않는다. 시험에서 마야 `MLdeleteUnused` 직접 호출과 **지운 노드 목록이 같은지** 대조한다.
지운 이름은 로그에 남는다(12 개 넘으면 `... (+N)`).

## 2. UI

- `Cleanup Items` 체크 목록 — 항목에 마우스를 올리면 자세한 설명(툴팁). Shift / Ctrl 로 여러 행을 골라 한 번에 체크(공용 checkList).
- `Check All` · `Uncheck All`
- `Run Cleanup` — 체크한 항목 목록을 보여 주는 확인 창 → 실행. 아무것도 체크 안 했으면 로그 안내만.
- 로그 — 항목마다 `removed N (이름들)` / `nothing to remove`, 경고 `[WARN]`, 실패 `[ERROR]`(한 항목이 실패해도 나머지는 돈다), 끝에 `Done : ...`.
- 체크 상태는 기억하지 않는다 — 열 때마다 전부 체크.

## 3. 항목 추가하는 법

`app/core/cleanup_items.py` 에 클래스 하나 + `ITEMS` 에 한 줄. UI · runner 는 고치지 않는다.

```python
class UnknownNodesItem(CleanupItem):
    key = "unknown_nodes"
    label = "Delete unknown nodes"          # UI 글자 (영어)
    tooltip = "..."
    default = True                          # 열 때 체크

    def run(self):
        return maya_cleanup.delete_unknown_nodes()   # CleanupResult(removed, warnings)

ITEMS = [..., UnknownNodesItem()]           # 이 순서로 실행
```

정리 함수는 공용 `Framework/core/maya_cleanup.py` 에 둔다(다른 툴도 쓸 수 있게). 시험 `tests/test_scene_cleanup.py` 에 항목 시험을 더한다.

## 4. 구조

```
A00600_SceneCleanup/
├─ __init__.py · launch.py · __dragDrop_A00600.py
├─ icon/A00600_SceneCleanup.svg (+ .png)    # 빗자루
├─ app/config/version.py
├─ app/core/cleanup_items.py               # CleanupItem + ITEMS 레지스트리
├─ app/core/cleanup_runner.py              # 체크한 항목 순서대로, undo 청크 하나, Layer Editor 갱신
├─ app/ui/main_window.py
└─ tests/test_scene_cleanup.py             # mayapy 오프스크린 33/33
Framework/core/maya_cleanup.py             # delete_display_layers · delete_animation_layers · delete_unused_nodes · refresh_layer_editors
```

## 5. 시험

`"C:\Program Files\Autodesk\Maya2024\bin\mayapy.exe" tests/test_scene_cleanup.py` — 33/33 (2026-11-05).
전부 실행 · undo 한 번 복원 · 체크 안 한 항목 · `BaseAnimation` 홀로 · 중첩 · 잠긴 레이어 · Hypershade 대조 · 레퍼런스 레이어 · 항목 예외 · UI.
**GUI 확인 아직.**
