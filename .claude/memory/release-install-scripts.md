---
name: release-install-scripts
description: Maya_Tool_Release 설치 스크립트의 두 함정 — userSetup 은 이름이 고정이고, git 출력은 UTF-8 인데 콘솔은 cp949
metadata:
  type: project
---

`Maya_Tool_Release/scripts/` 의 설치 스크립트에서 2026-09-22 에 고친 것들.
둘 다 **조용히 실패**해서 오래 안 드러났다.

## 1. `userSetup.py` 는 이름이 고정이다

**마야는 `userSetup.py` 라는 이름의 파일만 실행한다.** `userSetup_001.py` 는 아무도 안 읽는다.

옛 `setup_app_dir.py` 는 덮어쓰기를 피하려고 번호를 붙여 새 파일을 만들었다
→ **두 번째 설치부터 경로 등록이 전혀 안 되면서 "Install Complete" 라고 말했다.**
(이 PC 에도 죽은 `userSetup_001.py` 가 있었다.)

지금은 표식 블록만 갈아 끼운다 — 사용자 내용 보존 · idempotent · 경로를 옮기면 갱신.

```
# >>> JUN TOOLS >>>   ...   # <<< JUN TOOLS <<<
```

## 2. git 출력은 UTF-8, 한국어 Windows 콘솔은 cp949

`subprocess.run(..., text=True)` 는 **로케일**로 디코딩한다 → 커밋 제목에 한글이 있으면
`UnicodeDecodeError`. 게다가 그 예외는 **리더 스레드**에서 터져서 `run()` 은 조용히
`stdout=None` 을 돌려준다 — **진짜 실패해도 똑같이 조용하다.**

★ **읽기만 고치면 안 된다.** 콘솔도 cp949 라 `print` 에서 `UnicodeEncodeError`(예: em dash `—`)가
또 난다. 둘 다 고친다.

```python
for stream in (sys.stdout, sys.stderr):
    try:
        stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

subprocess.run(cmd, capture_output=True, encoding="utf-8", errors="replace")
```

★ **고친 `update.py` 는 다음 업데이트부터 듣는다** — `install.bat` 은 클론 안의 **옛** 스크립트로
업데이트를 돌리기 때문이다(`reset --hard` 가 미커밋 새 파일을 되돌리는 것으로 실측 확인).
그래서 **릴리즈 저장소 커밋 제목은 ASCII 로 쓴다**(본문은 한글 가능 — `reset` 출력엔 제목만 나온다).

관련: [[release-layout-launch-py]] · [[shelf-childarray-has-separators]] ·
`JUN_All/docs/Release_Layout.md` §6.
