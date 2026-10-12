---
name: wip-a00500-reloader
description: "dev/A00500_reloader (v01.00, 2026-10-12) — 손으로 붙여 넣던 리로더를 __dragDrop_A00500 셸프 툴로; dev 에 두는 이유, dev/reloader_v02 재노출을 지워선 안 되는 이유"
metadata:
  node_type: memory
  type: project
  originSessionId: 042dc05b-37df-4abd-b775-d917cf9a7c8b
  modified: 2026-10-12T03:03:35.452Z
---

2026-10-12 사용자: "`dev/reloader_mayaScript_v02.py` 를 복사해 마야 툴로 쓰고 있다, 다른 툴처럼 `__dragDrop_AXXXXX.py` 로
셸프에 설치하고 `AXXXXX_reloader` 폴더로 관리. tools 가 더 맞으면 tools 로 옮겨도 되고 dev 에 정리해도 된다."

- **dev 에 두었다** (`dev/A00500_reloader`, A00510_release_builder 와 같은 자리): `config.DEV_MODE` 에 의존하고 릴리즈본은
  `dev/` 를 통째로 제외한다([[release-layout-launch-py]]). 번호는 tools 의 다음 번호(A00490 다음) 를 썼다 — **A00500 은
  이 툴이, A00510 release_builder · A00520 icon_builder · A00530 dependency_check 가 쓴다**, 새 tools 는 A00540 부터.
- **`dev/reloader_v02.py` 는 지우지 말 것** — 40여 개 툴의 `launch.py` 가 `from dev.reloader_v02 import reload_for_tool` 을
  쓴다. 로직은 `app/core/reloader.py` 로 옮기고 그 파일은 얇은 재노출. `reload_path_list.py` 는 `app/config/reload_packages.py`.
- `launch.run(True)` 순서: `config` 리로드(DEV_MODE 변경 반영) → 리로더 자신 → `Framework`, `tools`(sys.modules 에 있는 것만,
  깊은 것부터) → 뷰포트 `inViewMessage` 로 개수. `reload_package` 는 이제 `(ok, [(name, err)])` 를 돌려준다.
- **전부 리로드는 떠 있는 다른 툴 창을 닫을 수 있다**(launch 모듈 최상단 `window_instance = None` 재실행) — 그래서 각 툴
  버튼은 `reload_for_tool`(자기 + Framework)만 쓴다. 이 버튼은 "전부 새로 읽고 싶을 때".
- 옛 세대(v01 리로더 · 모듈 목록 · 붙여넣기 스크립트 v01/v02)는 `legacy/` 에 git mv 로 보존, import 되지 않는다.
- 검증은 mayapy(run · 재노출 · DEV_MODE off · 드롭 파일 셸프 명령 exec). **마야 GUI 드롭 설치는 아직.**
- **2026-10-12 dev 정리 끝**: dev/ 에는 `__init__` · `reloader_v02`(재노출) · `check_dependencies`(재노출) · 툴 폴더 4개만.
  옛 `remove_pycache.py` 는 여기 `app/core/pycache.py` + `clean_pycache()` + 두 번째 드롭 파일 `__dragDrop_A00500_pycache.py`(드롭 파일
  이름은 파일마다 고유해야 해서 둘로). `build_icons.py` → A00520(dev/*/icon 도 훑음, --only · --ico), `check_dependencies.py` → A00530,
  `build_release.py` → A00510/legacy, `__userSetup.py` · `__memo.py` → `_archive/study_notes/100_Memo/`.

관련: [[wip-release-builder-qt]], [[new-tool-needs-icon]], [[shelf-childarray-has-separators]]
