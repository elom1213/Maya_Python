---
name: wip-a00120-fkik-auto-devmode
description: "A00120_FKIK v01.11 — Setup Manual/Auto(네임스페이스 단위 씬 조사), Targets/Followers 접이식(기본 접힘), Search 숨김(코드 유지), Dev Mode 공용 메뉴의 Release 화면, Bake 진행률 팝업"
metadata:
  node_type: memory
  type: project
  originSessionId: 1b679bc1-ca09-4af4-b1a4-09415405fb3c
  modified: 2026-10-12T00:22:06.233Z
---

2026-10-12 사용자 요청으로 A00120_FKIK 를 v01.11 로 올렸다.

- **Auto 모드** = `app/core/fkik_scan.py` `FKIKScanner.scan()`. `cmds.ls("*BlendFKIKPos_grp*", recursive=True, type="transform", long=True)`
  로 모든 네임스페이스에서 찾아 **네임스페이스마다** 톱 노드들을 `FKIKSetup.resolve` 에 넘긴다. 같은 네임스페이스에 리그가 여럿이라
  개수 검증(24)에 걸리면 톱 노드마다 다시 풀어 `(root) | rigB_grp` 로 나눈다. 실패한 단위는 `[WARN] Skipped` 로그만.
  Auto 로 바꾸는 순간에도 조사하고, Refresh 는 전에 고른 단위를 유지한다. 리스트 TSL 은 버튼 없음 · `attach_uuids=False`
  (항목이 네임스페이스 라벨이라 노드가 아니다).
- **Release 화면** (`apply_view(False)`): Auto 라디오 선택 · 접이식 숨김 · `Bake (Constraint)` 숨김 · 로그 `set_shrunk(True)` ·
  `Force Refresh` 숨김. Manual 라디오는 남는다(요청은 "Auto 가 기본"). Developer 로 돌아올 때 Setup 모드는 건드리지 않는다.
- **Search 는 숨김만** — 사용자가 "코드를 삭제하지는 말고 ui 에서 안 보이도록" 이라고 했다. `self.search_box.setVisible(False)`.
- **창 높이**는 `showEvent` 첫 번째(테마가 입혀진 뒤)와 접이식 토글 · 화면 전환 뒤 `layout.sizeHint()` 로 다시 잡고
  `availableGeometry().height() - 80` 으로 자른다([[window-taller-than-screen-ghost]]).
- **Bake 진행률**: `FKIKMatcher.bake(..., progress=None)` 프레임마다 콜백, UI 는 `JUN_mod_progress_qt_v01` 단계 하나.
  `suspend_refresh()` 안에서도 팝업은 그려진다(Qt processEvents 는 마야 뷰포트 suspend 와 무관).

검증은 mayapy 2024 오프스크린(합성 리그 3개)까지. **마야 GUI 에서의 확인은 아직** — 특히 Release 화면의 실제 창 높이.

관련: [[framework-devmode-widget]], [[wip-a00120-fkik-bake-constraintfree]].
