---
name: wip-a00275-transfer-pairs
description: "A00275 Weights > Transfer 의 Target mode(1:1 타겟 리스트, v01.32) - 메시 아닌 항목은 짝 맺기 전에 걸러야 순서가 안 밀린다 · 진행률 팝업은 메시 단위 · kangaroo _pSelection 에 이름을 줄 수 있다"
metadata:
  node_type: memory
  type: project
---

`A00275_skinTool_V01` **Weights > Transfer** 의 `Target mode` (v01.31 -> **01.32**,
2026-09-22 사용자 요청). 기존 동작은 기본값 `Scene selection` 으로 그대로 두고,
`Target list (1:1)` 을 고르면 `Source Meshes` **우측에 `Target Meshes` TSL** 이 생겨
`소스[i] -> 타겟[i]` 로 전이한다. 코어 `weight_transfer_manager.transfer_pairs()` ·
`pair_meshes()`, UI 는 `main_window._build_transfer_tab` + `_sync_transfer_mode`.

**Why:** 메시 여러 벌을 한 번에 갈아 끼울 때 씬 선택을 바꿔 가며 누르는 일이 없어진다.

**How to apply:**
- ★ **메시가 아닌 항목은 짝을 맺기 *전에* 걸러낸다.** 지워진 노드가 리스트에 남아 있으면
  그 뒤가 한 칸씩 밀려 **엉뚱한 메시에 전이**된다(개수가 다르면 적은 쪽만큼 짝짓는 규칙과
  같은 함정). 걸러낸 사실은 로그에 적는다.
- 1:1 모드는 **전이 경로를 새로 만들지 않는다** — 짝마다 기존 `_transfer_one_native()` 를
  소스 하나 · 버텍스 선택 없음으로 부른다. 결과가 기존 모드와 같아야 하기 때문이다.
- 짝은 **메시 전체**가 대상이다(씬 선택을 보지 않는다). 그래서 1:1 모드에서는 soft falloff
  체크를 **끈다** — 계산에서 빠지는 값이 화면에서 살아 있으면 안 된다.
- kangaroo 도 같은 모드로 돈다 — `transferSkinCluster(_pSelection="<타겟 이름>")`.
  kangaroo 의 `_translateInput` 이 문자열을 `patch.patchFromName` 으로 바꿔 주므로
  **씬 선택을 건드리지 않고** 짝마다 부를 수 있다.
- 진행률은 공용 [[framework-progress-widget]] 팝업. core 는 `progress(done, total, message)`
  콜백만 안다. **메시/짝 하나 단위**로만 보고한다 — `copySkinWeights` 가 메시 안쪽 진행을
  주지 않는다. 콜백 예외는 삼켜 전이를 멈추지 않는다.
- ★ 팝업은 `finally` 에서 닫고 예외는 로그로 — 안 그러면 **모달 팝업이 뜬 채 트레이스백만**
  나와 사용자에겐 멈춘 것으로 보인다.
- ★ 테스트 함정: `isVisibleTo(window)` 는 그 위젯이 **현재 탭이 아닌 페이지**에 있으면 False 다.
  `setVisible` 결과는 `isHidden()` 으로 보고, 실제 표시는 창을 띄우고 그 하위 탭을 고른 뒤 본다.
- 검증 58항목(mayapy 2024 + 오프스크린 Qt).
