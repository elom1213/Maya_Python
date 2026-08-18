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
| **Key** | 키의 존재 | Pose Key · Fill Keys(+from Selection) · Delete All |
| **Timing** | 키의 시점 | Move · Hold · Offset · Stagger |
| **Curve** | 커브의 값·형태 | Euler · **Filters**(Smooth·Intensity·Interp 한 화면, v02.01) |
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

**SmartLayer Curve Filters 이식 완료** (v02.01): **Smooth / Intensity / Interp + Use Quaternions**.
- 대상은 UI 로 확인해야 했다 — `curve_retime_widget` · `remove_spikes_widget` · `curve_bake_widget` 은
  **파일만 있고 UI 에 없다**. **파일명으로 기능을 추정하면 안 된다**(계획서 결정 2개가 무효가 됐다).
- 소스는 컴파일 `.pyc` + 라이선스가 리버스 엔지니어링 금지 → **디컴파일하지 않고 직접 구현**.
  사용자가 허락해도 라이선스 당사자는 벤더이고, 이 저장소는 공개 포트폴리오라 위험이 크다.
- 수식: Smooth = 가우시안 `[1 2 1]/4`×N, `원본 + t·(스무딩-원본)`(t<0 = Rough) /
  Intensity = **구간 평균** 기준 스케일(평균 불변) / Interp = 양 끝 키를 잇는 이징으로 끌어당김.
- 조작은 **settle 커밋 재사용**(Stagger·Peak): 드래그 중 원본에서 재계산, 놓으면 undo 한 항목 +
  슬라이더 0 복귀(→ 반복 적용). 값 쓰기는 `keyframe -e -valueChange` 라 탄젠트/레이어 보존.
- **대상은 TSL 이 아니라 씬 선택**: 그래프 에디터 선택 키(`keyframe -q -sl -name` + 커브별
  `-indexValue`)가 1순위, 없으면 타임 슬라이더 구간(`timeControl -q -rangeArray`, 폭 1프레임
  이하면 "안 고름")+ 씬 선택. 둘 다 없으면 실행 안 함. 커브→구동 플러그는 `listConnections` 로
  몇 홉 따라가 찾는다(애님 레이어면 animBlendNode 경유).
- 세 필터는 **한 화면 접이식**(원본 UI 와 같은 구성). 섹션이 작고 번갈아 쓰는 작업이면
  [[prefer-subtabs-over-stacked-collapsibles]] 의 예외가 된다.

**Expand(별도 창)는 공용 위젯을 쓴다**([[framework-expand-widget]]) — `Framework.qt` 의 `JUN_mod_expand_qt_v01`
(v02.04 에 승격, 문서 `docs/Framework_MOD_expand_qt.md`). 새로 만들지 말 것:

    panel = JUN_mod_expand_qt.JUN_mod_expand_qt_v01(title=..., object_name=..., size=...)
    panel.add_widget(...) / panel.add_layout(...)
    panel.expanded_changed.connect(lambda *_: self._fit_window_later())

핵심은 **복제가 아니라 이동**(레이아웃에 add 하면 이전 부모에서 떨어진다) — 세션·슬라이더·undo 가
한 벌뿐이라 동기화 문제가 없다. 복귀 자리는 `layout.indexOf` 로 저장. **호스트 창의 Close 는
위젯이 eventFilter 로 감시해 자동으로 접는다**(툴 closeEvent 에 정리 코드 불필요 — 빠뜨리면 본문
위젯이 함께 파괴된다). `A00290_BSTool` 은 아직 자체 구현(공용화 이전)이라 옮길 수 있다.

**"from Selection" 원버튼 패턴** (Euler v01.38 → Curve Filters v02.01 → Fill Keys v02.02):
리스트업·구간 입력 단계를 **그래프 에디터에서 고른 키** 하나로 대신한다. 고른 키가 오브젝트·채널·
구간을 다 말해 준다(커브 → `driven_plug` 로 역추적). 규칙 두 가지 —
① 감지한 값을 **위젯에 되채워** 무엇을 처리했는지 보이게 하고(필터가 켜져 있으면 비운다),
② **고른 키가 없으면 실행하지 않는다**(전 구간을 조용히 건드리는 쪽이 위험). 새 기능에도 이대로 적용.
- 쿼터니언 되돌리기는 **원래 값에 가장 가까운 해**를 골라 ±360 점프를 없앤다. 축별 키 시간이
  다르면 그 오브젝트만 채널별 폴백.
