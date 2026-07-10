# A00030_quickTool — Quick Tool (사용 안내)

자주 쓰는 자잘한 작업을 버튼 하나로 처리하는 잡동사니 툴이다. 플레이백 갱신 범위 전환, 선택 출력,
FBX 노멀 임포트 옵션, 텍스처 파일 노드 생성, 오브젝트별 클러스터 생성을 모아뒀다.

- 버전: `V01.13` (파일 헤더 주석 / `str_headTitle`)
- 위치: `JUN_All/tools/A00030_quickTool`
- 형태: 아키텍처 (A) — **maya.cmds UI** 툴

---

## 1. 폴더 구조

```
A00030_quickTool/
├── __init__.py              # from .launcher import run
├── launcher.py              # run(reload_module=False) -> build__()
├── config.py                # DEV_MODE
├── MOD_QuickTool_v01.py     # 본체 (콜백 + JUN_ToolUI_QuickTool + build__)
├── __dragDrop_A00030.py     # 셸프 버튼 설치
└── icon/A00030_quickTool.(png|svg)
```

## 2. 설치 / 실행

`__dragDrop_A00030.py` 를 Maya 뷰포트로 드래그&드롭 → 셸프 버튼 설치.
이후 셸프 버튼 또는 `tools.A00030_quickTool.run(True)` 로 실행한다(`True` 면 reload).

## 3. UI 구성

| 요소 | 동작 |
|------|------|
| **Pin (always on top)** (v01.13~) | 켜면 이 창이 다른 창들 위에 항상 유지된다 |
| **Update window** — `Selected` / `All Windows` | `playbackOptions(view=...)` 를 `active` / `all` 로 전환 |
| **print** — `Print Selected` | 현재 선택을 스크립트 에디터에 출력 |
| **Import option** — `Import FBX normal` | FBX 임포트 시 `OverrideNormalsLock` 을 켠다 |
| **Create tool** — `Create texture file` | `file` + `place2dTexture` 를 만들고 UV 관련 어트리뷰트를 전부 연결 |
| **Create tool** — `Cluster Each` (v01.12~) | 선택한 **오브젝트마다 클러스터를 하나씩** 만든다 |

## 4. 동작 규칙

### Pin (always on top)
`maya.cmds` 창에는 최상단 고정 플래그가 없다. 그래서 `Framework/qt/maya_window.py` 의
`maya_ui_widget(<창 이름>)` 으로 창의 Qt 핸들(`MQtUtil.findWindow` → `wrapInstance`)을 얻어
`Qt.WindowStaysOnTopHint` 를 토글한다. Qt 는 윈도우 플래그를 바꾸면 창을 숨기므로, 토글 뒤
반드시 `show()` 를 다시 부른다. (Qt 툴들의 Pin 과 같은 방식 — `A00110` / `A00220` / `A00340`)

> `maya_ui_widget()` 은 공용 헬퍼다. 다른 `maya.cmds` 툴에 Pin 을 붙일 때 그대로 재사용하면 된다.

### Cluster Each
`cmds.cluster` 는 **선택 전체에 클러스터 하나**를 만든다. 오브젝트마다 따로 걸려면 하나씩 선택해서
호출해야 하므로, 선택 목록을 돌며 `cmds.select(obj, replace=True)` → `cmds.cluster(relative=True)` 를
반복한다. 여러 개여도 `undo_chunk()` 로 묶어 **Ctrl+Z 한 번**에 되돌아간다. 끝나면 생성된 핸들을 선택한다.

## 5. 로그 · 문제 해결

- `Created 3 cluster(s): [...]` — `Cluster Each` 성공. 아무것도 선택하지 않으면
  `Select object(s) first.` 경고.
- `Pin: could not access this window as a Qt widget.` — 창의 Qt 핸들을 못 찾은 경우.
  창을 닫았다 다시 열어본다.

## 6. 변경 이력 (요약)

파일 헤더 주석에 버전 이력이 있다. 최근:

- `V01.11` — rename uv 버튼 제거
- `V01.12` — Create tool 에 `Cluster Each` 추가
- `V01.13` — **`Pin (always on top)` 토글 추가**, **`Anim Tool` 섹션 제거**
  (rotate X / rotate Z / translate Y 입력 + `Rotate X Z to zero` 버튼, 콜백
  `JUN_cmd_anim_rot_x_z_to_zero`, `JUN_mod_tfg` 의존 제거). 섹션이 빠진 만큼 창 높이 450 → 300.
  > `Update window` 의 콜백 `JUN_cmd_update_window_for_anim` 은 이름에 anim 이 들어가지만
  > Anim Tool 이 아니라 `playbackOptions` 토글이므로 남아 있다.
