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
│  [Recursive] [Show Recorded Only] [File Types ▾]  [Scan]│
│ Remote [..] Branch [..] Author [.....]  [Save Settings]│
└────────────────────────────────────────────────────────┘
 Name filter [................................]  [ Filter ]
┌ 파일 목록 ───────────┐ ┌ 상세 ───────────────────────┐
│ File / Author /      │ │ [ thumbnail 320x180 ]        │
│ Thumb / Record / 수정│ │ [Capture Region][Load Image] │
│ (우클릭 →            │ │ Author [...........]         │
│  Show in File        │ │ Log history (read only)[Expand]│
│  Explorer)           │ │ New note [...]               │
│ ...                  │ │ [Add Log Entry][Save Record] │
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
2. **스캔**: `Scan Dir` 지정(보통 Project Root 하위) → **Scan**. **모든 확장자**의 파일 목록이 뜬다
   (`.mb`/`.ma` 뿐 아니라 `.fbx`/`.obj`/`.png` 등도 포함, v01.14).
   - `Thumb`/`Record` 열의 `O` 는 썸네일·기록 존재 표시. Project Root 밖 파일은 회색(`out of project root`)으로 비활성.
   - **Recursive**: 하위 폴더까지 재귀 스캔.
   - **Show Recorded Only**: 기록(Save Record)이 있는 파일만 남긴다 — 이 툴로 관리 중인 파일만 추리는 용도.
   - **File Types ▾**: 스캔에서 발견된 확장자 목록 중 **표시할 것만 체크**(All 포함). 메뉴는 여러 개를 연속
     토글해도 닫히지 않고, 버튼 라벨에 선택 요약(`File Types: mb, ma`)이 보인다.
   - **Name filter**: 파일 목록 위 입력란에 키워드를 넣고 **Filter**(또는 Enter) — **제목에 키워드가 포함된
     파일만** 표시(대소문자 무시), 비우면 전체.
   - 위 필터들은 **재스캔 없이 즉시 중첩 적용**된다(Recorded/Types 상태는 prefs 에 저장).
   - **우클릭 → Show in File Explorer**: 목록의 파일을 우클릭하면 그 파일을 **탐색기에서 선택 상태로** 연다.
   - 파일 선택 후 상세 패널의 **Log history** 가 길면 **Expand** 로 큰 창에서 볼 수 있다.
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
- **Branch** 입력은 **편집 가능한 드롭다운** — 펼치면 Store Repo 의 실제 git 브랜치(로컬 + 원격추적, 중복
  제거)를 보여줘 올바른 이름을 고를 수 있다(직접 타이핑도 가능). `main`/`master` 혼동 같은 브랜치명 불일치로
  생기는 `src refspec ... does not match any` push 오류를 줄인다.
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
- **Reference 점선 엣지(v01.16)**: 한 마야 파일이 다른 파일을 **reference 로 불러오는 관계**를 계보와 별도로
  표현한다. **Connect Mode** 를 켠 상태에서 *Connect Mode* 버튼 옆 **엣지 종류 드롭다운**을 **`Reference
  (dashed)`** 로 바꾸고 **참조 대상(불러와지는 파일) → 참조하는 파일** 로 드래그하면 **회색 점선 화살표**(채운
  삼각 화살촉)가 생긴다. reference 는 계보(parents)와 **독립** — **레인/색/Auto Layout 에 영향을 주지 않고**
  자체 순환 검사를 가진다. 그래프 JSON 에 노드별 `references` 목록으로 저장(구버전 그래프도 그대로 로드).
  점선 엣지도 클릭 선택 후 Delete 로 지운다. (드롭다운 기본값 `Lineage (parent)` = 기존 실선 계보.)
- **노드/엣지 색 수동 지정(v01.16~17)**: 러버밴드로 **여러 노드·엣지를 선택**한 뒤 **`Set Color...`**(색
  선택창)로 **선택 대상 전부의 색을 한 번에** 바꾼다. **`Reset Color`** 는 기본색으로 되돌린다(노드=레인색,
  계보 엣지=자식 레인색, reference 엣지=회색). 노드 수동색은 노드별 `color`, **엣지 수동색은 그래프 JSON
  의 `edge_colors`**(`kind:src>dst` 키)로 저장된다. 끝점 노드를 지우면 관련 엣지 색도 정리된다. (v01.16 은
  노드 색만, **v01.17 부터 엣지 색도** 지정 가능.)
- **겹치는 화살표 분리(v01.17)**: 같은 두 노드 사이에 **계보 + reference 화살표가 동시에** 있으면 예전엔 같은
  앵커로 **포개져** 보였다. 이제 같은 노드쌍 엣지들을 **가로로 균등하게 벌려** 각 화살표·화살촉이 구분된다.
- **엣지 종류 즉시 변환(v01.18)**: 화살표(엣지)를 **선택한 상태에서** *Connect Mode* 옆 **엣지 종류 드롭다운**
  을 `Lineage (parent)` / `Reference (dashed)` 로 바꾸면 **선택된 화살표가 그 종류로 즉시 변환**된다(방향은
  유지, 모양도 실선 빈 V ↔ 점선 채운 삼각으로 바로 바뀜). 내부적으로 계보(`parents`)와 `references` 사이로
  관계를 옮기고, 지정해 둔 엣지 색도 함께 따라간다. 변환이 **순환을 만들면 거부**된다. (엣지를 선택하지 않은
  상태에서는 예전처럼 *새로 그릴* 엣지의 종류만 정한다.)
- **버전업 / 브랜치 지정(v01.03)**: 노드를 선택하면 **Node** 패널의 **Relation to parent** 에서 부모와의
  관계를 고른다 — `Auto`(토폴로지 기본: 생성 순서상 첫 자식이 메인 라인) / **Version-up (main line)**
  (부모와 **같은 색** = 버전업 라인 상속) / **Branch (variation)**(강제로 **새 레인 = 다른 색**). 같은
  부모에서 어느 자식을 버전업으로, 어느 자식을 브랜치로 볼지 추가 순서와 무관하게 직접 바꿀 수 있다.
  (루트 노드처럼 부모가 없으면 비활성.) 색은 항상 관계에서 파생되므로 의미와 색이 어긋나지 않는다.
- **캔버스 조작(v01.03)**: 마우스 **휠로 줌**(커서 기준, 0.15x~4.0x), **중간 버튼 드래그로 화면 이동(pan)**.
  좌클릭(선택·노드 드래그)·Connect Mode 와 충돌하지 않는다.
  - **팬 범위 무제한(v01.15)**: 예전엔 노드 영역 바깥 200px 에서 팬이 막혔다(스크롤바가 sceneRect 에 갇힘).
    이제 콘텐츠 둘레에 한 뷰포트 크기 이상의 여백을 두고, 가장자리로 끌수록 sceneRect 가 따라 넓어져
    노드 바깥으로도 자유롭게 이동할 수 있다(다음 렌더에서 콘텐츠 기준으로 다시 줄어 영구 부풀지 않음).
- **노드 우클릭 메뉴(v01.04)**: 노드를 우클릭하면 **Reveal in File Explorer** — 그 노드 파일이 있는 폴더를
  탐색기로 열고 **파일을 선택(하이라이트)** 한다(Windows `explorer /select,`). 실제 경로가 해석될 때만
  활성(노드에 project-relative key 있음 + Project Root 설정됨 + 파일이 실제 존재) — **planned·루트 밖·
  경로에서 사라진 파일**은 비활성. 이후 우클릭 액션(Open File, Copy Path 등)을 계속 늘릴 수 있는 구조.
- **로그 기록 표시(v01.08)**: 노드를 선택하면 **Node** 패널 아래 **Log history (from record)** 에 그 노드
  파일의 작업 기록이 보인다 — **File Manager 탭의 Save Record 가 쓰는 `records/<key>.json` 을 그대로 읽어**
  같은 내용을 표시(읽기 전용). 노드 선택 시·Lineage 탭으로 돌아올 때마다 디스크에서 다시 읽어 **File Manager
  탭과 동기화**된다. record 가 매핑되는 노드에만 표시(planned·루트 밖 노드는 안내문).
- **노드·연결 삭제 / 다중 선택(v01.09)**: 노드뿐 아니라 **연결선(엣지)도 클릭으로 선택**해 지울 수 있다
  (얇은 곡선도 잘 잡히게 hit 영역을 넓혔고, 선택된 엣지는 흰색·굵게 강조). **Delete/Backspace** 로
  현재 선택(노드·연결 혼합)을 **확인 팝업 없이** 삭제 — 연결 삭제는 자식의 그 부모 링크만 제거하고,
  노드 삭제는 다른 노드의 고아 참조까지 정리한다. **빈 캔버스를 드래그하면 러버밴드 다중 선택**(사각형에
  **일부라도 걸친** 노드·연결 선택 — 전체를 감쌀 필요 없음, v01.10 부터 intersect). Connect Mode 중에는 선 긋기에 집중하도록 러버밴드를 끄고, 끄면 다시 켜진다.
  **Delete Node** 버튼도 선택된 **여러 노드를 한 번에**(팝업 없이) 삭제한다.
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

## 4-C. Path Structure 탭 — 폴더 구조 템플릿 (v01.01, 선택 기록 v01.07)

베이스 폴더의 **하위 폴더 구조**를 JSON 으로 저장(`<store_dir>/path_structures/<name>.json`, git 동기화)하고,
다른 PC 의 `Project Root` 아래에 **폴더만 재생성**한다(파일 미생성). 베이스는 project_root 상대경로로
저장되어 PC 가 달라도 동작한다.

```
┌ Save Structure ───────────────────────────────────────┐
│ Base Folder [............................] [Browse...] │
│ Folders to record              [v] All     [ Scan ]   │
│ ┌──────────────────────────────────────────────────┐ │
│ │ [v] 00_asset                                       │ │  ← 최상위 폴더 + 체크박스
│ │ [ ] 01_shot                                        │ │     (체크된 것만 기록)
│ │ [v] 02_output                                      │ │
│ └──────────────────────────────────────────────────┘ │
│ Name [................]                                │
│ [ ] Recursive (capture full nested tree)  [Capture][Save]│
└────────────────────────────────────────────────────────┘
┌ Saved Structures ─────────────────────────────────────┐
│ (저장된 구조 목록)   [Refresh][Recreate][Delete]      │
│ Preview (트리뷰)                                       │
└────────────────────────────────────────────────────────┘
```

**선택 기록(v01.07)**: 베이스의 **모든** 경로가 아니라 **체크한 최상위 폴더만** 기록한다.

- **Folders to record**: Base 의 **최상위 하위 폴더 이름**이 체크박스와 함께 리스트업된다(파일 무시).
  Base 를 고르거나 바꾸면(또는 **Scan**) 목록이 채워지고, 재스캔해도 기존 체크 상태는 이름 기준으로 보존된다.
- **All** 체크박스: 전체 폴더를 한 번에 선택/해제(= 전체 기록). 모든 항목이 체크돼 있을 때만 켜진 상태로 표시된다.
- **Recursive**: 체크된 최상위 폴더의 **하위 트리 전체**까지 캡처(끄면 최상위 폴더만).
- **Capture**: 체크된 폴더만 모아 (미저장 상태로) Preview 에 트리로 보여준다. 폴더가 있는데 하나도
  체크 안 하면 경고. → **Name** 입력 후 **Save** 로 JSON 저장(File Manager 탭의 **Push** 로 동기화).
- **Recreate**: 저장된 구조를 선택해 현재 `Project Root` 아래에 폴더를 생성(이미 있으면 건너뜀).

**사용 흐름**: Base 지정 → (Scan) → 기록할 폴더 체크(또는 **All**) → (필요 시 Recursive) →
**Capture** → **Name** 입력 → **Save** → **Push**. 받는 PC 에서 같은 구조 선택 → **Recreate**.

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
