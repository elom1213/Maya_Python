---
title: A00080_KWI_creator_V03 사용법
aliases: [KWI Creator V03, Kawaii Creator V03]
tags: [tool, unreal, kawaii-physics, maya]
updated: 2026-06-25
---

# A00080_KWI_creator_V03 사용법

## 1. 개요

언리얼 **KawaiiPhysics** AnimGraph 노드를 **클립보드 붙여넣기용 텍스트**로 대량 생성하는 툴이다.
타겟 **루트 본 목록**을 입력하면 본 개수만큼 KawaiiPhysics 노드(+ 세팅/LD 노드)를 만들어
`0020_out/` 에 파일로 쓴다. 생성된 파일 내용을 복사해 언리얼 AnimGraph 에 붙여넣으면 노드가 만들어진다.

- **V02 → V03 차이점**:
  - V02 는 **standalone PySide 앱**(`launch.py` 의 `run()` 직접 호출, exe 빌드)이었다.
  - V03 는 **마야 내부 실행(PySide-in-Maya)** 으로, `__dragDrop_A00080.py` 를 드래그&드롭해
    셸프 버튼으로 설치/실행한다(`A00110_animTool` 과 동일한 (B) 아키텍처).
  - 타겟 본 목록을 **파일(`A0101_tgtBones.py`)이 아니라 UI 의 TSL(`QListWidget`)** 로 입력받는다.
    마야 씬에서 **선택한 노드를 바로 리스트에 담을 수 있다**(Add Selected).
  - **생성 로직(노드 텍스트 생성)은 V02 와 동일**하다.

---

## 2. 폴더 구조

```
A00080_KWI_creator_V03/
├── __init__.py                  # from .launch import run
├── launch.py                    # run(reload): 마야 메인윈도우에 parent → 테마 → show()
├── __dragDrop_A00080.py         # 셸프 버튼 설치 + 드래그&드롭 진입점
├── requirements.txt
├── CHANGELOG.md
├── icon/
│   ├── A00080_KWI_creator_V03.png   # 셸프 아이콘 (32x32)
│   └── A00080_KWI_creator_V03.svg   # 아이콘 원본
└── app/
    ├── config/version.py        # VERSION / LAST_UPDATE
    ├── core/                    # 로직 (UI 비의존, 텍스트 처리)
    │   ├── KWI_creator.py           # 노드 텍스트 생성 본체 (+ set_tgt_bones)
    │   ├── template_engine.py       # {{KEY}} 치환
    │   ├── tool_path.py / utility.py / file_processor.py
    │   └── 0010_src/            # 소스 템플릿 + A0101_tgtBones.py(예시 본 목록)
    └── ui/main_window.py        # PySide UI (메뉴바 Help + 본 TSL + 생성 버튼 + 로그)
```

- `core` 는 DCC 비의존 텍스트 처리만 한다. `Add Selected` 만 `maya.cmds` 를 lazy import 한다.
- 결과물은 `app/core/0020_out/` 에 쓰인다(`.gitignore` 대상).

---

## 3. 설치

`A00080_KWI_creator_V03/__dragDrop_A00080.py` 를 Maya 뷰포트로 **드래그&드롭** → 셸프에 버튼(`KWI_V03`) 생성.

---

## 4. 실행

- 셸프 버튼 클릭, 또는 Script Editor 에서:

```python
import tools.A00080_KWI_creator_V03 as A00080_KWI_creator_V03
A00080_KWI_creator_V03.run(True)   # True = reload
```

- 창은 마야 메인 윈도우에 parent 되어 뷰포트 위에 뜬다. 재실행 시 기존 창을 닫고 다시 연다.

---

## 5. UI 구성

```
┌ Help ──────────────────────────────────────────────────┐  ← 메뉴바 (Help > How to use)
│ Target bones (Root bones) : 3                          │  ← 라벨에 현재 본 개수 표시
│ ┌ TSL (QListWidget) ─────────────────────────────────┐ │
│ │  cv_spline_necklace_02_01                          │ │
│ │  cv_spline_necklace_03_01  ...                     │ │
│ └────────────────────────────────────────────────────┘ │
│ [ bone name 입력란..................... ] [ Add ]      │
│ [ Add Selected ][ Remove ][ Clear ][ Load Example ]    │
│ Create type                                           │
│  (•) Multiple Nodes   ( ) Single Node                 │
│ Setting nodes Number   [ 1 ]                          │
│ [ Create base nodes ]                                 │
│ [ Create setting nodes ]                              │
│ [ Create LD nodes ]                                   │
│ [v] Also write individual files                       │
│ [ Create combined file ]                              │
│ ┌ read-only 로그창 (영어 출력) ─────────────────────┐ │
│ └────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────┘
```

- **Help** (메뉴바): `Help > How to use` 로 툴 사용 안내 팝업(`QMessageBox`)을 띄운다.
- **Target bones (TSL)**: 노드를 만들 **루트 본 목록**. 위에서부터 노드 순서(체인)가 된다.
  라벨 헤더에 현재 본 개수가 함께 표시된다(예: `Target bones (Root bones) : 3`).
  - **입력란 + Add** / Enter: 타이핑한 본 이름을 리스트에 추가(중복 무시).
  - **Add Selected**: 마야 씬에서 **선택한 노드들**을 리스트에 추가.
  - **Remove**: 리스트에서 선택 항목 삭제. **Clear**: 전체 비우기.
  - **Load Example**: 번들 예시 목록(`A0101_tgtBones.py`)을 리스트에 로드.
- **Create type**:
  - **Multiple Nodes**(기본): 본마다 KawaiiPhysics 노드 1개를 만들어 **체인으로 연결**.
  - **Single Node**: 노드 1개만 만들고, **나머지 본은 Additional Root Bones** 로 합친다.
- **Setting nodes Number**: 세팅/LD 링크의 interval(정수).
- **Create base / setting / LD nodes**: 각 부분을 **개별 파일**로 생성.
- **Create combined file**: base + setting + LD 를 **하나의 파일**로 합쳐 생성.
  - 합본 코드가 **클립보드에 자동 복사**되어 언리얼 AnimGraph 에 바로 붙여넣을 수 있다(Ctrl+V).
    (합본만 복사되며, 개별 파일 내용은 복사되지 않는다.)
  - **Also write individual files**(기본 ON): 합본과 함께 개별 파일도 남긴다.
- **로그창**: 결과/경고 메시지(영어) 출력.

---

## 6. 사용 순서

1. **타겟 본 목록 구성** — `Add Selected`(씬 선택) 또는 입력란/`Add`, 필요 시 `Load Example`.
2. **Create type** 선택(Multiple / Single).
3. **Setting nodes Number** 입력.
4. 생성:
   - 개별: **Create base / setting / LD nodes**.
   - 합본: **Create combined file**(권장, 한 파일로 정리).
5. `0020_out/` 의 생성 파일을 열어 내용을 복사 → **언리얼 AnimGraph 에 붙여넣기**.

---

## 7. 동작 규칙

- **본 목록이 비어 있으면** 생성하지 않고 로그에 경고(`Target bones list is empty...`) 후 중단한다.
- 생성 직전 UI 의 TSL 목록을 `KWI_creator.set_tgt_bones(list)` 로 코어에 주입한다
  (V02 는 항상 `A0101_tgtBones.py` 를 읽었음).
- **Setting nodes Number** 가 정수가 아니면 `... must be integer` 경고 후 중단.
- **Multiple**: 본 i 의 노드를 `..._{i}` 로 만들고, 이전 노드(`..._{i-1}`)의 Pose 핀에 LinkedTo 연결.
  노드 위치는 4개마다 줄바꿈(`nodePos_lineChange`).
- **Single**: 첫 본을 RootBone, 나머지를 `AdditionalRootBones` 로 합친다.
- 텍스트 치환은 `TemplateEngine.apply` 의 `{{KEY}}` 단순 치환(`NODE_NAME`/`ROOT_BONE`/`LINKED_TO`/
  `NODE_POS_X`/`NODE_POS_Y` 등).

---

## 8. 로그 · 문제 해결

- `Target bones list is empty. Add bones first.` — TSL 에 본을 먼저 추가한다.
- `Setting nodes Number must be integer` — 숫자만 입력.
- `Nothing selected` / `maya.cmds not available (run inside Maya)` — `Add Selected` 는 마야 안에서,
  노드를 선택한 상태로 눌러야 한다.
- `Combined file created : <path>` — 생성 완료. 합본 코드는 클립보드에도 복사된다
  (`Copied combined code to clipboard...`). 언리얼 AnimGraph 에 Ctrl+V 로 붙여넣는다.
