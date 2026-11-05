# A00210_FileManager — PC 간 작업 파일 동기화 추적 계획서 (Sync Tracker)

> **작성** 2026-11-05 · 상태: **계획 확정 · 구현 보류** (결정 4개 반영 — 7장) · 대상: `C:\JUN\JUN_MUE` (정션) 아래 작업 파일 전부
> 요청: 여러 PC 가 같은 경로(`C:\JUN\JUN_MUE`)로 작업한다. 형상관리처럼 **어느 PC 의 파일이 최신본인지**,
> **어느 PC 가 최신본과 어긋나 있는지**(없음 · 옛것) 추적 · 감지하고 싶다.
> 예: 이 PC 에서 `5040_cleanup_BCM_KANA/00010_cleanup_KANA_00080.mb` 를 만들면, 다른 PC 에서는
> "이 파일이 없다" 를 알려 줘야 한다. 이 폴더뿐 아니라 프로젝트 전체에 대해.
> 조건: GitHub 사용 가능. Perforce · SVN 처럼 전용 서버 · 외부 장치가 필요한 방법은 후순위.

---

## 0. 결론

**파일 자체는 지금처럼 각 PC 디스크에 두고, "각 PC 가 가진 파일 목록(매니페스트)" 만 GitHub 로 주고받는다.**
매니페스트는 PC 마다 json 하나 — 경로 · 크기 · 수정 시각 · 해시. 모든 PC 의 매니페스트를 나란히 놓으면
파일마다 "누가 최신본을 가졌고, 누가 없고, 누가 옛것인지" 가 표로 나온다.

- 저장 위치는 **이미 있는 A00210 데이터 저장소** `JUN_FileManager_data`(비공개 GitHub, `main`)의
  `profiles/MUE/manifests/<루트>/<PC>.json`(추적 루트는 여러 개 — 4-1A). 새 서버 · 새 저장소 · 새 계정이 필요 없다.
  A00210 의 `GitSync` 가 이미 이 폴더 단위로 pull/push 한다(v01.45).
- PC 마다 **자기 파일 하나만 쓰므로 git 충돌이 원리상 나지 않는다.**
- 화면은 A00210 에 **`Sync` 탭**을 붙인다 — "이 PC 에 없는 파일 · 옛 파일 · 이 PC 만 가진 파일" 목록.
- 1차는 **감지 · 알림까지**. 파일 전송은 지금처럼 **구글 드라이브 수동 업/다운**을 유지하고,
  3차에서 "올릴 파일 모으기 / 받은 파일 제자리에 넣기" 로 그 흐름을 돕는다.
- 구글 드라이브에서 받은 파일은 수정 시각이 바뀌므로 **판정은 해시로** 한다(4-3).

**`.mb` 를 GitHub 에 직접 올리는 방법(git / Git LFS)은 권하지 않는다** — 프로젝트가 18.6 GB 이고 씬 하나가 50~60 MB,
버전마다 새 파일이 쌓이는 구조라 LFS 무료 한도(1 GB)를 바로 넘는다(3장).

---

## 1. 관찰 (2026-11-05, 이 PC)

| 항목 | 값 |
|------|-----|
| `C:\JUN\JUN_MUE` | 정션 → `C:\Users\USER\Desktop\JP\0001_PJ\0023_MUE_original` (이 PC 로컬 폴더, git 아님) |
| 규모 | 파일 381개 · **18.6 GB** — `.mb` 144 · `.jpg` 109 · `.png` 53 · `.pdc` 18 · `.MP4` 11 · `.fbx` 10 … |
| 동기화 | 정션은 **경로만** 맞춘다. 내용은 **수동 — 새 파일을 구글 드라이브에 올리고 다른 PC 에서 내려받아 같은 상대 경로에 넣는다**(사용자 설명). 무엇을 아직 안 옮겼는지는 기억에 의존 → 어긋남을 알 길이 없는 상태 |
| 예시 폴더 | `00_04_02_ANI_00_PJ_010/scenes/5040_cleanup_BCM_KANA/` |
| | `00010_cleanup_KANA_00010.mb` ~ `_00070.mb` (48~60 MB, 11-03 ~ 11-05) |
| | `backup/` — `*_BU.mb` 4개 + `log.txt` (저장 툴이 만드는 백업, 프로젝트 전체 `backup/` 안 파일 53개) |
| 기존 메타 | A00210 이 `JUN_FileManager_data/profiles/MUE/records/<상대경로>.mb.json` 에 파일별 노트 · 작성자 · 시각을 이미 기록 |
| 해시 속도 | 60 MB `.mb` SHA-256 1개 ≈ 0.07 초(캐시된 상태). 18.6 GB 전체 첫 해시는 디스크 속도 기준 수 분 예상 |

**핵심:** 파일 열쇠는 `C:\JUN\JUN_MUE` 기준 **상대 경로**로 잡는다(A00210 records 의 `key` 와 같은 규칙).
정션 덕분에 모든 PC 에서 같은 상대 경로가 같은 파일을 뜻한다 — 정션 대상(실제 디스크 위치)이 PC 마다 달라도 상관없다.

---

## 2. 요구사항

| # | 요구 | 예 |
|---|------|-----|
| R1 | 다른 PC 에 있는데 **이 PC 에 없는 파일** 감지 | B PC 가 `_00080.mb` 를 만듦 → A PC 에서 "Missing" |
| R2 | 같은 경로인데 **내용이 옛것**인 파일 감지 | A 에서 `_00070.mb` 를 덮어 저장 → B 의 `_00070.mb` 는 "Outdated" |
| R3 | **양쪽에서 따로 고친** 파일 감지 (충돌) | A, B 가 각자 `_00070.mb` 를 고침 → "Conflict" |
| R4 | 이 PC **에만 있는** 파일 (다른 PC 가 아직 못 받음) | "Only here" — 내가 퍼뜨려야 할 것 |
| R5 | 특정 폴더만이 아니라 **프로젝트 전체** | 381개 전부, 폴더 트리로 묶어 보기 |
| R6 | 서버 · 외부 장치 없이 | GitHub 비공개 저장소만 |
| R7 | 지운 파일을 "없음" 과 구분 (2차) | A 에서 일부러 지운 파일은 B 에게 "Deleted on A" |

---

## 3. 방법 비교

| 안 | 내용 | 장점 | 단점 | 판정 |
|----|------|------|------|------|
| **A. 매니페스트 + GitHub** | 각 PC 가 파일 목록(경로 · 크기 · 시각 · 해시)만 json 으로 GitHub 에 올리고 서로 비교 | 수백 KB 짜리 텍스트만 오감 · 기존 A00210 저장소/`GitSync` 재사용 · PC 별 파일이라 충돌 없음 · 서버 불필요 | 파일 **전송**은 별도(사람이 복사) · 스캔해야 최신 | **권장** |
| B. `.mb` 를 git / Git LFS 로 | 프로젝트 폴더 자체를 git 저장소로 | 진짜 형상관리(되돌리기 · 전송까지) | 18.6 GB · 버전이 파일명으로 쌓여 계속 늚. GitHub 파일당 100 MB 제한 → LFS 필수, LFS 무료 저장 · 전송 1 GB/월 → **유료 데이터팩 필수**. 바이너리라 병합 불가 | 비권장 |
| C. P2P 동기화 앱 (Syncthing 등) | PC 끼리 폴더를 자동 복제 | 전송까지 자동 · 서버 없음 | 두 PC 가 **동시에 켜져 있어야** 전송 · 외부 프로그램 설치 · 마야 저장 중 반쯤 쓴 파일 복제 위험 · 충돌 시 `.sync-conflict` 파일 생성 | 대안(4차 검토) |
| D. 클라우드 드라이브 **자동 동기화** (Google Drive for desktop · OneDrive) | 프로젝트 폴더 자체를 동기화 폴더로 | 전송 자동 | 18.6 GB 용량 · 회사 정책 · 온디맨드(스트리밍) 파일이 마야 레퍼런스 경로를 깨뜨릴 수 있음 · 저장 중 업로드 | 보류 |
| (현행) 구글 드라이브 **수동** 업/다운 | 새 파일만 올리고 받음 | 이미 쓰는 중 · 추가 설치 없음 | 무엇을 옮겨야 하는지 모름 · 수정 시각이 바뀜 | **안 A 와 함께 유지** — 안 A 가 "무엇을 올리고 받을지" 목록을 준다 |
| E. Perforce · SVN · NAS | 전용 서버 | 업계 표준(잠금 · 이력) | 서버 · 장치 필요 | **후순위**(요청대로) |

A 는 **B~E 와 함께 써도 된다** — 나중에 C 나 E 를 도입해도 "정말 다 맞는지" 검증하는 감시 역할로 남는다.

---

## 4. 설계 (안 A)

### 4-1. 저장 위치

```
JUN_FileManager_data/                  (비공개 GitHub, main — A00210 기존)
└── profiles/MUE/
    ├── records/ thumbs/ lineage/ path_structures/     (기존)
    └── manifests/                     (신규)
        ├── mue/DESKTOP-ABC123.json    ← 이 PC 만 쓴다 (루트별 폴더 — 4-1A)
        ├── mue/LAPTOP-XYZ789.json     ← 저 PC 만 쓴다
        └── _pcs.json                  ← PC 별명 (선택, 사람이 편집)
```

- 파일 이름 = `COMPUTERNAME`(환경 변수). 별명(`Office`, `Home`)은 `_pcs.json` 에서 화면 표시용으로만.
- `GitSync` 는 이미 `profiles/<data_folder>/` 만 스테이징 → 매니페스트도 같이 올라간다. 코드 변경 최소.
- `.gitignore` 의 `*.mb` 안전망은 그대로 — 매니페스트는 `.json` 이라 영향 없음.

### 4-1A. 추적 루트 여러 개 — Tracked Roots (사용자 추가 요청 2026-11-05)

`C:\JUN\JUN_MUE` 하나가 아니라 **사용자가 원하는 경로를 몇 개든 추적 루트로 등록**한다.

```
[Sync] > Tracked Roots
 ┌ Name ──────── Path (this PC) ─────────────────────────── Files ─ Last scan ─┐
 │ MUE           C:/JUN/JUN_MUE                              381    11-05 08:10 │
 │ Mocap         D:/Mocap/2026_MUE                           1204   11-05 08:11 │
 │ RigLib        (not set on this PC)  ⚠                     —      —           │
 └─────────────────────────────────────────────────────────────────────────────┘
 [Add Root...] [Set Path on This PC...] [Rename] [Remove]     Root: [MUE ▼]  ← Sync 표가 보여 줄 루트
```

- **루트 = 이름(id) + PC 마다의 실제 경로.** `C:\JUN\JUN_MUE` 는 정션 덕분에 모든 PC 에서 같은 경로지만,
  새로 고르는 경로는 PC 마다 다를 수 있다(`D:\Mocap` vs `E:\Mocap`). 그래서
  - 공유(`_sync_settings.json`): `roots: [{"id": "mocap", "name": "Mocap", "default_path": "D:/Mocap/2026_MUE", "excluded_paths": [...]}]`
  - PC 별(그 PC 의 A00210 prefs, 공유 안 함): `sync_root_paths: {"mocap": "E:/Mocap/2026_MUE"}` — 없으면 `default_path`.
  - 경로가 없는 PC 는 `(not set on this PC)` — 이 경우 그 PC 를 그 루트 비교에서 "참여 안 함" 으로 두고, `Missing` 을 쏟아내지 않는다.
- 파일 열쇠는 **루트 기준 상대 경로**. 비교는 같은 루트 id 끼리만 한다.
- **제외 경로(4-6)는 루트마다** 따로 가진다.
- 루트끼리 겹치면(한 루트가 다른 루트 안) 등록 시 경고하고, 안쪽 루트를 바깥 루트의 제외 경로로 자동 추가할지 묻는다(이중 추적 방지).
- 정션 · 심볼릭 링크를 루트로 골라도 된다(경로 그대로 따라감). 루트 **안의** 정션은 따라 들어가지 않는 것이 기본(무한 루프 · 이중 추적 방지), 루트별 옵션.

저장 위치는 루트마다 폴더 하나 — PC 매니페스트도 루트마다 따로(루트 하나 스캔이 다른 루트 파일을 건드리지 않음):

```
profiles/MUE/manifests/
    _sync_settings.json          (roots · 루트별 excluded_paths · ignore_patterns)
    _pcs.json
    mue/    DESKTOP-ABC123.json  LAPTOP-XYZ789.json
    mocap/  DESKTOP-ABC123.json  LAPTOP-XYZ789.json
```

> 첫 루트는 `mue` = `C:/JUN/JUN_MUE` 로 미리 등록해 둔다. 루트들은 지금 A00210 프로파일(MUE)에 속한다 —
> 다른 프로젝트 프로파일로 바꾸면 그 프로파일의 `manifests/` 를 쓴다.

### 4-2. 매니페스트 형식

```json
{
  "schema": 1,
  "pc": "DESKTOP-ABC123",
  "user": "Dnable_JunnyPark",
  "root_id": "mue",
  "root": "C:/JUN/JUN_MUE",
  "scanned_at": "2026-11-05 08:10:00",
  "files": {
    "00_04_02_ANI_00_PJ_010/scenes/5040_cleanup_BCM_KANA/00010_cleanup_KANA_00070.mb": {
      "size": 59729072,
      "mtime": "2026-11-05 07:54:00",
      "sha256": "9f2c…",
      "history": ["41ab…", "9f2c…"]
    }
  },
  "deleted": {
    "…/00010_cleanup_KANA_00065.mb": {"at": "2026-11-05 07:40:00", "sha256": "77de…"}
  }
}
```

- `history` = 이 PC 에서 이 경로가 가졌던 해시들(최근 N=10 개). **R3 충돌 판정의 근거**(4-4).
- `deleted` = 직전 매니페스트엔 있었는데 이번 스캔에 없는 파일(R7, 2차). 30일 뒤 정리.
- 정렬된 키 · 들여쓰기 고정 → git diff 가 "어떤 파일이 늘고 바뀌었는지" 로 그대로 읽힌다(그 자체로 이력).
- 크기: 파일 381개 기준 약 100 KB.

### 4-3. 스캔 — 빠르게, 정확하게

1. `os.scandir` 로 트리를 돈다(정션 아래는 실제 폴더라 그대로 따라감). 무시 규칙(4-6) 적용.
2. **크기 + 수정 시각이 직전 매니페스트와 같으면 해시를 다시 계산하지 않는다**(캐시). 바뀐 파일만 SHA-256.
   → 평소 스캔은 초 단위, 첫 스캔만 수 분.
3. 해시는 백그라운드 스레드 + 공용 progress 위젯. 마야가 **저장 중인 파일**(크기가 스캔 중 변함)은 건너뛰고 다음 스캔으로.
4. 시각은 로컬 시각 문자열 + UTC epoch 둘 다 저장(PC 시계 · 시간대 차이 대비, 비교는 해시가 1순위).

> ★ **지금 전송 경로인 구글 드라이브 웹 다운로드는 수정 시각을 보존하지 않는다** — 내려받은 파일의 시각 = 받은 시각,
> 여러 개를 받으면 zip 으로 묶여 와서 압축 해제 시각이 된다. 그래서 "받은 쪽이 더 새것" 처럼 보인다.
> **같음/다름 · 앞뒤의 판정은 반드시 해시 + history 로 하고, 시각은 표시용**으로만 쓴다.
> (탐색기 복사 · `robocopy` 는 시각을 보존하지만 그것도 해시로 확인한다.)

### 4-4. 비교 — 파일마다 상태 하나

모든 PC 매니페스트를 읽어 경로마다 PC 별 `(sha256, mtime, history)` 를 모은다. **이 PC 기준** 상태:

| 상태 | 조건 | 색 | 의미 / 할 일 |
|------|------|----|-------------|
| `OK` | 모든 PC 해시가 같다 | 회색 | — |
| `Missing` | 다른 PC 에 있고 이 PC 에 없다 (그쪽 `deleted` 도 아님) | 빨강 | **받아 와야 함** (R1) |
| `Outdated` | 이 PC 해시가 다른 PC 의 `history` 안에 있다 (= 그쪽이 내 버전 뒤에 또 고침) | 주황 | 받아 와야 함 (R2) |
| `Only here` | 이 PC 에만 있다 | 파랑 | 다른 PC 로 보내야 함 (R4) |
| `Ahead` | 다른 PC 해시가 **내** `history` 안에 있다 | 파랑 | 내 것이 최신, 보내야 함 |
| `Conflict` | 서로의 해시가 서로의 `history` 에 없다 (양쪽이 따로 고침) | 보라 | 사람이 판단 (R3) |
| `Deleted elsewhere` | 다른 PC `deleted` 에 있고 이 PC 엔 있다 | 노랑 | 지울지 결정 (R7, 2차) |

- **최신본 = 이력(history)으로 판정, 시각은 보조.** `history` 로 앞뒤를 알 수 없을 때(처음 만난 파일 등)만
  `mtime` 이 큰 쪽을 "아마 최신" 으로 표시하고 `?` 를 붙인다.
- 각 PC 매니페스트의 `scanned_at` 을 함께 보여 준다 — **"저 PC 는 3일째 스캔 안 함"** 이면 결과를 믿지 말라는 신호.
- 예시 시나리오:
  - 이 PC 가 `_00080.mb` 저장 → 스캔 → push.
  - 다른 PC 에서 A00210 열기(또는 `Refresh`) → pull → `_00080.mb` = **`Missing`** (요청한 동작 그대로).

### 4-5. 화면 — A00210 `Sync` 탭 (UI 문자열은 영어)

```
[Sync]
 PCs:  ● DESKTOP-ABC123 (this PC, scanned 08:10)   ● LAPTOP-XYZ789 (scanned 2 days ago ⚠)
 [Scan & Push]  [Pull & Compare]      Show: [x] Missing [x] Outdated [x] Conflict [ ] Only here [ ] OK
 ┌ Path ────────────────────────────────────────── This PC ─── LAPTOP ─── Status ─┐
 │ 00_04_02_ANI_00_PJ_010/scenes/5040_cleanup_BCM_KANA                             │
 │   00010_cleanup_KANA_00080.mb                    —          11-05 09:12  Missing │
 │   00010_cleanup_KANA_00070.mb                    11-05 07:54 11-04 18:00 Ahead   │
 └─────────────────────────────────────────────────────────────────────────────────┘
 Summary: Missing 1 · Outdated 0 · Conflict 0 · Only here 3
 [Copy Paths]  [Export Missing List...]  [Reveal in Explorer]
```

- **PC 수는 늘어난다(현재 2대)** → PC 열은 매니페스트 개수만큼 **동적으로** 만든다(고정 2열 금지).
  - PC 가 4대를 넘으면 기본 표시를 **요약 모드**로: `Path · This PC · Latest on · Missing on · Outdated on · Status`
    (예: `Latest on: OFFICE` · `Missing on: HOME, LAPTOP`). `PCs...` 버튼으로 보일 PC 열을 고른다(optionVar 대신 prefs 기억).
  - 비교는 "이 PC 기준" 이 기본이고, `Compare: [All PCs ▼]` 로 "어느 PC 에서든 어긋난 파일 전부" 를 볼 수도 있다.
- 트리는 공용 `MOD_fileTree_qt_v01` / 필터 위젯, 탭 높이는 `tabFit`, 확대는 `viewZoom` — 기존 Framework 재사용.
- 폴더 노드에 하위 상태 개수 뱃지(`5040_cleanup_BCM_KANA  ● 1 Missing`).
- 기존 File Manager 탭의 파일 목록에도 상태 아이콘을 작게 표시(2차).

### 4-6. 추적 범위 · 제외 경로 (사용자 결정 2)

**기본은 `C:\JUN\JUN_MUE` 아래 모든 파일 · 폴더를 추적하고, 사용자가 고른 경로는 그 하위 전부를 추적에서 뺀다.**

**(a) Excluded Paths — 사용자가 고르는 제외 경로**

```
[Sync] > Excluded Paths
 ┌───────────────────────────────────────────────┐
 │ 00_00_02_자료/                                │   ← 폴더 = 그 아래 모든 파일 · 하위 폴더 제외
 │ 99_00_01_Fin_movie/                           │
 │ 00_04_02_ANI_00_PJ_010/scenes/0010_test/      │
 │ 00_04_02_ANI_00_PJ_010/sound/bgm_tmp.wav      │   ← 파일 하나도 가능
 └───────────────────────────────────────────────┘
 [Add Folder...] [Add File...] [Remove]      (트리 우클릭: Exclude from Sync / Include Again)
```

- 저장: `profiles/MUE/manifests/_sync_settings.json` 의 **루트별** `excluded_paths` (루트 기준 상대 경로, `/` 구분, 폴더는 끝에 `/`).
  **모든 PC 가 같은 목록을 공유**한다 — 한 PC 에서 빼면 다른 PC 에서도 빠진다(pull 로 전달).
  PC 마다 따로 빼고 싶은 경우를 위해 `local_excluded_paths`(그 PC 의 prefs, 공유 안 함)도 둔다.
- 판정: 경로 `p` 는 목록의 폴더 `e/` 에 대해 `normcase(p).startswith(normcase(e))` 이면 제외(경계는 `/` 까지 포함해 비교 —
  `scenes/0010_test/` 가 `scenes/0010_test_02/` 를 빼지 않게).
- **스캔과 비교 둘 다에 적용한다.** 스캔은 제외 폴더 안으로 들어가지 않고(빠름), 비교는 다른 PC 의 옛 매니페스트에
  그 경로가 남아 있어도 걸러낸다 — 제외 목록을 고친 직후 다른 PC 가 다시 스캔하기 전에도 결과가 맞다.
- 제외를 풀면(`Include Again`) 다음 스캔부터 다시 추적. 그동안의 `history` 는 없으므로 앞뒤 판정은 시각 기준 `?` 로 시작한다.
- 화면: 제외된 폴더는 트리에서 회색 + `(excluded)` 로 보이고, `Show: [ ] Excluded` 로 숨길 수 있다.

**(b) 기본 무시 패턴 — 도구가 만드는 잡파일** (`_sync_settings.json` 의 `ignore_patterns`, glob), 기본값:

```
**/backup/**        (저장 툴 백업 — 53개, PC 마다 달라도 정상)
**/incrementalSave/**
**/.mayaSwatches/**  **/*.swatches
**/Thumbs.db  **/desktop.ini  **/~$*
```

`cache/` · `images/` 처럼 다시 만들 수 있는 결과물 폴더는 패턴이 아니라 (a) Excluded Paths 로 사용자가 직접 뺀다(기본은 추적).

### 4-7. 코어 / UI 분리 (CLAUDE.md 9장)

```
tools/A00210_FileManager/app/core/
    sync_manifest.py   # scan(root, ignore, prev) -> manifest dict · save/load · 해시 캐시   (UI · DCC 비의존)
    sync_compare.py    # compare(manifests, this_pc, excluded) -> [FileStatus]           (순수 함수, 시험 쉬움)
    sync_settings.py   # _sync_settings.json 읽기/쓰기 · is_excluded(rel, excluded)       (경계 매칭)
tools/A00210_FileManager/app/ui/
    sync_tab.py        # Sync 탭
```

`sync_compare` 는 순수 함수라 매니페스트 json 몇 개로 상태 표 전부를 단위 시험한다 —
가짜 PC **2대 · 3대 · 5대** 시나리오(늘어날 PC 대비), 제외 경로 경계(`0010_test/` vs `0010_test_02/`) · 제외 해제 포함.

---

## 5. 단계

| 단계 | 내용 | 산출 |
|------|------|------|
| **1차 (MVP)** | `sync_manifest` 스캔 + 해시 캐시 · `sync_compare` (OK/Missing/Outdated/Only here/Ahead/Conflict) · `Sync` 탭(PC 열 동적) · **Tracked Roots**(여러 루트 · PC 별 경로) · `Scan & Push` / `Pull & Compare` · **Excluded Paths**(공유 + 이 PC 만) · 무시 패턴 · 단위 시험 | A00210 v01.47 |
| 2차 | 지운 파일(`deleted`) · `Deleted elsewhere` · A00210 시작 시 자동 pull + 스캔, 요약 한 줄 알림 · File Manager 탭 상태 아이콘 · `_pcs.json` 별명 | v01.48 |
| 3차 (마야 연동) | 씬을 열 때 "이 파일보다 새 버전이 다른 PC 에 있다"(`_00080` 이 있는데 `_00070` 을 엶 · 같은 이름 Outdated) 경고 — 저장 툴(A00220) 저장 직후 해당 파일만 매니페스트 갱신 | A00220 / userSetup 훅 |
| 3차 (전송 보조 · 구글 드라이브 흐름) | 보내는 PC: `Only here` / `Ahead` 목록 → **`Collect for Upload`** = 상대 경로를 유지한 채 임시 폴더(또는 zip)에 모음 → 드라이브에 그 폴더째 올림. 받는 PC: 받은 zip/폴더를 **`Place Downloaded...`** 로 지정 → 해시로 매니페스트와 대조해 맞는 상대 경로에 넣고(시각도 원본 `mtime` 으로 복원) 다시 스캔. 손으로 경로를 찾아 넣는 실수 · 엉뚱한 버전 덮어쓰기를 막는다 | 선택 |
| 3차 후보 | Google Drive for desktop 이 깔린 PC 라면 드라이브 폴더(`G:\내 드라이브\…`)를 "전달함" 으로 지정해 업로드 대기 · 받을 파일을 자동 확인 | 검토 |
| 4차 (검토만) | 전송 자동화가 필요해지면 Syncthing(안 C) 또는 NAS/Perforce(안 E) 검토 — Sync 탭은 검증 도구로 유지 | 별도 계획서 |

---

## 6. 위험 · 주의

| 위험 | 대응 |
|------|------|
| 스캔을 안 하면 매니페스트가 낡는다 → 잘못된 "OK" | PC 별 `scanned_at` 를 항상 표시, 24h 넘으면 경고색. 2차에서 툴 시작 시 자동 스캔 |
| 마야 저장 중 파일을 해시 | 해시 전후 크기 · 시각 비교, 다르면 건너뜀 |
| PC 이름이 바뀌거나 OS 재설치 | 새 매니페스트가 생김 → `_pcs.json` 에서 옛 이름을 `retired` 로 표시해 비교에서 뺀다 |
| 같은 파일을 두 PC 에서 동시에 작업 | 감지(Conflict)만 한다. 잠금은 안 A 범위 밖 — 필요하면 "작업 중" 표시(records 에 `editing_by`)를 2차 후보로 |
| 매니페스트 git 충돌 | PC 당 파일 하나라 생기지 않음. `GitSync` 의 `pull --rebase --autostash` 그대로 |
| 비공개 데이터 노출 | 경로 이름만 올라간다(파일 내용 X). 저장소는 이미 Private(v01.45) |
| 상대 경로 대소문자 | Windows 라 `normcase` 로 비교 키를 만들고, 표시는 원래 이름 |

---

## 7. 결정 (2026-11-05 사용자 답)

| # | 질문 | 결정 | 반영 |
|---|------|------|------|
| 1 | 위치 | **A00210 의 탭** (`Sync`) | 4-5 · 4-7 |
| 2 | 추적 범위 | **`C:\JUN\JUN_MUE` 전체 추적 + 사용자가 고른 경로(하위 전부)는 제외하는 기능** | 4-6 (a) Excluded Paths |
| 3 | PC 수 | **현재 2대, 늘어날 계획** | 4-5 PC 열 동적 · 4대 넘으면 요약 모드, 시험 2·3·5대 |
| + | 추적 경로 (추가 요청) | **`C:\JUN\JUN_MUE` 외에도 원하는 경로를 마음대로 정해 추적** | 4-1A Tracked Roots (루트별 PC 경로 · 제외 경로) |
| 4 | 진행 | **계획서만, 구현은 보류** | 착수는 사용자가 따로 요청할 때 — 그때 1차(5장)부터 |
