# A00260_ConstraintConverter

마야 씬의 **컨스트레인트 세팅**을 언리얼 **Control Rig** 의 **Parent / Position / Rotation Constraint**
노드 텍스트로 변환해 **클립보드에 복사**하는 PySide 툴.
언리얼 Control Rig 그래프에 그대로 `Ctrl+V` 붙여넣으면 노드가 생성된다.

- **아키텍처**: (B) Standalone/Qt — PySide, Maya 내 실행 (`A00110_animTool` 클론)
- **버전**: `app/config/version.py` (v01.06)
- **설치**: `__dragDrop_A00260.py` 를 Maya 뷰포트로 드래그&드롭 → 셸프 버튼(`CnsConv`) 생성 → `tools.A00260_ConstraintConverter.run(True)`
- **참고 출력 포맷**: `ref_/sample_position.py`, `ref_/sample_position_close.py`, `ref_/sample_rotate.py`
  (UE Control Rig 에서 각 노드를 복사한 원본 텍스트. Parent 용 옛 샘플 `smaple.py` / `sample_01~04.py` 는 제거됨)

---

## 무엇을 하나

마야 컨스트레인트(`parentConstraint` 등)에서 다음을 읽어 UE Constraint 노드로 옮긴다.

- **타겟들 + 웨이트 값** — `targetList` / `weightAliasList` 로 읽은 각 타겟과 가중치
- **컨스트레인 대상(child)** — 컨스트레인트 노드의 부모 트랜스폼

그리고 다음은 UI 에서 정한 값을 **전체 변환에 공통 적용**한다(컨스트레인트별이 아님).

- **Constraint Type** (`Parent` / `Position` / `Rotation`, 기본 `Parent`) — 생성할 UE 노드 종류
- **축(X/Y/Z)별 Translate / Rotate / Scale 필터** (기본: Translate 의 X/Y/Z 만 체크)
- **Maintain Offset** 체크 여부 (기본 체크)
- **InterpolationType** (`Average` / `Shortest`, 기본 `Shortest`)

본/대상 이름은 네임스페이스·DAG 경로를 제거한 **짧은 이름**(예: `ns:rig|clavicle_l` → `clavicle_l`)으로 들어가,
보통 UE 본 이름과 그대로 매칭된다.

---

## Constraint Type (v01.05)

생성할 UE 노드를 드롭다운으로 고른다. 세 노드는 **Child / Parents(타겟+웨이트) / Maintain Offset / Weight**
구성이 같고, **Filter 핀의 모양**과 **AdvancedSettings 핀 유무**만 다르다.

| Type | UE 노드 (`ResolvedFunctionName`) | Filter 핀 | AdvancedSettings | 노드 이름 접두사 |
|------|----------------------------------|-----------|------------------|------------------|
| `Parent`   | `FRigUnit_ParentConstraint` | `Translation` / `Rotation` / `Scale` **3중첩**, 각 `bX/bY/bZ` | 있음 (`InterpolationType`) | `ParentConstraint_` |
| `Position` | `FRigUnit_PositionConstraintLocalSpaceOffset` | **단일** `bX/bY/bZ` | **없음** | `PositionConstraint_` |
| `Rotation` | `FRigUnit_RotationConstraintLocalSpaceOffset` | **단일** `bX/bY/bZ` | 있음 (`InterpolationType`) | `RotationConstraint_` |

- **Filter 는 축(X/Y/Z) 단위 3×3 그리드**다. `Parent` 는 Translate/Rotate/Scale 세 행을 모두 쓰고,
  `Position` 은 **Translate 행만**, `Rotation` 은 **Rotate 행만** 쓴다.
- 안 쓰는 행(과 `Position` 의 `Interpolation Type`)은 **비활성 + 흐리게** 표시된다.
  테마 qss 에 `:disabled` 규칙이 없어 그냥 `setEnabled(False)` 만으로는 색이 그대로라,
  옵션 그룹박스에만 `DISABLED_QSS`(`main_window.py`)를 덧대 흐리게 만든다.
- 타입을 바꿨을 때 그 타입이 쓰는 채널의 축이 **전부 꺼져 있으면 X/Y/Z 를 자동으로 켠다**
  (필터가 전부 `false` 면 노드가 아무 일도 하지 않으므로). Convert 시에도 축이 하나도 없으면 막고 로그를 남긴다.

---

## 폴더 구조

```
A00260_ConstraintConverter/
├── __init__.py                      # run() 노출
├── launch.py                        # run(): 창 생성 + green_dark 테마
├── __dragDrop_A00260.py             # 셸프 버튼 설치 (뷰포트 드롭)
├── icon/A00260_ConstraintConverter.png
├── ref_/                            # UE 원본 노드 텍스트(출력 포맷 레퍼런스)
│   ├── sample_position.py           #   Position Constraint (펼친 형태)
│   ├── sample_position_close.py     #   Position Constraint (접힌 형태)
│   └── sample_rotate.py             #   Rotation Constraint
└── app/
    ├── config/version.py
    ├── ui/main_window.py            # TSL + 옵션 + Convert + 로그
    └── core/
        ├── constraint_reader.py     # 마야 씬 → ConstraintData (타겟/웨이트/대상)
        ├── node_builder.py          # ConstraintData + 옵션 → UE 노드 텍스트, NODE_TYPES 스펙
        ├── constraint_converter.py  # 오케스트레이터 (PathManager, 0010_src→0020_out)
        ├── template_engine.py       # {{KEY}} 치환 (A00080_KWI_creator_V02 와 동일)
        ├── tool_path.py
        └── 0010_src/                # {{}} 플레이스홀더 템플릿 6종
            ├── A0001_Src_constraint_node.py   # Parent 노드 전체 골격
            ├── A0002_Src_parent_decl.py        # parent 1개 선언(stub) 조각  (3종 공용)
            ├── A0003_Src_parent_def.py         # parent 1개 정의(값) 조각    (3종 공용)
            ├── A0004_Src_link.py               # 노드 간 ExecutePin 연결(RigVMLink) 조각
            ├── A0005_Src_position_node.py      # Position 노드 전체 골격 (v01.05)
            └── A0006_Src_rotation_node.py      # Rotation 노드 전체 골격 (v01.05)
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
  - **Constraint Type** 드롭다운 (`Parent` / `Position` / `Rotation`, 기본 `Parent`).
  - **Filter**: `Translate` / `Rotate` / `Scale` × `X` / `Y` / `Z` 체크박스 3×3 그리드
    (기본 Translate 의 X/Y/Z 만 ON). 선택한 타입이 안 쓰는 행은 흐리게 비활성화.
  - **Maintain Offset** 체크박스 (기본 ON).
  - **Interpolation Type** 드롭다운 (`Average` / `Shortest`, 기본 `Shortest`). `Position` 에서는 비활성.
- **Convert -> Copy to Clipboard** — 변환 실행 + 클립보드 복사 + 파일 저장.
- **로그** — 변환 결과 요약 / 안내 / 에러.

---

## 사용 순서

1. 마야에서 변환할 대상(컨스트레인트 노드 또는 컨스트레인된 트랜스폼)을 선택.
2. **List from Sel**(또는 **Add from Sel**)로 TSL 에 컨스트레인트를 리스트업.
3. Constraint Type / Filter(축별) / Maintain Offset / Interpolation Type 옵션 설정.
4. **Convert** 클릭 → 텍스트가 클립보드에 복사되고 `0020_out/` 에 저장된다.
5. 언리얼 Control Rig 그래프에서 `Ctrl+V` 로 붙여넣기.

---

## 동작 규칙

- 선택이 **컨스트레인트 노드**면 그대로, **트랜스폼**이면 그 아래(`listRelatives -type constraint`)
  컨스트레인트를 수집한다. 지원 타입: `parentConstraint` / `pointConstraint` / `orientConstraint` / `scaleConstraint`.
  마야 컨스트레인트의 **종류는 매핑에 쓰이지 않는다** — 어떤 타입이든 타겟/웨이트/child 만 읽고,
  생성할 UE 노드는 UI 의 **Constraint Type** 이 결정한다.
- 타겟이 없는 컨스트레인트는 건너뛴다.
- **세 노드 모두 닫힌(접힌) 형태로 출력**된다(v01.06) — Filter / Parents / AdvancedSettings 드롭다운이 접혀
  있어 노드 길이가 짧다. 펼친 형태와의 차이는 **컨테이너 핀의 `bIsExpanded=True` 유무뿐**이다
  (`sample_position.py` ↔ `sample_position_close.py` 는 딱 두 줄 차이 — `Parents` 컨테이너와 `Filter` 컨테이너).
  컨테이너 안쪽 `Parents.N` / `Child` 의 `bIsExpanded=True` 는 접힌 형태에도 그대로 남는다.
- 여러 컨스트레인트를 변환하면 각 노드 이름은 `ParentConstraint_1`, `ParentConstraint_2`, … 로 고유화되고
  (접두사는 Constraint Type 에 따라 `PositionConstraint_` / `RotationConstraint_`)
  **가로로 나열**된다(Position X 오프셋). 한 줄에 **4개**를 채우면 줄을 바꿔 아래로 내린다(Position Y 오프셋).
  붙여넣을 때 UE 가 현재 그래프 경로로 다시 매핑하므로 내부 그래프 경로 상수의 실제 값은 결과에 영향이 없다.
- **노드 간 연결(v01.04)**: 생성된 노드들을 **생성 순서대로 `ExecutePin` → `ExecutePin`** 으로 잇는
  `RigVMLink` 블록(`A0004_Src_link.py`)을 노드 텍스트 뒤에 덧붙인다 — 붙여넣으면 노드들이 **실행 체인으로
  연결된 상태**가 된다. 노드가 **1개면 링크 없음**,
  N 개면 `RigVMLink_0 … RigVMLink_{N-2}` 로 N-1 개 생성. 빌더의 `NodeBuilder.build_links(graph, node_names)`.
- 타겟 배열은 샘플의 UE 직렬화 형태를 그대로 재현한다 — 선언/정의는 인덱스 **내림차순**으로 나열,
  Parents 컨테이너 `SubPins` 는 **오름차순**, 정의 섹션의 `bIsDynamicArray=True` 는 **첫 parent 에만** 붙는다.
- 본/대상의 `Type` 은 샘플과 동일하게 `Bone` 고정(현재 버전).

> **검증(Parent)**: 닫힘 샘플 데이터(`ball_l` ← `upperarm_twist_01_l` 0.764, `upperarm_twist_02_l` 0.236, Translate
> 필터만, Maintain Offset ON, Shortest)로 생성한 결과가 당시 레퍼런스(`ref_/sample_02_close.py`, 현재는 제거됨)와
> 381줄 전부 동일함을 확인.
>
> **검증(Position / Rotation, v01.06)**: 샘플 데이터(`dyn_pants_btmL_01_01` ← `thigh_twist_02_l` 0.8,
> `thigh_twist_01_l` 0.2, X 축만 필터, Maintain Offset ON, Average)로 `ConstraintConverter.build_text()` 가
> 만든 텍스트가 `ref_/sample_position_close.py`(접힌 형태) 및 `ref_/sample_rotate.py` 의 접힘 변환본과
> **바이트 단위로 동일**함을 확인 (노드 이름 · Position 좌표 제외).

---

## 로그 · 문제 해결

- `No constraints in the list. List some first.` — TSL 이 비어 있음. 먼저 List/Add 로 채운다.
- `Nothing converted. (No valid targets on the listed nodes.)` — 리스트 항목에 유효한 타겟이 없음.
- `Listed N constraint(s) from selection.` — N 개를 리스트업함.
- `No axis checked for <Type>. Check at least one of X / Y / Z.` — 선택한 타입의 필터 축이 전부 꺼져 있음.
- `Constraint type: <Type> (filter: ...)` — 타입을 바꿈. 괄호는 그 타입이 쓰는 채널.
- `Converted N constraint(s) -> <Type> Constraint node(s).` /
  `Copied to clipboard. Paste into Control Rig graph (Ctrl+V).` — 정상 완료.
- 붙여넣은 노드의 본 이름이 UE 와 다르면, 마야 조인트 이름이 UE 스켈레톤 본 이름과 일치하는지 확인
  (네임스페이스 제거 후의 짧은 이름 기준).
