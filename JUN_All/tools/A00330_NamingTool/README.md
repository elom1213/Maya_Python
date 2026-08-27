# A00330_NamingTool

레거시 `JUN_PY_NamingTool_V03_04.py`(maya.cmds UI)를 **PySide(PythonQt)** 로 이식한 네이밍 툴.
기존 2개 탭에 더해, `ref/ref_01.mel` 의 빠른 리네임 기능을 **3번째 탭**으로 추가했다.

> 프레임워크 컨벤션(A00310_SearchTool 등)과 동일한 패키지 구조 / dragDrop 설치 / `Framework.qt` 사용.

---

## 탭 구성

| 탭 | 출처 | 기능 |
|----|------|------|
| **Naming Dyn** | legacy Naming Dynamics | 오브젝트 + transform 자손을 `Token1_Token2_Token3_Index1_Index2` 로 일괄 리네임. Index1=루트 그룹마다 증가, Index2=그룹 내 항목마다 증가. pad 로 0 패딩. |
| **Copy Name** | legacy Copy name | Base 리스트의 leaf 이름(+Prefix)을 Targets 리스트에 순서대로 적용. 좌/우 리스트 각각 Sort 지원. **세트도 대상이 된다**(v01.03) — 세트는 같은 이름을 못 써서 `Set suffix`(기본 `_copy`)가 붙는다. `Add Sets` 로 세트를 담는다. 네임스페이스 보존. |
| **Quick Rename** | `ref/ref_01.mel` (이식) | **현재 선택** 기준. Front Insert(앞 삽입) / Change New(이름+인덱스, 10 미만 0 패딩) / Last Add(뒤 추가) / `-1 Front`·`-1 Rear`(앞·뒤 한 글자 제거) / All Apply(New→Insert→Add 순). |
| **Set Rename** | 신규 (v01.02) | **세트 이름**의 부분 문자열 찾아 바꾸기 + 미리보기 + `Add`/`Del`(v01.03). 마야 기본 `Search and Replace Names` 는 세트를 못 고른다 — `cmds.select(set)` 이 멤버를 펼쳐 선택하기 때문이다. 네임스페이스 보존 · 충돌/잘못된 문자 사전 표시. |

리스트 위젯(Select/Add/Del/Up/Down/Sort)은 공용 `Framework.qt.JUN_mod_tsl_qt_v01` 재사용.
모든 작업은 단일 Undo 로 묶인다(`core.undo_chunk`).

---

## 폴더 구조

```
A00330_NamingTool/
├── __init__.py                 # from .launch import run
├── __dragDrop_A00330.py        # Maya 뷰포트로 드래그&드롭 → 셸프 버튼 설치
├── launch.py                   # run() 진입점 (green_dark 테마)
├── README.md
├── icon/
│   ├── A00330_NamingTool.svg   # 벡터 아이콘
│   ├── A00330_NamingTool.png   # 셸프 아이콘 (64)
│   └── A00330_NamingTool_32.png
├── ref/
│   └── ref_01.mel              # Quick Rename 원본 (참고)
└── app/
    ├── config/version.py       # VERSION / LAST_UPDATE
    ├── core/naming_ops.py      # 네이밍 로직 (maya.cmds, thin UI 가 호출)
    ├── core/set_rename_ops.py  # 세트 이름 찾아 바꾸기 (v01.02)
    └── ui/main_window.py       # 4-탭 QWidget
```

---

## 설치 / 실행

1. **설치**: `__dragDrop_A00330.py` 를 Maya 뷰포트로 드래그&드롭 → 현재 셸프에 `NamingTool` 버튼 생성.
2. **실행**: 셸프 버튼 클릭. (내부적으로 `tools.A00330_NamingTool.run(True)`)
3. 스크립트로 직접 실행:
   ```python
   import sys; sys.path.append(r"<...>/JUN_All")
   import tools.A00330_NamingTool as nt
   nt.run(True)
   ```

요구: PySide2(Maya ~2024) 또는 PySide6(Maya 2025+). 둘 다 `Framework.qt.qt` 가 자동 분기.

---

## 레거시 대비 변경점

- `cmds` 기반 절차형 UI → PySide `QTabWidget` + 재사용 위젯으로 재작성.
- 로직을 `app/core/naming_ops.py` 의 순수 함수로 분리 (Maya 없이 단위 테스트 가능, 13/13 통과).
- 원본 `get_zero_with_length` 의 `is 0` (Python 3 경고) → `== 0` 으로 정정.
- 이름 처리 시 네임스페이스(`:`)까지 제거하여 rename 안정성 향상.
- 신규 **Quick Rename** 탭으로 MEL 기능 통합(별도 창 → 탭).

> 알려진 한계(원본과 동일): Naming Dyn 에서 동일 short name 자손이 여러 부모에 걸쳐 있으면
> 경로 모호성으로 rename 이 실패할 수 있다(레거시 동작 유지).
