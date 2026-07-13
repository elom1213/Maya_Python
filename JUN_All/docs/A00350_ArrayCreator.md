---
title: A00350_ArrayCreator 사용법
aliases: [Array Creator, ArrayCreator, A00350]
tags: [maya-python, tool-guide, unreal, control-rig, text-generator]
updated: 2026-07-13
---

# A00350_ArrayCreator 사용법

Maya 안에서 도는 **텍스트 생성** PySide 툴이다(arch B, in-Maya). TSL 에 리스트업한 오브젝트들을
그 순서대로 **언리얼 Control Rig 의 Item Array 노드**(`TArray<FRigElementKey>`) 텍스트로 만들어
**클립보드에 복사**(UE 그래프에 Ctrl+V) + `0020_out/` 에 파일로 저장한다. 마야가 아니라 **텍스트 처리 툴**이다
(A00080_KWI_creator 계열).

- **버전**: `app/config/version.py` (v01.01)
- **설치**: `__dragDrop_A00350.py` 를 Maya 뷰포트로 드래그&드롭 → 셸프 버튼 **ArrayCreator** → `tools.A00350_ArrayCreator.run(True)`
- **참고 아키텍처**: A00080_KWI_creator_V03 · A00260_ConstraintConverter (PathManager `0010_src`→`0020_out` + TemplateEngine `{{KEY}}` + NodeBuilder 조립 + 클립보드).

---

## 1. 사용법

1. Maya에서 오브젝트(조인트 등)를 선택 → **Select Objects**(리스트 교체) 또는 **Add**(중복 없이 추가)로
   **Objects** 리스트에 담는다. 순서가 곧 배열 요소 순서다(**Up/Down** 으로 조정, **Del** 로 제거).
   - **Reverse**(v01.01~): 리스트에 올라온 순서를 **한 번에 통째로 뒤집는다**. 선택한 순서와 배열에
     넣을 순서가 반대일 때(예: 체인을 끝→루트로 골랐을 때) 유용하다. (공용 TSL 위젯의 옵션 버튼)
   - 요소 이름은 오브젝트의 **leaf 이름**을 쓴다(DAG 경로 `|...` 는 제거).
2. **Element Type**: 배열 요소의 `ERigElementType` 을 고른다 — None / Bone / Null / Control / Curve /
   Reference / Connector / Socket. **기본 Bone**. (모든 요소에 공통 적용)
3. **Node Title**: UE 그래프에 붙여넣었을 때 노드에 보일 이름(기본 `Test_array`).
4. **Create Array Node → Copy to Clipboard**:
   - 리스트 순서대로 Item Array 노드 텍스트를 생성.
   - **클립보드에 복사** → UE Control Rig 그래프에서 **Ctrl+V** 로 바로 붙여넣기.
   - `app/core/0020_out/A001_array_node_out.py` 로도 저장.

> **붙여넣기 시 경로**: 생성 텍스트의 asset/노드 경로는 템플릿(v01) 값을 그대로 쓴다. UE 는 붙여넣을 때
> 이 경로를 **현재 그래프로 다시 매핑**하므로 값 자체는 중요하지 않다(노드 이름만 있으면 된다).

---

## 2. 생성되는 노드 구조

Item Array 노드는 `RigVMDispatchNode`(`DISPATCH_RigVMDispatch_Constant`, `TArray<FRigElementKey>`)로,
요소마다 **Type**(ERigElementType)과 **Name**(FName) 두 서브핀을 가진다. 텍스트는 두 부분이 요소 수만큼 반복된다:

- **선언부**(declaration): 각 요소의 핀 계층을 `Begin/End Object ... RigVMPin` 으로 선언(stub).
- **정의부**(definition): 각 요소의 실제 값 — `Type.DefaultValue`(선택한 타입), `Name.DefaultValue`(오브젝트 이름).
- 마지막에 배열 핀의 `SubPins(0..N-1)` 목록.

리스트에 `dyn_pants_chain_r_01_02 …` 6개를 담고 타입 Bone / 제목 Test_array 로 생성하면 참고 파일
`app/core/0010_src/A0010_Src_Array_node_v01.py` 와 **바이트 단위로 동일한** 텍스트가 나온다(검증됨).

---

## 3. 구조

```
tools/A00350_ArrayCreator/
├── launch.py / __init__.py / __dragDrop_A00350.py
├── icon/A00350_ArrayCreator.svg (+ .png)     # 셸프 아이콘(배열 [ ] 브래킷 + 요소 행)
└── app/
    ├── config/version.py
    ├── core/
    │   ├── 0010_src/
    │   │   ├── A0001_Src_array_node.py        # 전체 노드 템플릿({{NODE}}/{{ASSET}}/{{NODE_TITLE}}/{{POS_*}}/{{VALUE_DECL}}/{{VALUE_DEF}}/{{SUBPINS}})
    │   │   ├── A0002_Src_element_decl.py      # 요소 선언 조각({{IDX}})
    │   │   ├── A0003_Src_element_def.py       # 요소 정의 조각({{IDX}}/{{TYPE}}/{{NAME}})
    │   │   └── A0010_Src_Array_node_v01/v02.py# 참고 예시(v01=정식 구조, v02=타입 카탈로그)
    │   ├── 0020_out/                          # 생성 결과(.gitignore)
    │   ├── template_engine.py                 # {{KEY}} 치환
    │   ├── tool_path.py                       # 읽기/쓰기 경로 dataclass
    │   ├── node_builder.py                    # decl/def/SubPins 를 요소 수만큼 조립 + ELEMENT_TYPES/기본값
    │   └── array_creator.py                   # 오케스트레이터(PathManager 0010_src→0020_out, 파일 저장)
    └── ui/main_window.py                      # PySide UI (TSL + Type 콤보 + Node Title + 생성/클립보드)
```

- 핵심 API: `array_creator.ArrayCreator().create(names, ArrayOptions(...))` → `(text, element_names, out_path)`.
- 요소별로 바뀌는 것은 Type/Name 의 `DefaultValue` 뿐이라, 조각 템플릿을 반복 조립한다(A00260 NodeBuilder 패턴).
- 참고: v02 는 한 노드에 여러 타입이 아니라 **타입별 단일요소 노드 8개**를 이어붙인 카탈로그다. 현재 툴은
  **모든 요소 공통 타입**(Type 콤보)으로 동작한다.
