---
name: wip-a00400-curve-joints
description: "A00400_CurveTool Edit > Joints — 커브 위 균일 조인트 + 커브 바인드 + zro/con/ctl/tgt 컨트롤러"
metadata:
  node_type: memory
  type: project
---

`A00400_CurveTool` **Edit > Joints** 탭 (v01.06 -> v01.07, 2026-09-07).
리스트업한 커브마다 조인트를 균일 배치 -> 그 조인트로 **커브를 skinCluster** -> 조인트마다
`_zro`/`_con`/`_ctl`/`_tgt` 스택을 세워 마지막 노드로 컨스트레인트한다. 컨트롤러 -> 조인트 -> 커브.

**Why:** 커브를 리깅에 쓰려면 커브를 직접 잡는 대신 무언가가 끌어 줘야 하는데, 그 셋업이
조인트 배치 · 바인드 · 컨트롤러 세 단계로 흩어져 있었다.

**How to apply:**
- 코어는 `app/core/joint_curve_manager.py`, UI 는 `_build_joints_tab` + `on_joints_create`.
  스택 구성 · 옵션 · 툴팁은 **`A00460_ControllerTool` 의 FK 탭과 같은 모양**으로 맞췄다
  (두 툴을 오가도 같은 자리에서 같은 이름을 찾게).
- **다른 툴의 core 를 import 하지 않는다** — `dev/build_release.py` 는 **툴 하나 + Framework**
  만 복사해서 릴리스를 만든다. A00460 의 `fk_manager` 를 참조했다면 릴리스에서 곧바로 깨진다.
  툴 사이 공유가 필요하면 `Framework` 로 올릴 자리다.
- **"균일하게" 는 호 길이 균등이 기본**이다. 파라미터 균등(`minValue~maxValue` 등분)과 다르고,
  스팬 길이가 제각각인 커브(엣지에서 뜬 커브가 대표적)에서 **짧은 스팬에 조인트가 몰린다.**
  CV `(0,0,0)(1,0,0)(11,0,0)` 에 3개 -> 호 길이 `0, 5.5, 11` / 파라미터 `0, 1, 11`.
  호 길이는 `MFnNurbsCurve.length()` + `findParamFromLength()`.
- **닫힌 커브는 `u=0` 과 `u=1` 이 같은 점**이라 그대로 등분하면 마지막 조인트가 첫 조인트 위에
  겹친다. `.form != 0` 이면 `count` 등분(0, 1/n, 2/n ...)으로 바꿔 마지막 자리를 뺀다.
  엣지 루프에서 뜬 커브가 대부분 여기 해당한다.

**확인한 것 (mayapy 2024):**
- **커브에도 skinCluster 가 걸린다** — 메시 전용이 아니고, `polyToCurve` 로 뜬
  **히스토리가 살아 있는 커브**에도 걸려 조인트가 CV 를 끈다(디포머가 히스토리 뒤에 낀다).
- **바인드는 조인트를 그룹에 넣은 뒤에** — `bindPreMatrix` 가 바인드 시점 행렬을 잡으므로
  순서가 뒤집히면 리페어런트만으로 커브가 튄다.
- **리페어런트가 롱네임을 죽인다** — 조인트를 그룹에 넣는 순간 `|spine_1_jnt` 는 없는 경로가
  되어 `cmds.xform` 이 `No object matches name`. 결과에는 **옮긴 뒤 경로**를 담고, 컨트롤러
  스택은 옮기기 전에 **UUID** 를 잡아 뒀다 다시 해석한다([[uuid-safe-rename-duplicate-names]]).
- **`cmds.joint` 는 현재 선택의 자식으로 붙는다** — 매번 `select(clear=True)` 하지 않으면
  조인트끼리 체인이 되어 버린다. 커브 구동 조인트는 각자 독립이어야 한다.
- 조인트 방향은 `rotate` 말고 **`jointOrient`** 에 쓴다(로컬 = `R * JO`, 갓 만든 조인트는
  `R=0` 이라 JO 가 곧 월드 방향). `rotate` 에 넣으면 애니메이터가 채널을 0 으로 돌릴 때 풀린다.
