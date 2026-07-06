# A00340_SelectionTool

마야에서 선택된 오브젝트들을 **버튼 하나로 빠르게 다시 선택**하는 in-Maya PySide 툴.
A00240_PathTool 처럼 버튼을 자유롭게 추가·삭제·순서변경 하고, Profile 로 원하는
종류끼리 버튼 세트를 나눠 보관한다.

- **버전**: v01.03 (2026-07-06)
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
8. **Always on Top** — 상단 헤더 행 오른쪽의 `Pin` 버튼(체크형). 켜면 창이 다른 마야
   창들보다 항상 위에 유지되고(`Qt.WindowStaysOnTopHint`) 라벨이 `Pinned` 로 바뀐다.
   다시 누르면 해제. 버튼은 고정 크기라 토글해도 위치·크기가 변하지 않는다.
   (플래그 변경 후 창이 숨는 Qt 특성을 피하려 내부에서 `show()` 재호출)

---

## 코드 구성

```
A00340_SelectionTool/
├── __init__.py                 # run() 노출
├── launch.py                   # run(reload_module=True): 창 재생성 + blue_dark 테마
├── __dragDrop_A00340.py        # 셸프 설치(드롭 진입점)
├── icon/                       # 셸프 아이콘 (png + svg, 파란 선택 마퀴+커서)
├── CHANGELOG.md
├── data/                       # 프로파일 JSON 저장소
└── app/
    ├── config/version.py       # VERSION / LAST_UPDATE
    ├── core/
    │   ├── prefs.py            # 프로파일/카테고리/버튼 영속화 (UI·DCC 비의존)
    │   └── maya_select.py      # 선택 캡처 / 오브젝트 선택 (maya.cmds 어댑터)
    └── ui/
        ├── main_window.py      # 마야 parent 창 + 로그 + About
        └── selection_tab.py    # Profile/Category/Selection 버튼 UI + 편집
```

- `core` 는 UI 와 분리. `prefs.py` 는 마야 비의존(순수 JSON), `maya_select.py` 만
  `maya.cmds` 사용.
- 모든 UI 문자열/로그는 영어. 주석/문서만 한국어.
