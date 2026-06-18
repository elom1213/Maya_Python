# A00210_FileManager — 사용 안내

Maya 씬 파일(`.mb` / `.ma`)의 **버전·작업 기록 추적** 파이프라인 툴.
경로를 지정하면 그 폴더의 Maya 파일들이 **어떤 작업인지(작업자·기록)** 와 **썸네일** 로 보이고,
기록을 **git 으로 push/pull** 해 **어느 PC 에서나 동일하게 로그를 추적**한다.
**원본 mb/ma 는 push 대상이 아니다.**

> 이 툴은 Maya 안에서 도는 툴이 아니라 `A00080_KWI_creator_V02` 처럼 **Windows 에서 독립 실행되는
> PySide6 앱** 이다. Maya 설치/실행 없이 동작한다.

---

## 1. 핵심 개념

| 개념 | 설명 |
|------|------|
| **Project Root** | Maya 파일들이 모여 있는 작업 루트. 기록 키(key)를 이 기준 **상대경로**로 만든다. |
| **Store Repo** | 기록(JSON)·썸네일(PNG)을 모아두는 **중앙 git 데이터 리포**(예: `JUN_FileManager_data`). |
| **key** | `Project Root` 기준 상대경로(예: `chars/charA_rig.mb`). PC 가 달라도(예: `P:/proj` vs `D:/work`) **같은 파일이 같은 기록**에 매핑된다. |
| **원본 제외** | 원본 mb/ma 는 Store Repo 에 애초에 들어가지 않는다(+ `.gitignore` 로 `*.mb`/`*.ma` 이중 차단). |

스토어 레이아웃:
```
JUN_FileManager_data/        # git repo
├── .gitignore               # *.mb, *.ma, __pycache__/
├── records/<key>.json       # records/chars/charA_rig.mb.json
└── thumbs/<key>.png         # thumbs/chars/charA_rig.mb.png
```

PC 마다 다른 절대경로·작업자명은 git 으로 공유하지 않고 **로컬 prefs** 에 저장한다:
`%USERPROFILE%/.jun_filemanager/prefs.json` (push 대상 아님).

---

## 2. 실행

- **개발 실행**: `python JUN_All/tools/A00210_FileManager/launch.py`
- **exe 빌드**: 툴 폴더의 `build_exe.bat`(PyInstaller, `launch.spec`) → `dist/A00210_FileManager.exe`
- 필요 패키지: `PySide6`, `pyinstaller`. git sync 는 **시스템 git(PATH)** 을 사용한다(별도 패키지 없음).

---

## 3. 화면 구성

```
┌ Settings ─────────────────────────────────────────────┐
│ Project Root [............] [Browse]                   │
│ Store Repo   [............] [Browse]                   │
│ Scan Dir     [............] [Browse]                   │
│                            [Recursive]      [ Scan ]   │
│ Remote [..] Branch [..] Author [.....]  [Save Settings]│
└────────────────────────────────────────────────────────┘
┌ 파일 목록 ───────────┐ ┌ 상세 ───────────────────────┐
│ File / Author /      │ │ [ thumbnail 320x180 ]        │
│ Thumb / Record / 수정│ │ [Capture Region][Load Image] │
│ ...                  │ │ Author [...........]         │
│                      │ │ Log history (read only)      │
│                      │ │ New note [...]               │
│                      │ │ [Add Log Entry][Save Record] │
└──────────────────────┘ └──────────────────────────────┘
┌ Git Sync ────────────────────────────────────────────┐
│ [ Pull ] [ Push ]            status...                 │
└────────────────────────────────────────────────────────┘
( 하단 로그 출력 )
```

---

## 4. 사용 흐름

1. **설정**: `Project Root`, `Store Repo`, `Remote`/`Branch`, `Author` 를 채우고 **Save Settings**.
   - 처음이라면 **Pull**(또는 Push) 시 Store Repo 가 git repo 가 아니면 자동으로 `git init` + 스켈레톤(`records/`,
     `thumbs/`, `.gitignore`)을 만든다. 원격에서 받아오려면 Store Repo 를 비운 폴더로 두고 원격 URL 을 사용한다.
2. **스캔**: `Scan Dir` 지정(보통 Project Root 하위) → **Scan**. `.mb`/`.ma` 목록이 뜬다.
   - `Thumb`/`Record` 열의 `O` 는 썸네일·기록 존재 표시. Project Root 밖 파일은 회색(`out of project root`)으로 비활성.
3. **기록 작성**: 파일을 선택 → 우측에서 **Author** 입력, **New note** 작성 후 **Add Log Entry**(타임스탬프 자동) →
   **Save Record**. `records/<key>.json` 이 생성/갱신된다.
4. **썸네일**: **Capture Region** → 화면이 **살짝 어두워지며(실제 화면은 비쳐 보임)** 드래그로 영역 선택
   (예: Maya 뷰포트, 뷰어 등 화면에 보이는 것). 드래그한 영역만 **또렷하게** 보여 캡쳐 범위를 확인할 수 있다
   (Win+Shift+S 와 유사, Windows 10/11 공통). 선택 즉시 `thumbs/<key>.png` 로 저장되고 미리보기가
   갱신된다. (`Esc` 취소)
   - 외부 이미지를 쓰려면 **Load Image...** 로 PNG/JPG 를 지정한다.
5. **공유(Push/Pull)**:
   - **Push**: `records`/`thumbs` 변경을 커밋 후 원격에 푸시. **원본 mb/ma 는 포함되지 않는다.**
   - **Pull**: 다른 PC 에서 같은 `Project Root` 를 지정하고 Pull 하면, 동일 상대경로 키로 기록·썸네일이 그대로 보인다.

### 5-A. 배포받은 사용자: 원클릭 데이터 동기화 (v01.06)

툴(릴리즈본)을 git 으로 받은 사용자는 **데이터 리포를 따로 clone/설정하지 않아도** 동기화된다.
툴에 **중앙 데이터 리포의 URL·브랜치와 기본 clone 경로가 번들**돼 있기 때문이다
(`app/config/data_repo.py`). 

- **첫 Pull**: Store Repo 가 비어 있으면 번들된 **Remote URL** 을 기본 경로
  `~/.jun_filemanager/JUN_FileManager_data` 에 **자동 clone** 한 뒤 pull 한다. 사용자는 **Pull 한 번**이면 된다.
- **Settings** 의 `Store Repo`/`Remote`/`Branch`/`Remote URL` 은 번들 기본값으로 **미리 채워진다**(리포를
  포크/이전했다면 `Remote URL`/`Branch` 만 바꿔 Save). 데이터 리포 기본 브랜치는 **`master`**.
- 이후 Push/Pull 은 기존과 동일하게 같은 중앙 리포로 동기화된다.

> **인증 주의**: 중앙 데이터 리포가 **private** 이면, clone 하려면 사용자에게 **그 GitHub 리포 접근 권한 +
> 캐시된 git 자격증명**(시스템 git)이 있어야 한다. 권한/네트워크 문제로 clone 이 실패하면 **로컬 init 으로
> 조용히 폴백하지 않고** 하단 로그에 오류를 표시한다(끊긴 빈 repo 가 생기지 않음).
> `Project Root`(각 PC 의 Maya 파일 위치)는 데이터 동기화와 무관 — 미설정이어도 lineage/records 는 정상
> pull 된다(로컬 파일/썸네일 링크 표시에만 영향).

> 여러 PC 가 같은 파일 기록을 동시에 수정하면 git 충돌이 날 수 있다. **Push 전에 Pull** 하는 습관을 권장한다.

---

## 4-B. Lineage 탭 — 파일 브랜치/병합 관계 (v01.04)

여러 리비전 폴더(예: `JP__Revision_00010`, `JP__Revision_00020_mgear`)에 흩어진 파일들 사이의
**브랜치/병합 관계(DAG)** 를 **직접 기록**하고 `git log --graph` 스타일의 **색상 레인 트리**로 본다.
예: `JP__LUN_rig_0140.mb` 에서 베리에이션 `JP__LUN_rig_0140_mgear_0010.mb` 를 만든 관계를 명시.
**파일 포맷은 무관** — `.mb`/`.ma` 뿐 아니라 `.fbx`/`.obj`/ZBrush/텍스처 등 어떤 파일도 노드가 된다.

```
│ *  JP__LUN_rig_0140_mgear_0030.mb (planned)
│ *  JP__LUN_rig_0140_mgear_0020.mb
* │  JP__LUN_rig_0140_mgear_0010.mb
│/
* JP__LUN_rig_0140.mb
* JP__LUN_rig_0130.mb
```

- **노드**: 마야 파일 1개(또는 **Planned** = 아직 안 만든 "제작 예정" placeholder). 캔버스에서 드래그로
  자유 이동(위치 저장). **색상은 토폴로지 레인에서 자동 계산** — 브랜치는 다른 색 컬럼, 병합은 레인 수렴.
- **관계 입력**: **Connect Mode** 를 켜고 노드(부모) → 노드(자식) 로 드래그해 선을 긋는다. 자기 연결·중복·
  **순환은 자동 거부**.
- **버전업 / 브랜치 지정(v01.03)**: 노드를 선택하면 **Node** 패널의 **Relation to parent** 에서 부모와의
  관계를 고른다 — `Auto`(토폴로지 기본: 생성 순서상 첫 자식이 메인 라인) / **Version-up (main line)**
  (부모와 **같은 색** = 버전업 라인 상속) / **Branch (variation)**(강제로 **새 레인 = 다른 색**). 같은
  부모에서 어느 자식을 버전업으로, 어느 자식을 브랜치로 볼지 추가 순서와 무관하게 직접 바꿀 수 있다.
  (루트 노드처럼 부모가 없으면 비활성.) 색은 항상 관계에서 파생되므로 의미와 색이 어긋나지 않는다.
- **캔버스 조작(v01.03)**: 마우스 **휠로 줌**(커서 기준, 0.15x~4.0x), **중간 버튼 드래그로 화면 이동(pan)**.
  좌클릭(선택·노드 드래그)·Connect Mode 와 충돌하지 않는다.
- **노드 우클릭 메뉴(v01.04)**: 노드를 우클릭하면 **Reveal in File Explorer** — 그 노드 파일이 있는 폴더를
  탐색기로 열고 **파일을 선택(하이라이트)** 한다(Windows `explorer /select,`). 실제 경로가 해석될 때만
  활성(노드에 project-relative key 있음 + Project Root 설정됨 + 파일이 실제 존재) — **planned·루트 밖·
  경로에서 사라진 파일**은 비활성. 이후 우클릭 액션(Open File, Copy Path 등)을 계속 늘릴 수 있는 구조.
- **Auto Layout**: 레인(컬럼) × 토폴로지(행) 로 자동 정렬. 이후 드래그한 위치도 그대로 저장된다.
- **저장 단위**: 에셋별 **이름 붙인 그래프** — `<store_dir>/lineage/<name>.json`. 목록에서 New/Save/
  Delete. 기존 **Push/Pull 로 자동 git 동기화**(records/thumbs 와 함께).

**사용 흐름**:
1. (File Manager 탭에서) `Project Root`/`Store Repo` 설정.
2. Lineage 탭 → **New** → 이름 입력(예: `LUN_rig`).
3. 노드 추가 방법 3가지:
   - **Add Node from Scan...**: 폴더를 재귀 스캔(**모든 포맷**)해 목록에서 골라 추가. 다이얼로그 상단
     **Filter** 에 확장자(예: `mb ma fbx obj`)를 넣어 목록을 좁힐 수 있다(빈칸 = 전체). **Check/Uncheck
     Visible** 로 보이는 항목 일괄 토글.
   - **Add File...**: 임의의 단일 파일을 포맷 무관하게 바로 노드로 추가.
   - **Add Planned Node**: 아직 없는 파일("제작 예정") placeholder 추가 후 **Node** 패널에서 이름 변경.
   - 스캔/파일 추가 시 파일이 Project Root 안이면 기존 record/썸네일에 자동 링크된다(밖이면 링크 없이 추가).
4. **Connect Mode** 로 부모 → 자식 선 긋기(0130→0140, 0140→0010, 0140→0020, 0020→0030…).
5. **Auto Layout** → 색상 레인 트리 확인. 노드 선택 시 우측 **Node** 패널에서 이름/Planned/**Relation to
   parent(버전업·브랜치)**/라벨/연결 키·썸네일 미리보기. 휠 줌·중간 버튼 팬으로 캔버스 탐색.
6. **Save** → **Push**(File Manager 탭) 로 다른 PC 와 공유.

> 노드의 **File name 변경은 표시 전용** — 연결된 기록(key)은 그대로다.

---

## 5. 구조 (개발자용)

```
A00210_FileManager/
├── launch.py            # main(): QApplication → ThemeManager(blue_dark) → MainWindow → exec
├── launch.spec          # PyInstaller
├── build_exe.bat
├── requirements.txt
├── CHANGELOG.md
└── app/
    ├── config/version.py    # VERSION, LAST_UPDATE
    ├── config/data_repo.py  # 번들 데이터 리포 기본값(URL/branch/기본 clone 경로) — 배포에 포함
    ├── core/                # 순수 로직 (Qt/Maya 비의존)
    │   ├── models.py        # FileRecord, LogEntry
    │   ├── store.py         # MetaStore: 키 산출, record JSON / 썸네일 read·write
    │   ├── scanner.py       # 디렉터리 .mb/.ma 수집 + 기록 조인
    │   ├── prefs.py         # PC 로컬 설정 저장/로드
    │   ├── git_sync.py      # GitSync: ensure/clone, pull, push (subprocess git)
    │   ├── path_structure.py# 폴더 구조 템플릿 캡처/재생성
    │   └── lineage.py       # 브랜치/병합 DAG 모델 + 레인/색상 계산 (compute_lanes)
    └── ui/
        ├── main_window.py   # MainWindow(QWidget) 조립 + 핸들러
        ├── file_table.py    # 파일 목록 위젯
        ├── region_capture.py# 화면 영역 캡쳐 오버레이
        ├── path_structure_tab.py # Path Structure 탭
        └── lineage_tab.py   # Lineage 탭 (QGraphicsView 캔버스 + 노드/엣지 아이템)
```

- **core 는 Qt/Maya 를 import 하지 않는다** → 단위 테스트·exe 빌드 용이. 화면 캡쳐만 Qt(`QScreen.grabWindow`)에 의존.
- Qt 바인딩은 `Framework/qt/qt.py`(PySide6→2 폴백), 테마는 `Framework/themes/theme_manager.py`(`blue_dark.qss`) 재사용.

---

## 6. 주의

- git 은 PATH 의 시스템 `git` 을 사용한다. 미설치/원격 미설정/인증 실패/충돌은 하단 로그에 메시지로 표시되며 앱이
  죽지 않는다. 인증은 캐시된 git 자격증명에 의존한다.
- Store Repo 는 **이 프로젝트 repo 와 별개**의 전용 데이터 리포를 쓴다(예: `JUN_FileManager_data`).
- 화면 캡쳐는 멀티 모니터/DPI 환경의 좌표를 고려한다. 캡쳐 시 앱 오버레이는 잠깐 숨겨져 자기 창은 찍히지 않는다.
  캡쳐 오버레이는 **투명 배경(`WA_TranslucentBackground`)** 으로 실제 화면을 비춰 보여준다 — 풀스크린 '상태'
  대신 가상 데스크탑 geometry 로 전체 모니터를 덮는다(Windows 10/11 공통, 풀스크린+반투명의 단일모니터
  스냅/합성 깨짐 회피). (v01.05)
- UI 텍스트·로그·git 커밋 메시지는 영어, 주석/문서는 한국어(프로젝트 관례).
