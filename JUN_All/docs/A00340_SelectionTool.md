# A00340_SelectionTool

마야에서 선택된 오브젝트들을 **버튼 하나로 빠르게 다시 선택**하는 in-Maya PySide 툴.
A00240_PathTool 처럼 버튼을 자유롭게 추가·삭제·순서변경 하고, Profile 로 원하는
종류끼리 버튼 세트를 나눠 보관한다.

- **버전**: v01.15 (2026-10-27) — Buttons 탭 버튼을 **드래그로 옮겨** 순서 · 카테고리 변경(A00240 과 같은 방식) · v01.14 (2026-10-27) — 로그창이 **접힌 채(Shrink 켜짐) 시작**, `Show` 로 편다 · v01.13 (2026-10-27) — `Pin` 이 켜진(`Pinned`) 동안 **연한 빨강**(공용 `Framework.qt.pin_style`, 다른 툴과 같음) · v01.12 (2026-10-27) — **창 가로 길이를 드래그로 자유롭게** 줄일 수 있게(Rules 상태 줄의 긴 폴더 경로가 최소 폭을 잡고 있었다, 최소 폭 1494 → 286px) · v01.11 (2026-10-26) — 최상위 탭 **`Buttons` / `Rules`**. Rules = 규칙 하나가 json 파일 하나, 어느 씬에서든 그 이름 목록을 선택(§Rules 탭)
- **아키텍처**: (B) Standalone/Qt 앱형 구조지만 마야 안에서 실행(PySide, `maya.cmds`).
- **참고**: 구성/편집 흐름은 `A00240_PathTool`, 마야 연동(셸프 설치·창 parenting·리로드)은
  `A00310_SearchTool` 를 이식.

---

## 개념

- **Selection 버튼** — 현재 마야 선택을 캡처해 만든 버튼. 클릭하면 저장된 오브젝트가
  씬에서 선택된다. 씬에서 이름이 바뀌거나 삭제된 오브젝트는 건너뛰고 로그로 알려준다.
  버튼마다 **색**을 지정할 수 있다(팔레트 + 스포이드).
- **Category** — 버튼을 묶는 그룹(QGroupBox). 우클릭으로 이름변경/순서변경/삭제.
- **Profile** — 캐릭터/에셋처럼 서로 다른 버튼 세트. JSON 파일 1개 = 1 프로파일.
  New / Rename / Delete 지원. 최소 1개는 유지된다.

저장 위치(툴 폴더 내부):

```
A00340_SelectionTool/data/
├── profiles/<profile>.json   # 예: Default.json, BodyRig.json
└── active.json               # {"active": "<현재 프로파일>"}
```

프로파일 JSON 구조:

```json
{
  "categories": [
    {
      "name": "FK Controls",
      "buttons": [
        { "name": "Arms", "objects": ["fk_arm_L", "fk_arm_R"], "color": "#3a7bd5" }
      ]
    }
  ]
}
```

---

## 사용법

1. **설치** — `__dragDrop_A00340.py` 를 마야 뷰포트로 드래그&드롭하면 현재 셸프에
   `SelectTool` 버튼이 생긴다. 이후 셸프 버튼 또는 `tools.A00340_SelectionTool.run(True)`.
2. **Category 만들기** — Create 그룹의 `Category` 버튼.
3. **Selection 버튼 만들기** — 마야에서 오브젝트를 선택한 뒤 Create 그룹의 `Selection`
   버튼 → 카테고리 선택 + 버튼 이름 입력. 현재 선택이 그 버튼에 저장된다.
4. **선택하기** — 버튼 클릭. `Add` 체크박스가 켜져 있으면 현재 선택을 지우지 않고
   누적 선택한다.
5. **편집** — 버튼/카테고리를 우클릭:
   - Category: Move Up/Down · Rename · Delete
   - Button: Move Up/Down · Rename · **Update Objects**(현재 선택으로 교체) ·
     **Add Objects**(현재 선택을 이어붙임) · **Set Color...** · **Reset Color** ·
     Change Category · Delete
6. **버튼 색 지정(개별)** — 버튼 우클릭 `Set Color...` 는 색 팔레트를 띄운다.
   다이얼로그의 **Pick Screen Color(스포이드)** 로 화면의 아무 색이나 집어 복사할 수
   있다. 배경 밝기에 따라 라벨 글자색(검정/흰색)이 자동으로 정해져 항상 잘 읽힌다.
   `Reset Color` 로 테마 기본 스타일로 되돌린다. 색은 프로파일 JSON 의 버튼별
   `"color"`(hex) 로 저장돼 세션이 바뀌어도 유지된다.
7. **버튼 색 지정(여러 개 한번에)** — `Color` 바의 **`Color Select`** 를 켜면 색칠
   모드가 된다. 이때 모든 버튼이 체크형으로 바뀌고, 버튼을 클릭하면 오브젝트 선택
   대신 **체크/해제**가 된다. **카테고리를 넘나들며** 원하는 버튼을 자유롭게 체크한
   뒤 **`Apply Color...`** 로 고른 한 색을 체크된 버튼 전부에 일괄 적용한다.
   **`Clear Color`** 는 체크된 버튼들의 색을 지운다. 체크된 버튼은 강조 테두리로
   표시되고, 색을 적용해도 체크 상태는 유지돼 다른 색을 연이어 칠할 수 있다. 모드를
   끄면 체크가 초기화되고 클릭이 다시 '선택'으로 돌아온다.
8. **화면 레이아웃(분리·접기)** — 창은 **상하 스플리터**로 나뉜다. 위 = 컨트롤
   패널(**Profile / Create / Color**), 아래 = 생성한 버튼 모음, 그리고 **로그창은 스플리터 밖
   창 맨 아래**(v01.09~). 가운데 핸들을 드래그해 두 영역의 비율을 조절한다. 컨트롤 3칸은
   **하나의 접이식 `Controls` 박스**로 묶여 있어, 제목 바(▾/▸)를 클릭하면 세 칸을 **한 번에**
   접었다 편다. 접으면 위 pane 이 헤더만 남게 줄고 그만큼 버튼 영역이 넓어진다(펴면 원위치).
   - **기본 상태에서 Controls 는 스크롤 없이 전부 보인다**(v01.09~) — 창이 처음 보일 때
     컨트롤 내용의 실제 높이를 재서 위 pane 을 그 높이로 연다(폰트·테마마다 달라 상수로 박지
     않는다). 핸들로 더 줄이면 그때는 스크롤된다.
   - v01.08 에서 좌우 배치(Controls 왼쪽 | 버튼 오른쪽)로 바꿨다가 v01.09 에서 **취소**하고
     상하로 되돌렸다.
   - **`View > Show Controls`** (v01.07~) — 접어도 헤더 줄과 스크롤 영역의 최소 높이는 남아
     버튼 영역이 충분히 넓어지지 않는다. 메뉴 바의 `View`(Help 왼쪽) 에서 체크를 끄면 **위 pane
     자체를 숨겨** 스플리터 핸들까지 사라지고 버튼 모음이 창 전체를 쓴다. 다시 켜면 숨기기
     직전의 비율로 돌아온다. 상태는 `data/active.json` 의 `show_controls` 에 남아 **다음에 열
     때도 같다.** 로그창은 창 맨 아래라 숨겨도 그대로 보인다.
   - **`View > Show Profile`** (v01.10~) — 탐색기를 열어 **지금 활성인 프로파일 json** 을 선택(하이라이트)한
     채로 보여 준다. 이 PC 에서 툴이 실제로 읽고 쓰는 파일(`<툴>/data/profiles/<프로파일>.json`)이라 백업 ·
     다른 PC 로 복사할 때 쓴다. 파일이 없으면 `profiles` 폴더를 열고 로그에 `[WARN]` 을 남긴다.
     탐색기 열기는 공용 `Framework.core.file_opener.open_path`.
9. **Always on Top** — 상단 헤더 행 오른쪽의 `Pin` 버튼(체크형). 켜면 창이 다른 마야
   창들보다 항상 위에 유지되고(`Qt.WindowStaysOnTopHint`) 라벨이 `Pinned` 로 바뀐다.
   다시 누르면 해제. 버튼은 고정 크기라 토글해도 위치·크기가 변하지 않는다.
   (플래그 변경 후 창이 숨는 Qt 특성을 피하려 내부에서 `show()` 재호출)

---

## 드래그로 버튼 옮기기 (v01.15)

선택 버튼을 **누른 채 끌어서 놓으면** 그 자리로 간다 — `A00240_PathTool` 의 Path 버튼과 같은 동작이다.

- **같은 카테고리 안**: 버튼 사이로 끌어 놓으면 순서가 바뀐다. **다른 카테고리**로 끌어 놓으면 그쪽으로 옮겨진다
  (`Change Category` 와 같은 규칙 — 대상에 같은 이름의 버튼이 있으면 막고 알려 준다).
- 끄는 동안 **놓일 자리에 가로줄**이 보이고 커서는 움켜쥔 손 모양이 된다. 목록이 길면 **위 · 아래 가장자리에서 저절로
  스크롤**된다. **`Esc`** 로 취소.
- 누른 뒤 거의 안 움직이고 놓으면 **평소 클릭**(오브젝트 선택)이다. 드래그 판정 거리는 OS 기본(`startDragDistance`).
- **Color Select** 가 켜져 있으면 끌지 않고 체크만 한다.
- 우클릭 `Move Up / Move Down` · `Change Category` 는 그대로 있다. 바뀐 순서는 프로파일 JSON 에 저장된다.
- 구현: 네이티브 `QDrag` 가 아니라 버튼 서브클래스(`_DragButton`)의 마우스 이벤트로 처리한다. 버튼은 이름이 아니라
  (카테고리 인덱스, 버튼 인덱스)로 집어 같은 이름이 둘 있어도 다른 쪽이 움직이지 않는다.
- 검증(오프스크린, 실제 마우스 이벤트): 같은 카테고리 순서 · 다른 카테고리 이동 · 같은 이름 막기 · Esc 취소 ·
  드래그 놓음은 클릭이 아님 · 살짝 클릭은 선택 · 색칠 모드는 드래그 없음 · 저장 · 커서 복원 — 12 항목.

## 창 폭 (v01.12)

창은 가로로 **자유롭게** 줄일 수 있다(최소 약 286px, 오프스크린 측정 - 남은 하한은 맨 아래 공용 로그창의 버튼 줄).

- 예전에는 Rules 탭 상태 줄이 규칙 폴더 **전체 경로**를 썼다. 경로는 공백 없는 한 단어라 줄이 바뀌지 않고, 그 길이가
  창의 최소 폭이 됐다. `QTabWidget` 은 **안 보이는 탭까지** 가장 넓은 페이지의 최소 폭을 따르므로 Buttons 탭을 보고
  있어도 창이 줄지 않았다(1494px).
- 지금 상태 줄은 끝 두 폴더(`3 rule(s) in .../data/rules`)만 쓰고 전체 경로는 **툴팁**에 있다(`Show Folder` 로 연다).
- Rules 페이지는 Buttons 페이지처럼 스크롤 칸 안이다 - 버튼 줄보다 좁히면 가로 스크롤바가 생긴다. 저작권 줄은 줄바꿈된다.

## Rules 탭 (v01.11)

**규칙(rule)** 은 어느 씬에서든 다시 선택할 **오브젝트 이름 목록** 하나다. `Buttons` 탭의 버튼과 하는 일은 같지만
저장 단위가 다르다 — 버튼은 프로파일 json 하나에 여러 개가 들어가고, **규칙은 json 파일 하나 = 규칙 하나**다.
폴더만 봐도 어떤 규칙이 있는지 보이고, 다른 PC 와는 **파일을 복사하는 것으로 공유가 끝난다.**

```
<A00340_SelectionTool>/data/rules/<rule name>.json
{
  "name": "rule_01",
  "description": "left arm fk joints",
  "objects": ["jnt_01", "jnt_02", "jnt_03"]
}
```

| 버튼 / 동작 | 하는 일 |
|------|------|
| `New Rule from Selection` | 현재 마야 선택을 이름을 물어 규칙 json 으로 저장. 파일 이름은 규칙 이름을 따른다(Windows 금지 문자만 `_`) |
| `Select` / 규칙 **더블클릭** | 고른 규칙의 오브젝트를 씬에서 선택. 여러 규칙을 Ctrl/Shift 로 고르면 **합집합**. `Add to current selection` 이면 누적 |
| `Update Objects` · 우클릭 `Add Objects (append)` | 규칙의 오브젝트를 현재 선택으로 **교체** / 뒤에 **추가** |
| `Rename` | 규칙 이름을 바꾼다 — json 안의 `name` 과 **파일 이름을 함께**. 같은 이름 · 같은 파일 이름이 있으면 거부 |
| `Delete` | 고른 규칙(여러 개 가능)의 json 을 한 번 확인한 뒤 지운다. **되돌릴 수 없다**(규칙 폴더 안의 .json 만 지움) |
| `Description` | 메모. 포커스를 잃을 때 json 에 저장(규칙 하나를 골랐을 때만 편집) |
| `Reload` · `Show Folder` · `View > Show Rules Folder` | 밖에서 json 을 넣었으면 Reload. 탭을 다시 열 때도 폴더를 다시 읽는다 |

오른쪽 `Objects` 목록은 고른 규칙의 이름을 저장 순서로 보여 주고 **지금 씬 기준**으로 색을 칠한다:

| 색 | 뜻 | Select 때 |
|----|----|----------|
| 기본 | 씬에 하나 있다 | 선택 |
| **빨강** | 씬에 없다 | 건너뛰고 `[WARN] n missing` 로그 |
| **주황** | 같은 이름이 둘 이상 | **전부 선택**하고 `[WARN] 'x' matches 2 nodes` 로그 |

- 오브젝트는 캡처 당시의 **짧은 이름**(`cmds.ls` 기본값)으로 저장한다 — 네임스페이스나 그룹이 달라진 씬에서도
  이름이 같으면 맞는다. 동명이 있을 때 `cmds.select(짧은이름)` 은 "More than one object matches name" 으로
  **실패**하므로(`objExists` 는 True 를 주는데도) 이름마다 `cmds.ls(name, long=True)` 로 펼쳐 고른다 (mayapy 실측).
- 깨진 json 은 `[WARN] Rule 'x.json' not loaded` 로만 알리고 건드리지 않는다. `name` 이 없는 손으로 만든 json 은
  파일 이름을 규칙 이름으로 쓴다.
- 마지막에 보던 탭(`Buttons` / `Rules`)은 `data/active.json` 의 `active_tab` 에 남아 다음에 그 탭으로 열린다.
- `data/` 는 git 제외(사용자 데이터). 규칙을 저장소로 나누고 싶으면 `data/rules/` 의 json 을 다른 경로에 두고
  복사해 쓴다.
- mayapy 실측(2026-10-26): 코어 29 항목(저장 · 금지 문자 · 파일 충돌 · 깨진 json · update · rename(대소문자만 포함) ·
  delete 범위 · union · name_status · select_names) + 오프스크린 UI 26 항목(새 규칙 · 없는/동명 선택 + 색 · Add ·
  Description · Update/Append · Rename · 합집합 · Delete · Reload · 메인 창 탭 기억). **실기 눈 확인 아직.**

---

## 코드 구성

```
A00340_SelectionTool/
├── __init__.py                 # run() 노출
├── launch.py                   # run(reload_module=True): 창 재생성 + blue_dark 테마
├── __dragDrop_A00340.py        # 셸프 설치(드롭 진입점)
├── icon/                       # 셸프 아이콘 (png + svg, 파란 선택 마퀴+커서)
├── CHANGELOG.md
├── data/                       # 프로파일 JSON(profiles/) + 규칙 JSON(rules/, v01.11) 저장소 - git 제외
└── app/
    ├── config/version.py       # VERSION / LAST_UPDATE
    ├── core/
    │   ├── prefs.py            # 프로파일/카테고리/버튼 영속화 + 창 설정(get/set_setting) (UI·DCC 비의존)
    │   ├── select_rules.py     # 규칙 json (data/rules/<name>.json) load/save/update/rename/delete (v01.11, DCC 비의존)
    │   └── maya_select.py      # 선택 캡처 / 오브젝트 선택 + name_status / select_names (maya.cmds 어댑터)
    └── ui/
        ├── main_window.py      # 마야 parent 창 + 최상위 탭 Buttons/Rules + View/Help 메뉴 + 맨 아래 로그 + About
        ├── selection_tab.py    # Buttons 탭: 상하 스플리터(접이식 Controls 박스 + 버튼 pane) UI + 편집
        │                       #   CollapsibleBox: 제목 바 하나로 컨트롤 3칸을 한 번에 접기
        └── rules_tab.py        # Rules 탭: 규칙 표 + Objects 목록(없음 빨강/동명 주황) + 편집 · Select (v01.11)
```

- `core` 는 UI 와 분리. `prefs.py` 는 마야 비의존(순수 JSON), `maya_select.py` 만
  `maya.cmds` 사용.
- 모든 UI 문자열/로그는 영어. 주석/문서만 한국어.

---

## 로그창 (v01.05)

로그창은 **공용 위젯 `JUN_mod_log_qt_v01`** 이다. 오른쪽 위에 작은 버튼 셋이 붙어 있다.

| 버튼 | 동작 |
|------|------|
| `Expand` | 로그를 **별도 창으로 옮겨** 크게 본다. 확장 중에 들어온 로그도 같은 곳에 쌓이고, 창을 닫으면 제자리로 돌아온다 |
| `Clear` | 로그를 비운다 |
| `Copy` | 로그 **전문**을 클립보드로 |

자세한 것은 [`Framework_MOD_log_qt.md`](Framework_MOD_log_qt.md).
