---
name: wip-a00275-smooth-tab
description: "A00275 Weights > Smooth (v01.31) — kangaroo SkinCluster>Smooth 이식. 선택 밖 이웃은 읽기만 · Loop Curve 는 루프를 가로질러 푼다 · Rigid 는 약한 몫을 깎는다 · 쓰기는 구간 setAttr"
metadata:
  node_type: memory
  type: project
---

`A00275_skinTool_V01` **Weights > Smooth** (v01.30 -> **01.31**, 2026-09-22, 사용자 요청
"kangaroo SkinCluster 탭의 Smooth 를 분석해서 모두 이식").
코어 `app/core/weight_smooth_manager.py`, UI `app/ui/smooth_tab.py`(빌더 `_build_smooth_tab`).
원본은 [[kangaroo-plugin-external-readonly]] 대로 **읽기만** 했다 —
`kangarooTabTools/weights.py::smoothSkinWeights()` + `kangarooTools/patch.py`.

**Why:** 웨이트 스무딩을 쓰려고 플러그인을 띄우지 않아도 되게. 식은
`new[v] = (w[v] + Σw[이웃]) / (1 + 이웃 수)` 를 iteration 만큼(Jacobi).

**How to apply:**
- ★ **이웃은 선택 밖에 있어도 읽되 값은 바꾸지 않는다**(원본 `bIncludeNeighborsNotInIds=True`).
  이걸 빼면 선택 덩어리 가장자리가 바깥과 어긋나 계단이 생긴다.
- ★ **`Loop Curve` 는 루프를 "따라" 가 아니라 "가로질러" 푼다.** 이름만 보고 반대로 만들었다가
  테스트에서 걸렸다 — 커브가 집은 버텍스마다 **자기 번호를 라벨**로 받으므로 루프 위의 이웃은
  라벨이 달라 이웃 목록에서 빠지고, 남는 것은 루프를 벗어나는 쪽뿐이다. 입술·눈꺼풀 라인의
  결(구석->가운데)을 지키면서 라인을 넘는 쪽만 푸는 옵션이다.
- ★ **`Rigid` 는 "강한 것을 살린다" 가 아니라 "약한 몫을 깎는다".** 0~1 인 이웃 몫을 지수
  `1 + Rigid*0.25` 로 올리면 **작은 쪽이 비율상 더 깎인다**. 그래서 몫이 전부 같은 자리에서는
  정규화로 되돌아와 **값이 그대로**다(첫 테스트가 그 자리에서 "더 강해야 한다" 고 단정해 실패).
- ★ **쓰기는 구간 `setAttr`** (`weightList[v].weights[lo:hi]`, 바뀌는 버텍스만) —
  `MFnSkinCluster.setWeights` 는 undo 에 안 남는다([[wip-a00275-layer-tab]]). 스무딩은 눌러 보고
  Ctrl+Z 하는 기능이라 undo 가 필수다. 읽기는 API bulk.
- 세 마스크(Blend · 소프트 셀렉션 · 경계)는 **비율의 곱 하나**로 합쳤다 — 원본의 순차 lerp 세 번과
  값이 같다(셋 다 원래 값 쪽으로의 lerp).
- numpy 있으면 numpy, 없으면 같은 식의 순수 파이썬(두 경로 일치를 테스트로 고정).
  14,641 버텍스 x 3 인플루언스 x 4 iteration = 0.4초.
- **옮기지 않은 원본 옵션**: `bBarycentricWeighted`(원본이 실험 중이라 적어 둔 경로) ·
  `xDistanceMeshes` · `sSphereMasks` · `xClosestToCurve`(SkinCluster 탭 공용 마스크 + kangaroo
  `kt_findClosestPoints` 필요) · `iCheckMissingInfluences`(인플루언스를 더할 때의 규칙).
- kangaroo 의 UI 는 `uiSettings.addToUI` 데코레이터가 **함수 시그니처에서 자동 생성**한다.
  그래서 어떤 옵션이 화면에 있는지 보려면 시그니처 + 탭 공용 목록(`sTabControls`)을 함께 봐야 한다.
- UI 함정: **슬라이더가 스핀박스를 되먹어** 슬라이더 범위(20)를 넘는 Iterations 40 이 20 으로
  되돌아갔다. 동기화 플래그로 끊는다.
- 검증: 코어 53항목 + UI 38항목(mayapy 2024 + 오프스크린 Qt).
