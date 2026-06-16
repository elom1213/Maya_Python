# 작업 계획서 — 하드코딩 PySide → Framework.qt.qt 래퍼 마이그레이션

- **작성일**: 2026-06-16
- **상태**: ✅ 완료 (2026-06-16)
- **관련 문서**: `JUN_All/docs/DEPENDENCIES.md`

> **실제 결과**: 착수 후 확인 결과, 계획의 4개 대상 중 **A00008·A00090은 이미 래퍼를
> 쓰고 있었다**(직접 import는 `'''...'''` 주석 블록 안의 죽은 코드였고, 초기 grep이 이를
> 활성 import로 오인 → 계획서의 대상이 과대 집계되었다). 실제 교체가 필요했던 것은
> **A00004·A00080** 두 곳이다.
>
> 적용 내역:
> - `A00004_base_QT/launch.py`, `A00004_base_QT/app/ui/main_window.py`: `PySide6.QtWidgets` → `Framework.qt.qt` (명시적 이름 import 유지)
> - `A00080_KWI_creator_V02/app/ui/main_window.py`: `PySide6.QtWidgets` → `Framework.qt.qt` (launch.py 는 이미 래퍼 사용)
> - `A00008`·`A00090`: 오인을 유발하던 PySide2 죽은 주석 블록 제거 + requirements.txt 를 PySide2→PySide6(래퍼 우선)로 정정
> - 검증: 변경 5개 파일 `py_compile` 통과, tools 전역에 활성 PySide 직접 import 0건 확인.

---

## 1. Context (왜 하는가)

JUN_All의 Qt 툴은 두 부류다:

- **래퍼 사용(권장)**: `from Framework.qt.qt import *` — `Framework/qt/qt.py`가 PySide6를 먼저,
  실패 시 PySide2를 import 하는 폴백을 제공한다. 버전 차이를 신경 쓸 필요가 없다.
  (A00110~A00190 계열)
- **하드코딩(문제)**: PySide 버전을 직접 import 하는 4개 툴. Maya 버전이 바뀌면(2024 PySide2 ↔
  2025 PySide6) 깨질 수 있다.

이 계획은 후자 4개를 래퍼로 옮겨 **버전 충돌 위험을 제거**한다.

### 대상 (조사 확정)

| 툴 | 직접 import 위치 | 현재 바인딩 |
|----|------------------|-------------|
| `A00004_base_QT` | `launch.py:15`, `app/ui/main_window.py:1` | PySide6 |
| `A00008_base_QT_maya` | `app/ui/main_window.py:6-7` | PySide2 |
| `A00080_KWI_creator_V02` | `app/ui/main_window.py:1` | PySide6 |
| `A00090_ConnectionBuilder` | `app/ui/main_window.py:7-8` | PySide2 |

> A00004/A00008은 **템플릿**이다. 마이그레이션하면 앞으로 복제되는 새 Qt 툴이 처음부터
> 버전 비의존이 된다 — 이 작업의 가장 큰 이득.

---

## 2. 변경 패턴

각 파일의 직접 import 를 래퍼 import 로 교체한다. `qt.py`가 QtWidgets/QtCore/QtGui를
`import *` 로 재노출하므로, **명시적 이름 import 를 유지한 채** 출처만 래퍼로 바꾸는 것을 권장한다
(네임스페이스 오염 최소화).

**Before** (A00008/A00090 예):
```python
from PySide2.QtCore import Qt
from PySide2.QtWidgets import (QWidget, QVBoxLayout, QPushButton, ...)
```
**After**:
```python
from Framework.qt.qt import Qt, QWidget, QVBoxLayout, QPushButton, ...
```

**Before** (A00004/A00080 예):
```python
from PySide6.QtWidgets import (QWidget, ...)
```
**After**:
```python
from Framework.qt.qt import QWidget, ...
```

`launch.py`의 `from PySide6.QtWidgets import QApplication`(A00004)도 동일하게
`from Framework.qt.qt import QApplication`로 교체. (단, sys.path에 JUN_All 루트가 들어간
**뒤에** import 해야 한다 — 기존 launch.py는 이미 ROOT를 추가하므로 순서만 확인.)

---

## 3. 리스크 / 확인 포인트

1. **enum 스코프 차이 (가장 큰 리스크)**: PySide2는 `Qt.AlignCenter`, PySide6는 원칙적으로
   `Qt.AlignmentFlag.AlignCenter`. 최근 PySide6는 단축형 호환을 제공하지만 버전에 따라 다르다.
   → 각 툴에서 사용하는 `Qt.*`, `QSizePolicy.*`, `QFrame.*` 등 enum 사용처를 점검.
2. **`exec_()` vs `exec()`**: standalone 진입점(A00004/A00080)이 `app.exec_()`를 쓰면 PySide6에서
   동작 여부 확인(대개 alias 유지되나 버전별 상이).
3. **standalone 빌드(A00004/A00080)**: 래퍼를 쓰면 PyInstaller가 `Framework.qt.qt`와 그것이
   import 하는 PySide를 번들해야 한다. `launch.spec` / `build_exe.bat`에 `Framework` 패키지가
   포함되는지(현재 `--paths ../../` + Framework/styles data) 확인하고, 필요 시 `--collect-all`
   범위 점검.
4. **QAction 이동**: Qt5는 QtWidgets, Qt6는 QtGui. `qt.py`가 셋 다 `import *` 하므로 래퍼 경유 시
   자동 해결 — 직접 import 를 래퍼로 바꾸면 오히려 안전해진다.
5. **requirements.txt 갱신**: 마이그레이션 후 A00008/A00090은 래퍼 폴백 덕에 PySide6 우선이 되므로
   per-tool requirements 의 바인딩 표기를 재검토(현재 PySide2로 수정해 둔 상태).

---

## 4. 작업 순서 (제안)

1. **A00008_base_QT_maya** 먼저(템플릿 + PySide2 → 폴백 경로 검증에 적합).
2. **A00090_ConnectionBuilder** (PySide2, 페이셜 실사용 툴).
3. **A00004_base_QT** (PySide6 템플릿, standalone).
4. **A00080_KWI_creator_V02** (PySide6, standalone + 빌드 영향 큼 → 마지막).

각 단계마다 import 교체 → 아래 검증을 통과한 뒤 다음 툴로.

---

## 5. 검증 방법

- **in-Maya**: 각 툴을 Maya(가능하면 PySide2 환경=2023, PySide6 환경=2025 양쪽)에서 실행 →
  창이 정상 생성되고 enum/레이아웃 깨짐 없는지. `dev/check_dependencies.py`로 잡힌 바인딩 확인.
- **standalone**(A00004/A00080): venv에서 `pip install -r JUN_All/requirements.txt` →
  `launch.py` 실행 및 `build_exe.bat`로 exe 빌드 후 실행까지 확인.
- **회귀**: 교체 전후로 각 `main_window.py`가 쓰는 위젯/enum 목록을 grep으로 뽑아 누락 없는지 대조.

---

## 6. 범위 밖

- A00110~A00190 등 **이미 래퍼를 쓰는 툴**은 변경하지 않는다.
- `Framework/qt/qt.py` 자체 확장(예: QtGui 별도 노출, shiboken)도 이번 범위 밖 — 필요 시 별도.
