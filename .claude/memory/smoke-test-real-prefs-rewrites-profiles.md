---
name: smoke-test-real-prefs-rewrites-profiles
description: A00210 등 프로파일 툴을 실제 prefs 로 오프스크린 스모크하면 on_profile_changed 가 실제 프로파일 JSON 을 새 코드로 다시 저장한다 - 임시 PREFS_DIR 로만
metadata:
  node_type: memory
  type: feedback
  originSessionId: f4077785-9011-4665-a74f-6be71e7fa818
  modified: 2026-11-27T00:39:08.521Z
---

A00210 `MainWindow.on_profile_changed()` / `closeEvent` / `_save_current_to_active()` 는 떠나는 프로파일을 **`_collect_prefs()` 로 다시 저장**한다.
실제 `~/.jun_filemanager` 로 스모크 테스트하면서 프로파일을 바꾸면, **새 코드가 빼 버린 키가 실제 프로파일에서 지워진다.**

2026-11-27 v01.60 스모크에서 `Local_CH_D` · `JUN` · `MUE` 의 `recreate_to` 가 지워졌다(PC 설정 시드로 옮겨 가야 할 값, 직전 값 복구 불가 — 11-04 백업만 있음).

**Why:** 사용자 실제 설정은 되돌릴 기록이 없다(git 밖).
**How to apply:** 스모크 · 시험은 `prefs.PREFS_DIR / PROFILES_DIR / ACTIVE_PATH / PREFS_PATH` 를 임시 폴더로 바꿔 끼우고, 실제 프로파일이 필요하면 **복사본**을 임시 폴더에 넣어 쓴다.
실제 prefs 로 창을 띄워야 하면 프로파일 전환 · 창 닫기를 하지 말 것. 관련 [[wip-a00210-structure-library]]
