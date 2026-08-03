# A00030_quickTool — Quick Tool (사용 안내)

자주 쓰는 자잘한 작업을 버튼 하나로 처리하는 잡동사니 툴이다. 플레이백 갱신 범위 전환, 선택 출력,
FBX 노멀 임포트 옵션, 텍스처 파일 노드 생성, 오브젝트별 클러스터 생성, 씬 저장 폴더 복사,
로컬 축 표시 일괄 ON/OFF 를 모아뒀다.

- 버전: `V01.15` (파일 헤더 주석 / `str_headTitle`)
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
| **File** — `Copy Scene Folder` (v01.14~) | 현재 씬이 **저장된 폴더 경로**를 클립보드에 복사(이후 Ctrl+V 붙여넣기) |
| **Display** — `Local Axis ON` / `Local Axis OFF` (v01.15~) | 선택한 오브젝트의 **로컬 축 표시를 전부 켜거나 끈다**(토글 아님) |

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

### Copy Scene Folder
현재 씬 파일의 전체 경로를 `cmds.file(q=True, sceneName=True)` 로 얻은 뒤, **파일 이름은 떼고**
`os.path.dirname` 으로 **저장 폴더까지만** 남긴다. Maya 는 슬래시(`/`) 경로를 주므로
`os.path.normpath` 로 OS 네이티브(Windows 는 `\`) 형태로 바꿔 탐색기/파일 다이얼로그에 그대로
붙여넣을 수 있게 한다. 클립보드는 **Qt(`QApplication.clipboard().setText`)** 로 설정해 Maya 밖 다른
앱에서도 **Ctrl+V** 로 붙여넣기가 된다. 아직 **저장 안 된(untitled) 씬**이면 경로가 없어 복사하지 않고
경고만 낸다.

### Local Axis ON / OFF
선택한 오브젝트의 로컬 축(`displayLocalAxis`)을 **목표 상태로 맞춘다**. 토글이 아니라 절대 상태라서
일부만 켜져 있는 섞인 선택도 한 번에 전부 ON 또는 전부 OFF 가 된다. 오브젝트마다 현재 값을 먼저
읽어(진단) **목표 상태와 다른 것만** 바꾼다.

- **`toggle -localAxis` 를 쓰지 않는다.** MEL `toggle` 은 값은 바꾸지만 undo 큐에 아무것도 남기지
  않는다(빈 청크). 그래서 실행 직후 Ctrl+Z 를 누르면 로컬 축이 아니라 **그 이전 작업이 취소된다**.
  `cmds.setAttr(<노드>.displayLocalAxis, <값>)` 은 정상적으로 undo 되므로 이쪽을 쓴다.
- 선택은 `ls(sl=True, objectsOnly=True)` 로 받아 **컴포넌트(버텍스/엣지) 선택**도 오브젝트로 해석한다.
  이때 나오는 shape 에는 `displayLocalAxis` 가 없으므로 **부모 transform 으로 올라가서** 적용한다.
- 여러 오브젝트를 `undo_chunk()` 로 묶어 **Ctrl+Z 한 번**에 되돌아간다.
- 어트리뷰트가 **잠기거나 연결**되어 있으면 바꿀 수 없으므로 해당 노드 목록을 경고로 보고한다.

## 5. 로그 · 문제 해결

- `Created 3 cluster(s): [...]` — `Cluster Each` 성공. 아무것도 선택하지 않으면
  `Select object(s) first.` 경고.
- `Copied scene folder to clipboard: <경로>` — `Copy Scene Folder` 성공. 저장 안 된 씬이면
  `Current scene has not been saved yet (no file path to copy).` 경고.
- `Pin: could not access this window as a Qt widget.` — 창의 Qt 핸들을 못 찾은 경우.
  창을 닫았다 다시 열어본다.
- `Local axis ON: changed 3 of 4 object(s).` — 4개 중 이미 켜져 있던 1개는 건너뛰었다는 뜻.
  선택이 없으면 `Select object(s) first.`, 로컬 축 어트리뷰트를 가진 오브젝트가 하나도 없으면
  `No selected object has a local axis display attribute.` 경고.
- `Local axis could not be changed on N object(s) (locked or connected): [...]` —
  해당 노드의 `displayLocalAxis` 가 잠겨 있거나 다른 노드에 연결되어 있다. 잠금을 풀고 다시 실행한다.

## 6. 변경 이력 (요약)

파일 헤더 주석에 버전 이력이 있다. 최근:

- `V01.11` — rename uv 버튼 제거
- `V01.12` — Create tool 에 `Cluster Each` 추가
- `V01.13` — **`Pin (always on top)` 토글 추가**, **`Anim Tool` 섹션 제거**
  (rotate X / rotate Z / translate Y 입력 + `Rotate X Z to zero` 버튼, 콜백
  `JUN_cmd_anim_rot_x_z_to_zero`, `JUN_mod_tfg` 의존 제거). 섹션이 빠진 만큼 창 높이 450 → 300.
  > `Update window` 의 콜백 `JUN_cmd_update_window_for_anim` 은 이름에 anim 이 들어가지만
  > Anim Tool 이 아니라 `playbackOptions` 토글이므로 남아 있다.
- `V01.14` — **`File` 섹션 + `Copy Scene Folder` 버튼 추가** (씬 저장 폴더 경로를 Qt 클립보드로 복사,
  콜백 `JUN_cmd_copy_scene_path`). 섹션이 늘어난 만큼 창 높이 300 → 360 (Copyright 문구 잘림 방지).
- `V01.15` — **`Display` 섹션 + `Local Axis ON` / `Local Axis OFF` 버튼 추가**
  (콜백 `JUN_cmd_set_local_axis(state)`, 헬퍼 `JUN_fun_resolve_local_axis_node`).
  현재 상태를 진단해 다른 것만 `setAttr` 로 바꾸며, `toggle -localAxis` 는 undo 가 안 걸려 쓰지 않는다.
  섹션이 늘어난 만큼 창 높이 360 → 420.
