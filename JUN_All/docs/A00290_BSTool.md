# A00290_BSTool

레거시 `JUN_PY_BSTool_V01_01`(maya.cmds) 을 **PySide(Qt)** 로 재작성한 blendShape 작업 툴.
기존 툴의 **Connect BS 탭은 제외**하고 **Edit BS 탭만** 이식했으며, **Base Shape 탭**을 신규 추가했다.

- **아키텍처**: (B) Standalone/Qt — PySide, Maya 내 실행 (`A00270_skinMigrate` 클론, green_dark 테마)
- **버전**: `app/config/version.py`
- **설치**: `__dragDrop_A00290.py` 를 Maya 뷰포트로 드래그&드롭 → 셸프 버튼 생성 → `tools.A00290_BSTool.run(True)`

---

## 탭 1 — Edit BS

여러 blendShape 노드를 리스트에 담고 일괄 처리한다. (레거시 Edit BS 탭 그대로)

| 버튼 | 동작 |
|------|------|
| **Select BlendShape Nodes** / Add / Del / Up / Down / Sort | 씬 선택을 blendShape 리스트로 관리 (공용 `JUN_mod_tsl_qt`) |
| **Key every target** | 각 타겟을 프레임 `i` 에서 `1`, `i-1`/`i+1` 에서 `0` 으로 키 → 타임라인을 넘기면 타겟이 하나씩 순차로 보인다 |
| **Copy every target** | 위 키를 건 뒤, 프레임마다 베이스 메시를 복제해 각 타겟 모양을 **타겟 이름의 메시**로 추출(visibility off) → `<node>_targets` 그룹으로 묶음 |

> 리스트에 담긴 노드의 이름/순서는 자유. blendShape 가 아닌 항목은 무시된다.

## 탭 2 — Base Shape  (신규)

선택한 타겟의 **"기본(weight=1.0) 모양"을 다시 정의**한다.

### 사용 흐름
1. 아웃라이너/노드에디터에서 blendShape 노드(또는 그 메시)를 선택하고 **`<- Set`**.
   (메시를 고르면 히스토리에서 blendShape 를 찾아 채운다.)
2. **`List Targets`** → 타겟 이름이 weight 인덱스 순으로 리스트업된다.
3. 리스트에서 대상 타겟을 선택(`Select All` / `Clear Selection` 보조).
4. **Value** 에 기준 값을 입력(예: `0.5`, `1.3`).
5. **`Apply (Value -> 1.0)`** → 선택 타겟의 *Value 에서 보이던 모양*이 *weight 1.0 의 기본 모양*이 된다.

### 동작 원리
blendShape 결과는 `base + weight * delta` 이다(`delta` = 타겟 포인트 오프셋).
weight `X` 에서 보이던 모양을 weight `1.0` 의 모양으로 만들려면 **델타를 `X` 배**하면 된다:

```
new_delta = delta * X
weight 1.0 → base + 1.0*(delta*X) = base + X*delta = 예전 weight X 모양
```

즉 "값 X 의 모양을 1.0 의 기본 모양으로" == 타겟 포인트 델타를 `X` 배 스케일.
구현은 blendShape 노드의
`inputTarget[g].inputTargetGroup[w].inputTargetItem[i].inputPointsTarget`(pointArray)
를 직접 읽어 `X` 배 후 다시 써넣는다. in-between 아이템과 다중 출력 지오메트리도 함께 스케일한다.
전체가 **단일 undo 청크**.

- Value `0.5` → 타겟 강도 절반, `1.3` → 과장, 음수 → 반대 방향.
- Value 는 0 이 될 수 없다(0 이면 델타가 사라지므로 경고).
- 저장된 포인트 델타가 없는 타겟(라이브 지오 입력으로 연결된 경우 등)은 건너뛰고 로그에 표시.

---

## 구조

```
A00290_BSTool/
├── __init__.py                 # run() 노출
├── launch.py                   # run(reload): 창 생성 + green_dark 테마
├── __dragDrop_A00290.py        # 셸프 버튼 설치
├── CHANGELOG.md / requirements.txt
├── icon/A00290_BSTool.(png|svg)
└── app/
    ├── config/version.py
    ├── core/
    │   ├── blendshape_utils.py   # 타겟 조회 / 인덱스 매핑 / 베이스 메시 / 선택→blendShape
    │   ├── edit_bs_manager.py    # Edit BS 탭: key/copy every target
    │   └── base_shape_manager.py # Base Shape 탭: 타겟 델타 스케일
    └── ui/main_window.py         # QTabWidget 2탭 + 공용 로그
```

레거시 대비: **Connect BS 탭 제거**(Source/Attr/Destination 연결 기능). Edit BS 탭은 동작 동일.
