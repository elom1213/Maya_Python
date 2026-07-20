# A00370_ToolLauncher

여러 JUN 툴을 **버튼 하나로 팝업**시키는 in-Maya PySide 숏컷 런처.
툴마다 셸프 아이콘을 따로 만들 필요 없이, 이 창 하나에서 원하는 툴을 골라 띄운다.
`A00340_SelectionTool` 과 UI·기능(카테고리 / 프로파일 / 버튼 색)은 거의 같고, 버튼을
누르면 **오브젝트 선택** 대신 **지정한 툴이 실행**되는 점만 다르다.

- **버전**: v01.03 (2026-07-13)
- **아키텍처**: (B) Standalone/Qt 앱형 구조지만 마야 안에서 실행(PySide, `maya.cmds`).
- **참고**: 프로파일/카테고리/색/레이아웃은 `A00340_SelectionTool` 을 이식.
  버튼 클릭이 툴을 실행하는 로직은 `app/core/tool_launcher.py`.

---

## 왜 쓰나 (설계 의도)

`A00080_KWI_creator_V03`, `A00260_ConstraintConverter` 처럼 **마야에서 세팅해 언리얼에
쓸 코드를 만드는 툴**들은 각각 셸프 아이콘을 만들어 불러 쓴다. 이 런처는 그런 툴들을
**하나의 창에서 버튼으로 모아** 두고 클릭 한 번에 띄우는 용도다.

핵심은 **확장성**이다. KWI/ConstraintConverter 뿐 아니라, `run()` 진입점을 노출하는
**JUN_All 의 어떤 툴이든** 그 폴더 경로만 지정하면 숏컷 버튼이 된다. 예:

```
C:\Users\USER\Desktop\JP\0030_maya_python_JUN\Maya_Python\JUN_All\tools\A00080_KWI_creator_V03
```

이 경로 하나만 지정하면 해당 툴을 버튼으로 쓸 수 있다.

---

## 개념

- **Tool 버튼** — 실행할 **툴 폴더 경로** 하나를 담는 버튼. 클릭하면 그 툴이 실행된다.
  버튼 **왼쪽에 그 툴의 아이콘**(툴 폴더의 `icon/<폴더명>.png`)이 버튼 높이만큼의
  정사각형으로 크게 표시된다(아이콘 없는 툴은 텍스트 버튼만).
  버튼마다 **색**을 지정할 수 있다(팔레트 + 스포이드).
- **Category** — 버튼을 묶는 그룹(QGroupBox). 우클릭으로 이름변경/순서변경/삭제.
- **Profile** — 상황(리깅 / 페이셜 / UE 익스포트 등)별로 나눈 버튼 세트.
  JSON 파일 1개 = 1 프로파일. New / Rename / Delete 지원. 최소 1개는 유지된다.

저장 위치(툴 폴더 내부):

```
A00370_ToolLauncher/data/
├── profiles/<profile>.json   # 예: Default.json, Facial.json
└── active.json               # {"active": "<현재 프로파일>"}
```

프로파일 JSON 구조:

```json
{
  "categories": [
    {
      "name": "Maya to Unreal",
      "buttons": [
        {
          "name": "KWI Creator V03",
          "path": "C:/.../JUN_All/tools/A00080_KWI_creator_V03",
          "color": "#ff7a59"
        }
      ]
    }
  ]
}
```

`color` 는 지정했을 때만 저장된다.

---

## 설치

1. `tools/A00370_ToolLauncher/__dragDrop_A00370.py` 를 **마야 뷰포트로 드래그&드롭**한다.
   현재 셸프에 `ToolLauncher` 버튼이 설치된다.
2. 셸프 버튼을 누르면 런처 창이 뜬다. (또는 스크립트로
   `import tools.A00370_ToolLauncher as t; t.run(True)`)

> 드롭 파일 이름이 툴마다 고유(`__dragDrop_A00370.py`)하고, 설치 후 자기 자신을
> `sys.modules` 에서 제거하므로 다른 툴 드롭과 충돌하지 않는다(프로젝트 공통 규칙).

---

## 사용법

### 1) 카테고리 만들기
`Create` 그룹의 **Category** → 이름 입력. 버튼은 카테고리 안에 쌓인다.

### 2) 툴 버튼 추가
`Create` 그룹의 **Tool** → 다이얼로그에서
- **Add to category**: 넣을 카테고리 선택
- **Tool folder**: `Browse...` 로 툴 폴더 선택 (예: `A00080_KWI_creator_V03` 폴더)
- **Button name**: 버튼 이름 (비우면 폴더명이 자동으로 들어감)

경로는 저장 전에 검증된다(**폴더 존재 + `__init__.py` 보유**). 유효하지 않으면
경고 후 다시 입력받는다.

### 3) 툴 실행
버튼을 **클릭**하면 그 경로의 툴이 실행(팝업)된다. 결과는 하단 로그에 나온다.
- 내부적으로 `<부모폴더>.<툴폴더>` (예: `tools.A00080_KWI_creator_V03`) 를 import 해
  `run()` 을 호출한다 — 그 툴의 셸프 버튼이 하는 것과 **동일한 실행 경로**다.

### 4) Reload on launch (기본 ON)
`Create` 그룹의 체크박스. 켜져 있으면 실행 전에 툴을 리로드한다(`run(True)`, 셸프
버튼과 동일 — DEV_MODE 에서 코드 수정 즉시 반영). 끄면 이미 로드된 툴을 다시 보여주기만
한다(`run(False)`).

### 5) 버튼/카테고리 편집 (우클릭)
- **버튼 우클릭**: Move Up/Down · Rename · **Change Path...**(폴더 다시 지정) ·
  **Reveal in Explorer**(툴 폴더 열기) · Set Color... / Reset Color ·
  Change Category · Delete
- **카테고리 우클릭**: Move Up/Down · Rename · Delete

### 6) 색 지정
- 버튼 우클릭 **Set Color...** → 팔레트(+ 화면 스포이드)로 개별 색 지정.
- **Color Select** 모드를 켜면 버튼이 체크형으로 바뀐다. 카테고리를 넘나들며 여러 개를
  체크한 뒤 **Apply Color...** 로 한 번에 칠하거나 **Clear Color** 로 되돌린다.
  (이 모드에서는 클릭이 '실행' 대신 '체크'다.)

### 7) 프로파일
`Profile` 그룹에서 상황별 버튼 세트를 New / Rename / Delete 로 관리한다.
콤보를 바꾸면 해당 세트로 즉시 전환된다.

### 8) PC 이식 — 상대경로 저장(자동) + Environment
버튼은 `path` 에 **JUN_All 루트 기준 상대경로**(`tools/A000XX_name`)를 저장한다. 이 값은
**PC 가 달라도 동일**하므로, JUN_All 위치가 다른 다른 PC 에서 프로파일을 열어도 그냥 동작하고
프로파일 JSON 도 흔들리지 않는다(= git 병합 충돌 없음). 실제 절대경로는 실행 시점에 이 PC 의
JUN_All 루트로 resolve 한다.

- **자동 감지** — 런처 자신이 `JUN_All/tools/A00370.../` 안에 있으므로 현재 PC 의 JUN_All 루트를
  항상 정확히 안다. 보통은 **아무것도 안 만져도 된다**.
- **JUN_All Root 필드 / Browse / Apply Root** — 다른 JUN_All 을 가리키고 싶을 때만 쓴다.
  `Browse...` 로 폴더를 고르고 **`Apply Root`** 를 누르면 그 루트가 이 PC 의 **오버라이드**로 저장된다
  (자동 감지값과 같으면 오버라이드를 지운다). 오버라이드는 **gitignore 된 로컬 파일
  (`data/local_env.json`)** 에만 저장되어 PC 간 충돌이 없다. `Detect` 는 오버라이드를 지우고 다시
  자동 감지값으로 되돌린다.
- **Make Paths Portable** — (일회성 마이그레이션) 예전 버전/다른 PC 에서 만든 **절대경로** 버튼이
  섞여 있으면 모두 상대경로(`tools/…`)로 바꿔 저장한다. 이미 상대경로면 파일이 안 바뀐다(idempotent).
  `JUN_All/tools` 밖을 가리키는(=`tools` 앵커가 없는) 외부 버튼은 상대화할 수 없어 skip 으로 보고한다.
- **자동 복구(self-heal)** — 저장된 경로가 (구버전 절대경로라) 그대로 들어와도, 클릭 시 현재 PC 의
  루트로 resolve 해 실제로 있으면 거기서 실행한다.

> **git 추적 범위**: 프로파일(`data/profiles/*.json`, 버튼 세트)은 상대경로라 PC 간 동일하므로
> **계속 추적·공유**한다. PC별 상태인 `data/local_env.json`(루트 오버라이드)와
> `data/active.json`(마지막 연 프로파일)은 **gitignore** 되어 추적하지 않는다.

### 9) 레이아웃 / 기타
- 컨트롤 패널과 버튼 영역 사이의 **스플리터**를 드래그해 비율 조절.
- **Controls** 막대(▾/▸)를 클릭하면 Profile/Create/Color/Log 를 **한 번에 접어**
  버튼 영역을 넓힌다.
- 헤더 우측 **Pin** 버튼: 창을 다른 마야 창 위에 항상 표시(토글).

---

## 동작 원리 (경로 → 실행)

`app/core/tool_launcher.py`:

1. `resolve_module(path)` — 툴 폴더 경로에서
   `(<JUN_All 루트>, "<부모폴더명>.<툴폴더명>")` 을 뽑는다.
   JUN 규칙이면 `("...\JUN_All", "tools.A000XX_name")`.
2. `validate(path)` — 폴더 존재 + `__init__.py` 보유 확인.
3. `launch(path, reload_module)` — 루트를 `sys.path` 에 추가 →
   `importlib.import_module(module_name)` → 그 모듈의 `run(reload_module)` 호출.
   (`run` 이 인자를 안 받으면 무인자로 재시도.)

즉 셸프 버튼이 하던 `import tools.A000XX_name; run(True)` 를 **경로 기반으로 일반화**한
것이다. 그래서 `run()` 진입점을 가진 JUN_All 의 모든 툴에 그대로 적용된다.

경로 이식(PC 간 공유)용 헬퍼:

- `jun_all_root()` — 이 파일 위치(`JUN_All/tools/A00370.../app/core/tool_launcher.py`)에서
  거슬러 올라가 **현재 PC 의 JUN_All 루트**를 반환. 자동감지의 근거.
- `rebase_to_root(path, new_root)` — 경로의 마지막 `tools` 세그먼트를 앵커로 잡아 그 뒤를
  `<new_root>/tools/...` 로 다시 잇는다(`tools` 앵커 없으면 `None` = 건너뜀).
- `prefs.rebase_all_profiles(new_root)` — 모든 프로파일의 모든 버튼에 위를 적용하고
  바뀐 파일만 저장, 통계(changed/unchanged/skipped/total/profiles)를 반환.
- `launch()` 는 저장 경로가 깨졌을 때 `rebase_to_root(path, jun_all_root())` 로 자동 복구를
  한 번 시도한다.

---

## 파일 구조

```
A00370_ToolLauncher/
├── __init__.py                 # run() 노출
├── launch.py                   # run(): 창 생성 + yellow_light 테마
├── __dragDrop_A00370.py        # 셸프 설치 드롭 파일
├── CHANGELOG.md
├── icon/                       # A00370_ToolLauncher.svg / .png (로켓 + 실행 버튼)
├── data/                       # profiles/*.json, active.json (생성물)
└── app/
    ├── config/version.py       # VERSION / LAST_UPDATE
    ├── core/
    │   ├── prefs.py            # 프로파일/카테고리/버튼(path) 저장 (UI/DCC 비의존)
    │   └── tool_launcher.py    # 경로 → import → run() 실행 (UI 비의존)
    └── ui/
        ├── main_window.py      # 창 + 헤더(Help/Pin) + 로그
        └── launcher_tab.py     # 프로파일/카테고리/버튼/색 UI
```
