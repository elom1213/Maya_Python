# 공용 로그창 전면 교체 계획 (`JUN_mod_log_qt_v01`)

- 작성: 2026-09-16
- 대상 위젯: `Framework/qt/MOD_log_qt_v01.py` 의 `JUN_mod_log_qt_v01`
- 위젯 문서: `docs/Framework_MOD_log_qt.md`
- 선행 사례: `A00470_MaterialTool` (v01.02 에서 이미 교체 완료 · 유일한 기존 사용처)

> [!done] **상태: 완료 (2026-09-16)** — 46곳 전부 교체했고 배치 5개로 나눠 커밋했다.
> 툴마다 `app/config/version.py` 와 `docs/<툴>.md` 를 함께 올렸고, `mayapy` 오프스크린
> 전수 스모크 테스트를 **46/47 통과**로 마쳤다(실패 1건은 이번 작업과 무관한 기존 결함 — 7.3 참고).
> **남은 것은 7.2 의 Maya GUI 육안 확인만이다.**

---

## 1. 목표

저장소의 모든 PySide 툴이 각자 `QTextEdit` / `QPlainTextEdit` 를 하나씩 놓고
"읽기 전용 + 높이 고정" 을 반복하던 로그창을, **Expand / Clear / Copy 버튼을 갖춘 공용
로그 위젯**으로 바꾼다.

교체로 툴이 얻는 것:

- **Expand** — 로그를 별도 창으로 옮겨 크게 본다(복제가 아니라 이동이라 동기화 문제가 없다).
- **Clear** — 로그를 비운다.
- **Copy** — 로그 전문을 클립보드로.

### 왜 드롭인 교체가 되는가

저장소 전체에서 로그 위젯에 실제로 부르는 메서드를 전수 집계한 결과는 **10종뿐**이다.

| 메서드 | 호출 수 | 새 위젯의 처리 |
|--------|--------:|----------------|
| `setReadOnly` | 46 | 내부 텍스트로 위임 (생성자가 이미 `read_only=True`) |
| `append` | 43 | `QTextEdit.append` 와 동일 — **HTML 해석** 유지 |
| `setMaximumHeight` | 23 | **내부 텍스트**에 적용 |
| `appendPlainText` | 17 | 커서로 평문 삽입(직접 구현) |
| `setMinimumHeight` | 13 | **내부 텍스트**에 적용 |
| `setFixedHeight` | 13 | **내부 텍스트**에 적용 |
| `clear` | 3 | Clear 버튼과 같은 동작 |
| `moveCursor` | 2 | `__getattr__` 위임 |
| `setLineWrapMode` | 1 | `__getattr__` 위임 |
| `setFont` | 1 | **내부 텍스트**에 적용 |

그리고 다음은 **저장소 어디에도 없다** — 교체를 깨뜨릴 만한 것이 없다는 뜻이다.

- 로그 위젯에 대한 `isinstance(..., QTextEdit)` / `findChild(QTextEdit)` **타입 검사 0건**
- 로그 위젯에 대한 `setStyleSheet` **0건**, `setSizePolicy` **0건**
- 테스트 코드에서 로그 위젯을 참조하는 곳 **0건**
- `log_view`(QPlainTextEdit 계열)에 `append()` 를 부르는 곳 **0건**

즉 교체는 툴당 **생성부 2~3줄**로 끝나고, 나머지 호출부는 한 글자도 건드리지 않는다.

---

## 2. 교체 대상 — 46곳

`tools/*/app/ui/main_window.py` 의 로그 위젯 46개. (`A00470` 은 완료되어 제외)

### 2.1 계열별 요약

| 계열 | 속성명 | 개수 |
|------|--------|-----:|
| QTextEdit | `te_log` | 26 |
| QPlainTextEdit | `log_view` | 13 |
| 혼재 | `log_widget` | 6 |
| QTextEdit | `txt_log` | 1 |

### 2.2 전체 표 (현재 높이 설정 = 교체 후 내부 텍스트에 그대로 적용)

| 툴 | 속성 | 현재 타입 | 높이 설정 | 배치 |
|----|------|-----------|-----------|:----:|
| **A00004_base_QT** | `log_widget` | QTextEdit | (없음/stretch) | 1 |
| **A00008_base_QT_maya** | `log_widget` | QTextEdit | (없음/stretch) | 1 |
| A00010_humanIKTool_V02 | `te_log` | QTextEdit | Max 120 | 5 |
| A00040_file_exporter_V02 | `log_view` | QPlainTextEdit | Fixed 120 | 5 |
| A00060_jointTool_V02 | `te_log` | QTextEdit | Max 120 | 4 |
| A00060_jointTool_V03 | `te_log` | QTextEdit | Max 120 | 3 |
| A00080_KWI_creator_V02 | `log_widget` | QTextEdit | (없음/stretch) | 5 |
| A00080_KWI_creator_V03 | `log_widget` | QTextEdit | (없음/stretch) | 4 |
| A00090_ConnectionBuilder | `te_log` | QTextEdit | (없음/stretch) | 4 |
| **A00110_animTool** | `te_log` | QTextEdit | Min 90 / Max 160 | 2 |
| **A00110_animTool_V02** | `te_log` | QTextEdit | Min 90 / Max 160 | 2 |
| A00120_FKIK | `te_log` | QTextEdit | Fixed 90 | 5 |
| A00130_ControlRig_V02 | `te_log` | QTextEdit | Min 140 | 4 |
| A00140_ConnectClosest | `log_view` | QPlainTextEdit | (없음/stretch) | 5 |
| **A00145_RigConnect** | `te_log` | QTextEdit | Max 120 | 2 |
| A00150_remapVal | `log_view` | QPlainTextEdit | Fixed 120 | 4 |
| A00160_sphericalEye | `log_view` | QPlainTextEdit | Fixed 120 | 5 |
| **A00170_driverTool** | `log_view` | QPlainTextEdit | Fixed 120 | 2 |
| A00180_abSymMesh | `log_view` | QPlainTextEdit | Fixed 90 | 5 |
| A00190_FKIK_General_Tool | `log_view` | QPlainTextEdit | Fixed 90 | 5 |
| A00210_FileManager | `log_widget` | QPlainTextEdit | Max 120 | 3 |
| A00211_RefLineage | `txt_log` | QTextEdit | Max 140 | 5 |
| A00220_BackupTool | `log_widget` | QPlainTextEdit | Max 140 | 5 |
| A00260_ConstraintConverter | `te_log` | QTextEdit | Min 90 / Max 160 | 5 |
| A00270_skinMigrate | `te_log` | QTextEdit | Min 90 / Max 160 | 5 |
| **A00275_skinTool_V01** | `te_log` | QTextEdit | Min 90 / Max 160 | 2 |
| A00280_correctiveFromCache | `te_log` | QTextEdit | Min 90 / Max 150 | 4 |
| A00290_BSTool | `te_log` | QTextEdit | Min 80 / Max 140 | 3 |
| A00300_meshDoctor | `te_log` | QTextEdit | Min 280 | 4 |
| A00310_SearchTool | `log_view` | QPlainTextEdit | Fixed 110 | 5 |
| A00330_NamingTool | `log_view` | QPlainTextEdit | Fixed 110 | 3 |
| A00340_SelectionTool | `log_view` | QPlainTextEdit | Fixed 90 | 5 |
| A00350_ArrayCreator | `te_log` | QTextEdit | Min 90 / Max 150 | 5 |
| A00360_SortTool | `te_log` | QTextEdit | Max 110 | 5 |
| A00370_ToolLauncher | `log_view` | QPlainTextEdit | Fixed 90 | 5 |
| A00380_MeshTool | `te_log` | QTextEdit | Max 110 | 4 |
| A00390_WindTool | `te_log` | QTextEdit | Max 120 | 5 |
| A00390_WindTool_V02 | `te_log` | QTextEdit | Max 120 | 4 |
| A00390_WindTool_V03 | `te_log` | QTextEdit | Max 120 | 4 |
| A00400_CurveTool | `te_log` | QTextEdit | Max 110 | 3 |
| A00410_SecondaryMotion | `te_log` | QTextEdit | Max 110 | 4 |
| A00420_Wrapper | `te_log` | QTextEdit | Min 110 | 3 |
| A00430_DemBone | `te_log` | QTextEdit | Min 130 | 4 |
| A00440_SetTool | `log_view` | QPlainTextEdit | Fixed 110 | 5 |
| A00450_manipulatorTool | `log_view` | QPlainTextEdit | Fixed 90 | 5 |
| A00460_ControllerTool | `te_log` | QTextEdit | Max 120 | 5 |

---

## 3. 교체 대상이 **아닌** 텍스트 위젯 — 8곳

같은 스캔에 걸리지만 **로그가 아니다.** 건드리지 않는다.

| 위치 | 이름 | 성격 | 제외 이유 |
|------|------|------|-----------|
| A00080_KWI_creator_V03 `main_window.py:260` | `constraint_preview` | 읽기 전용 미리보기 | 생성 결과 미리보기지 로그가 아님 |
| A00290_BSTool `main_window.py:1828` | `te_bd_report` | 읽기 전용 리포트 | Bake Delete 분석 리포트. 고정폭 폰트·`NoWrap`·placeholder 를 갖춘 독립 뷰 |
| A00210_FileManager `main_window.py:474` | `txt_log_history` | record 데이터 표시 | **이미 자체 Expand 버튼 보유**(`btn_expand_log`). 툴 실행 로그가 아니라 저장된 record 내용 |
| A00210_FileManager `main_window.py:479` | `txt_new_note` | **편집기** | 사용자가 입력하는 칸 |
| A00210_FileManager `main_window.py:1030` | `viewer` | 다이얼로그 뷰 | 지역 변수. 로그 히스토리 팝업 본문 |
| A00210_FileManager `lineage_tab.py:683` | `txt_node_logs` | record 데이터 표시 | 노드별 record 로그 표시용 |
| A00250_SceneMemo `main_window.py:93` | `editor` | **편집기** | 메모 작성 칸 |
| A00200_CSV_tool `arkit_facial_import.py:440` | `log_text` | 진짜 로그 | **보류** — 아래 참고 |

> **A00200_CSV_tool 보류 사유**: 이 툴만 `app/ui/main_window.py` 구조가 아닌 단일 파일이고,
> `from Framework.qt.qt import *` 가 아니라 `QtWidgets.` 접두사 스타일로 import 한다.
> 교체 자체는 가능하나 다른 45곳과 패턴이 달라 기계적 일괄 처리에 섞으면 사고가 난다.
> **배치 5 이후 개별 판단**으로 남긴다. 원하면 함께 처리한다.

---

## 4. 교체 규칙 (정확한 diff 모양)

### 4.1 import 추가

```python
from Framework.qt.MOD_log_qt_v01 import JUN_mod_log_qt_v01
```

`Framework/qt/__init__.py` 에 `JUN_mod_log_qt` 별칭이 이미 등록되어 있으나, 선행 사례
`A00470` 이 **직접 모듈 경로 import** 를 썼으므로 46곳 전부 그 형태로 통일한다.

> import 스타일은 두 가지가 섞여 있다 — `from Framework.qt.qt import *` (38곳),
> `from Framework.qt.qt import (...)` 명시 목록 (12곳). 어느 쪽이든 **새 import 는 별도
> 한 줄 추가**이므로 기존 import 목록은 손대지 않는다.

### 4.2 QPlainTextEdit 계열 (`log_view` 13곳)

```diff
-        self.log_view = QPlainTextEdit()
-        self.log_view.setReadOnly(True)
-        self.log_view.setFixedHeight(120)
+        self.log_view = JUN_mod_log_qt_v01(
+            window_title="Driver Tool - Log",
+            object_name="JUN_A00170_driverTool_log_window")
+        self.log_view.setFixedHeight(120)
```

- `setReadOnly(True)` 는 **삭제**한다(생성자 기본값이 읽기 전용).
- 높이 호출은 **그대로 남긴다** — 위젯이 내부 텍스트에 걸어 주므로 보이는 줄 수가 같다.

### 4.3 QTextEdit 계열 (`te_log` / `log_widget` / `txt_log` 33곳)

```diff
-        self.te_log = QTextEdit()
-        self.te_log.setReadOnly(True)
-        self.te_log.setMinimumHeight(90)
-        self.te_log.setMaximumHeight(160)
+        self.te_log = JUN_mod_log_qt_v01(
+            window_title="Anim Tool - Log",
+            object_name="JUN_A00110_animTool_log_window")
+        self.te_log.setMinimumHeight(90)
+        self.te_log.setMaximumHeight(160)
```

`append()` · `appendPlainText()` 등 **호출부는 전부 그대로 둔다.**

### 4.4 `object_name` 규칙 (★ 중요)

`object_name` 은 **툴마다 반드시 유일**해야 한다. 같으면 Expand 창이 서로를 찾아 닫는다.

```
JUN_<번호>_<툴이름>_log_window
```

**버전 병존 툴은 버전까지 이름에 넣는다.** 다음 4쌍은 V01/V02/V03 이 동시에 설치되어
동시에 떠 있을 수 있다 — 여기서 이름이 겹치면 실제로 사고가 난다.

- `A00060_jointTool_V02` / `_V03`
- `A00080_KWI_creator_V02` / `_V03`
- `A00110_animTool` / `_V02`
- `A00390_WindTool` / `_V02` / `_V03`

### 4.5 `window_title` 규칙

`"<툴 표시 이름> - Log"`. 각 툴의 `setWindowTitle` 에 쓰는 이름을 따른다.

---

## 5. ★ 예상되는 기능 문제 — 미리 알리는 사항

### 5.1 모든 툴의 창이 세로로 **약 22px 커진다** (영향: 46곳 전부)

높이 지정이 내부 텍스트에 걸리므로 **로그가 보이는 줄 수는 교체 전과 같고**, 대신 버튼
줄(20px + 간격 2px)만큼 창이 커진다. 설계상 의도된 동작이다.

- `setMaximumHeight` 계열(23곳)은 창에 여유가 있으면 대부분 흡수된다.
- `setFixedHeight` 계열(13곳)은 **확실히 +22px** 다. `self.resize(560, 720)` 처럼 초기
  크기가 고정된 툴에서는 그만큼 다른 요소가 눌리거나 스크롤이 생길 수 있다.
- **대응**: 교체 후 눈에 거슬리는 툴만 초기 `resize()` 높이를 +22 해 준다. 46곳을
  일괄로 올리지는 않는다(대부분 여유가 있어 불필요하게 창만 커진다).

### 5.2 A00300_meshDoctor — **Clear Log 버튼이 중복된다** (배치 5)

`main_window.py:138-141` 에 별도 `btn_clear_log` ("Clear Log") 가 있다. 공용 위젯이
Clear 를 이미 제공하므로 **그 버튼과 연결 코드를 삭제**한다. 남기면 같은 기능 버튼이
두 개 보인다.

### 5.3 색깔 로그 3툴 — `append()` 의 HTML 해석이 유지되어야 한다 (배치 5)

`A00300_meshDoctor` · `A00410_SecondaryMotion` · `A00430_DemBone` 이
`append('<span style="color:…">…')` 형태로 **색깔 로그**를 쓴다.

공용 위젯은 내부가 `QTextEdit` 이고 `append()` 가 HTML 해석을 그대로 유지하므로 **동작은
같다.** 다만 이 3툴은 교체 후 **색이 실제로 나오는지 눈으로 확인**한다. (내부를
`QPlainTextEdit` 로 만들었다면 태그가 글자 그대로 보였을 지점이다.)

### 5.4 A00300_meshDoctor — 폰트·줄바꿈 설정 (배치 5)

`setFont(QFont("Consolas", 9))` 과 `setLineWrapMode(QTextEdit.NoWrap)` 을 쓰는 유일한
로그다.

- `setFont` → 위젯이 명시적으로 내부 텍스트에 적용한다. OK.
- `setLineWrapMode` → `__getattr__` 로 내부 텍스트에 위임된다. OK.
- 단 `QTextEdit.NoWrap` 이라는 **클래스 상수 참조**가 남으므로 해당 파일의 `QTextEdit`
  import 를 지우면 안 된다. (다른 파일도 `QTextEdit` 을 계속 import 한 채로 둔다 —
  제거는 이 작업 범위 밖이다.)

### 5.5 Pin 툴 4개 — Expand 창과 항상-위 설정의 상호작용 (배치 4)

`A00110_animTool` · `A00110_animTool_V02` · `A00220_BackupTool` · `A00340_SelectionTool` ·
`A00370_ToolLauncher` 는 Pin(`WindowStaysOnTopHint`) 기능을 갖고 있다.

Expand 창은 툴 창을 부모로 하는 `Qt.Window` 다. **Pin 이 켜진 상태에서 Expand 창이 툴
창 뒤로 가는지**는 Maya GUI 에서 직접 확인해야 한다. 오프스크린 테스트로는 잡히지 않는
항목이다. 문제가 있으면 Expand 창에 부모의 항상-위 플래그를 물려주는 처리를 위젯에
추가한다(위젯 수정이므로 전 툴에 일괄 반영된다).

### 5.6 A00110 / A00220 — 창 높이 자동 계산 로직 (배치 4)

두 툴은 접이식 섹션 토글·탭 전환 시 `self.resize(self.width(), target_h)` 로 **창 높이를
스스로 계산**한다(`_fit_window_later`, 접힘/펼침 delta 계산).

계산은 섹션 본문 높이와 레이아웃 최소 크기에 기반하므로 로그창이 22px 커져도 자동으로
반영된다 — **이론상 문제없다.** 다만 이 로직은 `minimumSizeHint` 에 민감해 과거에도
clamp 문제를 겪은 자리이므로, 교체 후 **섹션 접기/펼치기와 탭 전환을 실제로 눌러 본다.**

### 5.7 A00040_file_exporter_V02 — 로그가 `QGroupBox("Log")` 안에 있다 (배치 2)

그룹박스 제목 바로 아래에 버튼 줄이 들어간다. 기능 문제는 없고 **시각 확인만** 하면 된다.

### 5.8 앞으로의 주의 — 컨테이너에 `setStyleSheet` 을 걸면 안 된다

교체 후 `self.te_log` 는 **컨테이너 위젯**이다. 여기에 `setStyleSheet` 을 걸면 내부
텍스트에 그대로 먹지 않는다(그리고 버튼 3개까지 함께 물든다). 현재 저장소에 그런 호출은
**0건**이라 이번 교체에는 영향이 없지만, 앞으로 로그 색을 바꾸려면 `log.text` 에 건다.

### 5.9 템플릿 교체의 파급 (배치 1)

`A00004_base_QT` / `A00008_base_QT_maya` 는 **새 툴의 복제 원본**이다. 여기를 바꾸면
이후 만드는 모든 툴이 공용 로그창을 기본으로 갖는다 — 이 작업의 실질적 이득이 가장 큰
지점이다. 새 툴 작성자가 `object_name` 만 바꾸면 되도록 템플릿에 주석을 남긴다.

---

## 6. 진행 순서 (배치 5개) — **이득 순**

작은 배치로 나누는 이유는 한 배치를 Maya 에서 확인한 뒤 다음으로 넘어가기 위해서다.
문제가 나면 그 배치만 되돌리면 된다.

### 6.1 순서를 정한 기준

배치는 **툴이 로그를 얼마나 쏟아내는지** 순으로 짠다. 교체의 실질 이득(Expand · Copy)은
로그를 많이 찍는 툴에 몰려 있고, 상태 한두 줄만 찍는 툴에서는 일관성 외에 실익이 거의
없기 때문이다. 이렇게 하면 **중간에 멈추거나 문제가 생겨도 이득의 대부분은 이미 얻은
상태**가 된다.

(균질한 것부터 하는 "위험도 순" 도 후보였지만, 그러면 이득이 가장 큰 `A00145` ·
`A00110` · `A00170` 이 뒤쪽 배치로 흩어진다.)

로그 호출 수는 각 툴 폴더 전체에서 `self.log(` / `self._log(` / `log_callback(` 을
집계한 값이다.

### 6.2 배치

★ 표시는 5장의 주의 항목이 걸린 툴이다.

| 배치 | 툴 (로그 호출 수) | 개수 |
|:----:|------------------|-----:|
| **1** 템플릿 | `A00004_base_QT`(2) · `A00008_base_QT_maya`(2) | 2 |
| **2** 최상위 이득 | `A00145_RigConnect`(135) · `A00110_animTool_V02`(133)★5.5★5.6 · `A00170_driverTool`(122) · `A00275_skinTool_V01`(96) · `A00110_animTool`(86)★5.5★5.6 | 5 |
| **3** 상위 이득 | `A00290_BSTool`(61) · `A00400_CurveTool`(59) · `A00210_FileManager`(58)★3장 · `A00420_Wrapper`(43) · `A00060_jointTool_V03`(37) · `A00330_NamingTool`(35) | 6 |
| **4** 중위 | `A00300_meshDoctor`(31)★5.2★5.3★5.4 · `A00130_ControlRig_V02`(29) · `A00430_DemBone`(26)★5.3 · `A00390_WindTool_V03`(26) · `A00410_SecondaryMotion`(22)★5.3 · `A00380_MeshTool`(22) · `A00060_jointTool_V02`(21) · `A00090_ConnectionBuilder`(20) · `A00080_KWI_creator_V03`(20) · `A00280_correctiveFromCache`(19) · `A00150_remapVal`(19) · `A00390_WindTool_V02`(17) | 12 |
| **5** 하위 (일관성) | `A00370_ToolLauncher`(16)★5.5 · `A00440_SetTool`(15) · `A00160_sphericalEye`(15) · `A00310_SearchTool`(14) · `A00120_FKIK`(14) · `A00260_ConstraintConverter`(13) · `A00340_SelectionTool`(12)★5.5 · `A00390_WindTool`(11) · `A00220_BackupTool`(10)★5.5★5.6 · `A00350_ArrayCreator`(9) · `A00190_FKIK_General_Tool`(8) · `A00460_ControllerTool`(7) · `A00211_RefLineage`(7) · `A00040_file_exporter_V02`(7)★5.7 · `A00360_SortTool`(5) · `A00140_ConnectClosest`(5) · `A00080_KWI_creator_V02`(5) · `A00010_humanIKTool_V02`(5) · `A00270_skinMigrate`(4) · `A00450_manipulatorTool`(3) · `A00180_abSymMesh`(3) | 21 |
| (보류) | `A00200_CSV_tool` | 1 |

합계 **47** (보류 1 포함).

템플릿이 여전히 맨 앞인 것은 이득이 커서가 아니라 **파급이 크기 때문**이다(이후 만드는
모든 툴이 여기서 복제된다). 단독으로 확인하고 넘어간다.

### 6.3 툴별 `window_title` / `object_name`

`object_name` 은 **툴 폴더명을 그대로** 넣어 유일성을 보장한다 — 폴더명이 이미 유일하므로
버전 병존 4쌍(`A00060` · `A00080` · `A00110` · `A00390`)도 자동으로 갈린다.

```python
object_name = "JUN_<폴더명>_log_window"      # 예: JUN_A00145_RigConnect_log_window
```

`window_title` 은 각 툴의 `win_title` / `setWindowTitle` 에 쓰는 이름에서 **버전 번호를
뺀 것** + `" - Log"` 다. 제목에 버전을 넣으면 툴을 올릴 때마다 로그 창 제목이 흔들린다.

버전 병존 4쌍은 `win_title` 이 서로 **같으므로**(예: V01·V02·V03 모두 `"Wind Tool"`)
제목에 버전을 넣어 사람이 구분할 수 있게 한다 — `"Wind Tool V02 - Log"`.

---

## 7. 검증

### 7.1 배치마다 — 오프스크린 스모크 테스트

`mayapy` + 오프스크린 Qt 로 그 배치의 `main_window` 를 **import 후 실제로 생성**해
다음을 확인한다. (`QApplication` 을 `maya.standalone.initialize()` 보다 먼저 만든다 —
알려진 순서 함정)

1. 생성 중 예외 없음
2. 로그 위젯이 `JUN_mod_log_qt_v01` 인스턴스
3. `object_name` 이 **전 툴에서 유일**함 (46개 전수 대조)
4. `append` / `appendPlainText` 가 들어간 글자를 그대로 담음
5. 내부 텍스트의 높이 제약이 교체 전 값과 **정확히 일치**
6. `expand()` → `collapse()` 왕복 후 텍스트가 원래 자리로 돌아옴

### 7.2 배치마다 — Maya GUI 육안 확인

버튼 3개의 **글자가 보이는지**를 테마별로 본다. (과거 `padding` 이 낮은 버튼의 글자를
전부 먹은 사고가 있었고, 버튼은 멀쩡히 보이므로 크기만으로는 알 수 없다. 오프스크린
`grab()` 픽셀 검사는 글자를 래스터화하지 않아 **판정에 쓸 수 없다** — 육안이 맞다.)

배치 4·5 는 위 5.3 · 5.5 · 5.6 항목을 각각 눌러 본다.

---

### 7.3 실제 결과 (2026-09-16)

오프스크린 스모크 테스트를 **배치별이 아니라 47툴 전수**로 돌렸다(교체가 이미 전부 들어가 있었다).
7.1 의 6항목을 툴마다 확인해 **46/47 통과**.

유일한 실패는 `A00008_base_QT_maya` 고, **이번 교체와 무관한 기존 결함**이다 — 존재하지 않는
`tools.A00001_base_maya` 를 import 한다. 2026-06-02 `86a8a45` (`Migrate : JUN_QT to JUN_ALL`) 부터의
상태로, 이 템플릿은 그때부터 Maya 안에서 import 되지 않는다. 로그창 교체 자체는 정상이므로
**별도 안건으로 남긴다**(이 작업에서 고치면 범위가 달라진다).

---

## 8. 문서 · 버전 갱신

- 툴마다 `app/config/version.py` 에 한 줄씩 올린다
  (예: `01.07  로그창을 공용 위젯 JUN_mod_log_qt_v01 로 교체 (Expand / Clear / Copy)`).
- `docs/<툴>.md` 에 로그창 버튼 3개를 짧게 적는다.
- `docs/Framework_MOD_log_qt.md` 의 "사용처" 를 갱신한다.
- `docs/WORKLOG.md` 에 배치 단위로 기록한다(최신이 위).
- 46개 툴의 버전·문서를 함께 올리므로 **커밋은 배치 단위**로 끊는다.

---

## 9. 되돌리기

배치 단위 커밋이므로 문제가 생긴 배치만 `git revert` 한다. 위젯 자체는 이미 `A00470` 이
쓰고 있으므로 **위젯을 되돌릴 일은 없다.**
