# A00260_ConstraintConverter

마야 씬의 **컨스트레인트 세팅**을 언리얼 **Control Rig** 의 **Parent Constraint** 노드 텍스트로 변환해
**클립보드에 복사**하는 PySide 툴. 언리얼 Control Rig 그래프에 그대로 `Ctrl+V` 붙여넣으면 노드가 생성된다.

- **아키텍처**: (B) Standalone/Qt — PySide, Maya 내 실행 (`A00110_animTool` 클론)
- **버전**: `app/config/version.py` (v01.00)
- **설치**: `__dragDrop_A00260.py` 를 Maya 뷰포트로 드래그&드롭 → 셸프 버튼(`CnsConv`) 생성 → `tools.A00260_ConstraintConverter.run(True)`
- **참고 출력 포맷**: `ref_/smaple.py` (UE Control Rig 에서 Parent Constraint 노드를 복사한 원본 텍스트)

---

## 무엇을 하나

마야 컨스트레인트(`parentConstraint` 등)에서 다음을 읽어 UE Parent Constraint 노드로 옮긴다.

- **타겟들 + 웨이트 값** — `targetList` / `weightAliasList` 로 읽은 각 타겟과 가중치
- **컨스트레인 대상(child)** — 컨스트레인트 노드의 부모 트랜스폼

그리고 다음은 UI 에서 정한 값을 **전체 변환에 공통 적용**한다(컨스트레인트별이 아님).

- **Translate / Rotate / Scale 필터** 체크 여부 (기본: Translate 만 체크)
- **Maintain Offset** 체크 여부 (기본 체크)
- **InterpolationType** (`Average` / `Shortest`, 기본 `Shortest`)

본/대상 이름은 네임스페이스·DAG 경로를 제거한 **짧은 이름**(예: `ns:rig|clavicle_l` → `clavicle_l`)으로 들어가,
보통 UE 본 이름과 그대로 매칭된다.

---

## 폴더 구조

```
A00260_ConstraintConverter/
├── __init__.py                      # run() 노출
├── launch.py                        # run(): 창 생성 + green_dark 테마
├── __dragDrop_A00260.py             # 셸프 버튼 설치 (뷰포트 드롭)
├── icon/A00260_ConstraintConverter.png
├── ref_/smaple.py                   # UE 원본 노드 텍스트(출력 포맷 레퍼런스)
└── app/
    ├── config/version.py
    ├── ui/main_window.py            # TSL + 옵션 + Convert + 로그
    └── core/
        ├── constraint_reader.py     # 마야 씬 → ConstraintData (타겟/웨이트/대상)
        ├── node_builder.py          # ConstraintData + 옵션 → UE 노드 텍스트
        ├── constraint_converter.py  # 오케스트레이터 (PathManager, 0010_src→0020_out)
        ├── template_engine.py       # {{KEY}} 치환 (A00080_KWI_creator_V02 와 동일)
        ├── tool_path.py
        └── 0010_src/                # {{}} 플레이스홀더 템플릿 3종
            ├── A0001_Src_constraint_node.py   # 노드 전체 골격
            ├── A0002_Src_parent_decl.py        # parent 1개 선언(stub) 조각
            └── A0003_Src_parent_def.py         # parent 1개 정의(값) 조각
```

핵심 진입점: `ConstraintConverter().convert(constraint_nodes, ConvertOptions(...))`
→ `(combined_text, infos, out_path)`. 결과는 `app/core/0020_out/A001_constraint_nodes_out.py` 에도 저장된다.

---

## 설치

`__dragDrop_A00260.py` 를 Maya 뷰포트로 드래그&드롭 → 현재 셸프에 `CnsConv` 버튼 생성.
(`icon/A00260_ConstraintConverter.png` 가 있으면 아이콘으로, 없으면 `pythonFamily.png` 폴백)

## 실행

셸프 버튼 클릭, 또는 스크립트 에디터에서:

```python
import tools.A00260_ConstraintConverter as cc
cc.run(True)   # DEV_MODE 면 자기 자신 + Framework 리로드 후 실행
```

---

## UI 구성

- **Constraints** (TSL) — 변환할 컨스트레인트 노드 목록.
  - **List from Sel** — 선택에서 컨스트레인트를 찾아 리스트를 **교체**.
  - **Add from Sel** — 찾은 컨스트레인트를 중복 없이 **추가**.
  - Del / Up / Down / Sort — 항목 편집.
- **Convert Options**
  - **Filter**: Translate / Rotate / Scale 체크박스 (기본 Translate 만 ON).
  - **Maintain Offset** 체크박스 (기본 ON).
  - **Interpolation Type** 드롭다운 (`Average` / `Shortest`, 기본 `Shortest`).
- **Convert -> Copy to Clipboard** — 변환 실행 + 클립보드 복사 + 파일 저장.
- **로그** — 변환 결과 요약 / 안내 / 에러.

---

## 사용 순서

1. 마야에서 변환할 대상(컨스트레인트 노드 또는 컨스트레인된 트랜스폼)을 선택.
2. **List from Sel**(또는 **Add from Sel**)로 TSL 에 컨스트레인트를 리스트업.
3. Filter / Maintain Offset / Interpolation Type 옵션 설정.
4. **Convert** 클릭 → 텍스트가 클립보드에 복사되고 `0020_out/` 에 저장된다.
5. 언리얼 Control Rig 그래프에서 `Ctrl+V` 로 붙여넣기.

---

## 동작 규칙

- 선택이 **컨스트레인트 노드**면 그대로, **트랜스폼**이면 그 아래(`listRelatives -type constraint`)
  컨스트레인트를 수집한다. 지원 타입: `parentConstraint` / `pointConstraint` / `orientConstraint` / `scaleConstraint`
  (모두 UE Parent Constraint 노드 하나로 매핑).
- 타겟이 없는 컨스트레인트는 건너뛴다.
- 여러 컨스트레인트를 변환하면 각 노드 이름은 `ParentConstraint_1`, `ParentConstraint_2`, … 로 고유화되고
  세로로 간격을 두고 배치된다(Position Y 오프셋). 붙여넣을 때 UE 가 현재 그래프 경로로 다시 매핑하므로
  내부 그래프 경로 상수의 실제 값은 결과에 영향이 없다.
- 타겟 배열은 샘플의 UE 직렬화 형태를 그대로 재현한다 — 선언/정의는 인덱스 **내림차순**으로 나열,
  Parents 컨테이너 `SubPins` 는 **오름차순**, 정의 섹션의 `bIsDynamicArray=True` 는 **첫 parent 에만** 붙는다.
- 본/대상의 `Type` 은 샘플과 동일하게 `Bone` 고정(현재 버전).

> **검증**: 샘플 데이터(`clavicle_out_l` ← `clavicle_l` 0.6, `upperarm_l` 0.4, Translate 필터만,
> Maintain Offset ON, Shortest)로 생성한 결과가 `ref_/smaple.py` 와 384줄 전부 동일함을 확인.

---

## 로그 · 문제 해결

- `No constraints in the list. List some first.` — TSL 이 비어 있음. 먼저 List/Add 로 채운다.
- `Nothing converted. (No valid targets on the listed nodes.)` — 리스트 항목에 유효한 타겟이 없음.
- `Listed N constraint(s) from selection.` — N 개를 리스트업함.
- `Converted N constraint(s).` / `Copied to clipboard. Paste into Control Rig graph (Ctrl+V).` — 정상 완료.
- 붙여넣은 노드의 본 이름이 UE 와 다르면, 마야 조인트 이름이 UE 스켈레톤 본 이름과 일치하는지 확인
  (네임스페이스 제거 후의 짧은 이름 기준).
