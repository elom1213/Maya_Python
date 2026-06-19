# A00230_StartupTool

Windows 부팅(로그인) 시 지정한 **폴더들을 탐색기 창으로 팝업**하고, 지정한 **standalone 툴들을
자동으로 실행(팝업)**한다. 대상은 `config/startup.json` 으로 관리하며, 경로에 환경변수
(`%USERPROFILE%` 등)와 repo 상대 위치를 쓰므로 **PC 가 바뀌어도 동일하게** 동작한다.

## 구성

```
A00230_StartupTool/
├── startup.py          # 부팅 진입점: startup.json 읽어 폴더 팝업 + 툴 실행 (단독 실행 가능)
├── open_folders.py     # 폴더 로직 (startup.py 가 재사용 / 폴더만 단독 테스트 가능)
├── config/startup.json # 팝업할 폴더 + 실행할 툴 목록 (편집 지점)
├── install.py          # Startup 폴더에 런처 등록 (PC별 1회)
├── uninstall.py        # 런처 제거
└── README.md
```

## 사용법

### 1. 설치 (PC 별 1회)
```
python install.py
```
→ `%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\A00230_StartupTool.vbs` 생성.
다음 로그인부터 콘솔창 없이 폴더 + 툴이 자동으로 뜬다.
런처는 `pythonw` 로 `startup.py` 를 호출한다.

> **기존 사용자**: 이전엔 런처가 `open_folders.py`(폴더만)를 가리켰다. 툴 자동 실행까지
> 적용하려면 `python install.py` 를 **1회 재실행**해 런처를 `startup.py` 로 갱신한다.

### 2. 폴더 / 툴 추가·수정
`config/startup.json` 편집:
```json
{
  "open_missing": false,
  "folders": [
    { "path": "%USERPROFILE%\\Desktop", "enabled": true },
    { "path": "D:\\Work\\Project", "enabled": false }
  ],
  "tools": [
    { "tool": "A00210_FileManager", "enabled": true },
    { "tool": "A00220_BackupTool", "enabled": true },
    { "tool": "A00240_PathTool", "enabled": true }
  ]
}
```

**폴더 (`folders`)**
- `path` — 환경변수(`%VAR%`)와 `~` 확장 지원.
- `enabled` — `false` 면 건너뜀 (목록은 유지).
- `open_missing` — `false`(기본): 존재하지 않는 경로는 조용히 skip.

**툴 (`tools`) — 새 툴은 여기에 한 줄만 추가하면 됨**
- `tool` — `JUN_All/tools/<이름>/launch.py` 로 해석. **폴더명만** 적으면 된다.
  예) 새 툴 추가: `{ "tool": "A00250_MyTool", "enabled": true }`
- `launch` — (선택) 표준 위치 밖의 툴은 launch.py 절대경로/환경변수 경로를 직접 지정.
  예) `{ "launch": "%USERPROFILE%\\tools\\my\\launch.py", "enabled": true }`
- `enabled` — `false` 면 건너뜀.
- 각 툴은 **별도 프로세스**(`pythonw launch.py`)로 떠서 서로 영향이 없다.
  PySide(Qt) 가 설치된 파이썬에서 동작한다.

설치를 다시 할 필요 없이, JSON 만 바꾸면 다음 부팅에 반영된다.
줄 전체를 `//` 로 시작하면 주석 처리되어 그 항목을 임시로 끌 수 있다(엔트리 삭제 없이).

### 3. 테스트 (설치 없이 즉시 실행)
```
python startup.py        # 폴더 + 툴 모두 실행
python open_folders.py   # 폴더만 실행
```

### 4. 제거
```
python uninstall.py
```

## 다른 PC 로 이전
1. repo 를 git pull (이 폴더가 동기화됨).
2. 새 PC 에서 `python install.py` 한 번 실행.

폴더 경로는 환경변수로, 툴 경로는 repo 상대 위치로 풀리고, 런처는 그 PC 의 절대경로로
재생성되므로 추가 수정이 필요 없다.
