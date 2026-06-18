# A00230_StartupTool

Windows 부팅(로그인) 시 지정한 폴더들을 탐색기 창으로 자동 팝업한다.
열 폴더는 `config/folders.json` 으로 관리하며, 경로에 환경변수(`%USERPROFILE%` 등)를 쓰므로
**PC 가 바뀌어도 동일하게** 동작한다.

## 구성

```
A00230_StartupTool/
├── open_folders.py     # 본체: folders.json 읽어 폴더 팝업 (단독 실행 가능)
├── config/folders.json # 팝업할 폴더 목록 (편집 지점)
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
다음 로그인부터 콘솔창 없이 폴더들이 자동으로 뜬다.

### 2. 폴더 추가 / 수정
`config/folders.json` 편집:
```json
{
  "open_missing": false,
  "folders": [
    { "path": "%USERPROFILE%\\Desktop", "enabled": true },
    { "path": "D:\\Work\\Project", "enabled": false }
  ]
}
```
- `path` — 환경변수(`%VAR%`)와 `~` 확장 지원.
- `enabled` — `false` 면 건너뜀 (목록은 유지).
- `open_missing` — `false`(기본): 존재하지 않는 경로는 조용히 skip.

설치를 다시 할 필요 없이, JSON 만 바꾸면 다음 부팅에 반영된다.
줄 전체를 `//` 로 시작하면 주석 처리되어 그 항목을 임시로 끌 수 있다(엔트리 삭제 없이).

### 3. 테스트 (설치 없이 즉시 실행)
```
python open_folders.py
```

### 4. 제거
```
python uninstall.py
```

## 다른 PC 로 이전
1. repo 를 git pull (이 폴더가 동기화됨).
2. 새 PC 에서 `python install.py` 한 번 실행.

경로는 환경변수로 풀리고, 런처는 그 PC 의 절대경로로 재생성되므로 추가 수정이 필요 없다.
