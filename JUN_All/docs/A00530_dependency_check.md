# A00530_dependency_check — DepCheck (사용 안내)

이 인터프리터에서 **Qt 바인딩(PySide6 → PySide2) · pymel · maya.cmds · (선택) pyinstaller** 가 실제로
import 되는지 표로 보고하는 의존성 doctor 다. 옛 `dev/check_dependencies.py`(2026-06-16) 를 툴 폴더로 옮겼다.
무엇이 왜 필요한지는 [DEPENDENCIES](DEPENDENCIES.md).

- 버전: `v01.00` (`app/config/version.py`)
- 위치: `JUN_All/dev/A00530_dependency_check` — 개발 도구라 `dev/`
- 창이 없다. 표는 스크립트 에디터(print), 요약은 뷰포트 메시지.

## 1. 실행

- 마야 셸프: `__dragDrop_A00530.py` 를 뷰포트로 드롭 → `DepCheck` 버튼 (`run()`, standalone 항목은 건너뜀).
- 코드:

```python
import dev.A00530_dependency_check as chk
chk.run()                        # in-Maya 용
chk.run(check_standalone=True)   # pyinstaller 까지
```

- 터미널: `python dev/A00530_dependency_check/launch.py` (standalone 항목 포함, 누락이 있으면 exit 1).
- 옛 경로 `import dev.check_dependencies as chk; chk.run()` 도 **재노출**로 그대로 동작한다.

## 2. 구조

```
dev/A00530_dependency_check/
├── __init__.py · launch.py (run(check_standalone) -> bool) · __dragDrop_A00530.py
├── icon/A00530_dependency_check.svg|.png
└── app/
    ├── config/version.py
    └── core/dependency_check.py   # CHECKS 표 + run() (stdlib 만, 옛 파일 그대로)
```
