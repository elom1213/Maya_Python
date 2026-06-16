# JUN_All 외부 의존성 가이드

JUN_All의 모든 툴을 쓴다고 가정했을 때 필요한 외부 코드와 그 관리 방법을 정리한다.

핵심: 이 프로젝트의 의존성은 **두 실행 맥락**으로 갈린다.

| 맥락 | 의존성 출처 | pip 설치 |
|------|-------------|----------|
| **Maya 안에서 실행** (in-DCC 툴) | PySide·pymel·maya.cmds 모두 **Maya가 제공** | 불필요 |
| **standalone / .exe 빌드** | venv에 직접 설치 | 필요 (`PySide6`, `pyinstaller`) |

> 그래서 "외부 코드 목록"을 단순 텍스트로 두는 것보다, **설치 가능한 매니페스트**(루트
> `requirements.txt`)와 **import 가능 여부를 검증하는 doctor 스크립트**(`dev/check_dependencies.py`)로
> 나누는 편이 실제 쓸모가 있다.

---

## 1. 단일 진실 소스

- **`JUN_All/requirements.txt`** — standalone/빌드 맥락의 pip 의존성. 설치:
  ```
  pip install -r JUN_All/requirements.txt
  ```
  현재 내용: `PySide6`, `pyinstaller`.
- 각 툴 폴더의 `requirements.txt`는 릴리스 자기완결성을 위해 유지하되, 위 루트 파일을 단일
  진실 소스로 참조한다(상단 주석).

## 2. 전체 의존성 표

| 패키지 | 출처 | pip 대상 | 사용처 |
|--------|------|----------|--------|
| **PySide6** | standalone venv / Maya 2025+ 내장 | ✅ (standalone) | 모든 Qt 툴 (Framework.qt.qt 우선) |
| **PySide2** | Maya 2022~2024 내장 | ❌ (Maya 제공) | qt.py 폴백 (모든 Qt 툴이 래퍼 경유, 직접 import 없음) |
| **pymel** | Maya 내장 | ❌ (Maya 제공) | A00150, A00160, A00170, A00190 |
| **maya.cmds / maya.mel / maya.api** | Maya 내장 | ❌ | in-DCC 툴 공통 |
| **pyinstaller** | standalone venv | ✅ (빌드 시) | A00004/08/80/90 (.exe 빌드) |

그 외(numpy·scipy·requests 등) 외부 의존성은 **없다**.

## 3. Maya 버전 → Python / Qt 바인딩 (대략)

| Maya | Python | Qt 바인딩 |
|------|--------|-----------|
| 2022 | 3.7 | PySide2 |
| 2023 | 3.9 | PySide2 |
| 2024 | 3.10/3.11 | PySide2 |
| 2025+ | 3.11 | PySide6 |

정확한 값은 환경마다 다를 수 있으므로, **`dev/check_dependencies.py`가 런타임에 실제로 잡힌
바인딩을 출력**한다. 위 표는 안내용이다.

`Framework/qt/qt.py`가 PySide6를 먼저, 실패 시 PySide2를 import 하는 폴백을 제공하므로,
**툴 코드는 `from Framework.qt.qt import ...`를 쓰면 버전 차이를 신경 쓰지 않아도 된다.**
모든 Qt 툴이 이 래퍼를 경유한다(PySide 직접 import 없음). 마이그레이션 경과는
`docs/plans/qt_wrapper_migration_plan.md` 참고.

## 4. 검증 / 설치 절차

**standalone (exe 빌드/개발)**
```
python -m venv .venv && .venv\Scripts\activate
pip install -r JUN_All/requirements.txt
```

**in-Maya (스크립트 에디터에서)**
```python
import dev.check_dependencies as chk
chk.run()                       # in-DCC 툴 의존성만
chk.run(check_standalone=True)  # pyinstaller 등 standalone 항목까지
```
출력으로 Python·Maya 버전, 잡힌 Qt 바인딩(PySide6/2), pymel·maya.cmds import 결과와
누락 항목을 표로 확인한다.

## 5. in-Maya 전용 툴 (pip 의존성 없음)

다음 툴은 Maya 안에서만 동작하며 별도 pip 설치가 필요 없다(모든 의존성을 Maya가 제공):
A00000~A00060(maya.cmds), A00100_jsonEditor_MH(stdlib), 그리고 Framework.qt.qt를 쓰는
A00110~A00190 계열(Qt·pymel은 Maya 제공).
