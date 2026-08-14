---
name: wip-a00110-tab-taxonomy
description: A00110_animTool_V02 탭 분류 규칙 — 상위 탭 = 카테고리(Key/Timing/Curve/Transfer/Bake/View), 하위 탭 = 기능. V01 은 재분류 전으로 방치 (V02 v02.00)
metadata:
  node_type: memory
  type: project
---

**`A00110_animTool_V02`** = A00110_animTool 의 **탭 재분류판** (V01 v01.41 → V02 **02.00**, 2026-08-14).
**V01 은 재분류 전 상태로 그대로 둔다**(저장소 관례: 새 버전은 새 폴더).
**폴더가 `_V02` 면 버전도 `02.xx` 로 센다** — 폴더는 V02 인데 UI 가 v01.42 라 혼동을 부른다
(선례: `A00010_humanIKTool_V02`=02.00, `A00040_file_exporter_V02`=02.05). SmartLayer Curve Filters
이식 등 이후 작업은 **V02 에서** 한다. 계획서: `docs/plans/A00110_animTool_tab_reorg_plan.md`,
문서: `docs/A00110_animTool_V02.md`.

**툴을 복제해 갈랐을 때 바꿔야 하는 것**(체크리스트 — 안 바꾸면 두 툴이 서로를 닫거나 남의 모듈을 부른다):
드롭 파일 이름(`__dragDrop_A00110_V02.py`, CLAUDE.md 의 드롭 파일 규칙) · 셸프 `TOOL_LABEL` ·
아이콘 파일명 · `WINDOW_OBJECT_NAME` · 창 제목 · `launch.py` 의 `reload_for_tool`/import 경로 ·
**핫키 명령 문자열 안의 모듈 경로**(`hotkey_manager` 가 `python("import tools...")` 로 박아 둔다).

**규칙**: **상위 탭 = 카테고리 / 하위 탭 = 기능**, 예외 없음. 분류 기준은 하나 —
**"사용자가 무엇을 바꾸려 하는가"**.

| 카테고리 | 무엇이 바뀌나 | 기능 |
|---|---|---|
| **Key** | 키의 존재 | Pose Key · Fill Keys · Delete All |
| **Timing** | 키의 시점 | Move · Hold · Offset · Stagger |
| **Curve** | 커브의 값·형태 | Euler (+ SmartLayer Curve Filters 이식 예정) |
| **Transfer** | 오브젝트 간 이동 | Copy Key · Mirror Key · Follow |
| **Bake** | 키로 굽기 | Bake |
| **View** | 보기(**씬 불변**) | Graph Focus |

**왜 이렇게 됐나**: 그전엔 `Key Edit` 만 하위 탭 8개짜리 카테고리이고 나머지 5개는 기능 하나짜리
상위 탭이었다 → 새 기능이 전부 `Key Edit` 로 들어가 비대해졌다(Euler·Pose Key 가 실제로 그렇게
내려왔다). **새 기능은 위 표에서 카테고리를 먼저 고른다.**

**설계 판단**
- 하위가 하나뿐인 카테고리(Curve·Bake·View)도 **하위 탭 바를 남긴다** — Euler·Bake 페이지엔 제목
  그룹박스가 없어서, 탭 바가 없으면 기능 이름이 화면에서 사라진다.
- **View 는 씬을 바꾸지 않는 유일한 카테고리**라 따로 뒀다(나머지는 전부 "누르면 씬이 바뀐다").
- 각 카테고리의 **첫 하위 탭 = 대표 기능**(Key→Pose Key, Timing→Move, Transfer→Copy Key).
- 라벨은 짧게(창 폭 520), **전체 이름은 탭 툴팁**, 폭 모자라면 `ElideRight`.

**옮기기만 하는 리팩터가 싼 이유**: 페이지 빌더가 **전부 `JUN_mod_fit_tab_page_v01` 을 반환**하면
상위 탭이든 하위 탭이든 그대로 꽂힌다. 그래서 바뀐 코드는 **분류 표(튜플) + 상위 탭 구성**뿐이고
위젯 속성 이름은 하나도 안 건드렸다 → 핸들러·매니저·핫키 무영향. 상위·하위 **모든** 페이지가 그
타입이어야 `_fit_window` 의 창 높이 자동 맞춤이 유지된다([[prefer-subtabs-over-stacked-collapsibles]]).

**검증 방법이 핵심이었다**: 재분류 **전에** `MainWindow` 를 띄워 **위젯 속성 이름 집합 + 탭 트리**를
json 으로 스냅샷 → 재분류 후 다시 떠서 **diff**. 109/110 보존(사라진 건 옛 컨테이너 `key_edit_tabs`,
새로 생긴 건 카테고리 6개)이면 어떤 핸들러도 안 깨졌다는 뜻이다. 기능 이동 리팩터에 그대로 재사용.

**함정**: `Delete All` 은 확인 대화상자를 띄워서 headless 검증에서 기본값 `No` 로 아무것도 안 지운다
— 버그가 아니다. `QMessageBox.question` 을 Yes 로 스텁해야 실제 경로가 돈다.

**SmartLayer Curve Filters 이식은 아직 안 했다**(자리만 마련). 실제 UI 확인 결과 대상은
**Smooth / Intensity / Interpolate 3종 + Use Quaternions** — `curve_retime_widget` ·
`remove_spikes_widget` · `curve_bake_widget` 은 **파일만 있고 UI 에 없다**(파일명으로 기능을 추정하면
안 된다는 실례). 소스는 컴파일 `.pyc` 라 디컴파일하지 않고 **UI 관찰 + 실측으로 재구현**한다.
