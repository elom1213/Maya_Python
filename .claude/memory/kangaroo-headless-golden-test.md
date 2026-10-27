---
name: kangaroo-headless-golden-test
description: Kangaroo Builder functions run in mayapy for golden comparison (load kt_cmdUndo + dummy report); quirks - To list is list(set()) so exact ties are nondeterministic, Border Edges crashes on numpy 2
metadata:
  type: reference
---

Kangaroo 를 이식할 때 **원본을 mayapy 에서 직접 돌려 숫자로 대조**할 수 있다(2026-10-27, A00275 Weights > Move).

```python
sys.path.insert(0, r"...\0020_maya_plugin\0010_kangaroo\scripts")
cmds.loadPlugin(r"...\0010_kangaroo\plug-ins\win64\<2022~2025>\kt_cmdUndo.py")   # setSkinClusterWeights 가 kt_cmdUndo 를 부른다
import kangarooTabTools.weights as ktw
import kangarooTools.report as rep
rep.report = Dummy()      # __getattr__ -> no-op. 헤드리스에서는 None 이라 resetProgress 에서 죽는다
ktw.moveSkinClusterWeights(xJoints={"['fA','fB']": "['t1','t2']"}, bDisableIslandCheck=True,
    iCheckMissingInfluences=patch.MissingInfluencesOptions.onlyAddMissingInfluencesInSkinCluster)
```

**Why:** 이렇게 대조해서 Move 이식이 15 케이스 차이 0 ~ 2e-16 으로 고정됐고, 원본과 다른 점 두 개(점 좌표 읽는 명령, 동률)를 찾았다.

**How to apply:**
- 점 좌표는 원본처럼 `cmds.xform('shape.vtx[*]', q, ws, t)` 로 읽는다 - `MFnMesh.getPoints` 와 마지막 자리가 달라 동률 판정이 갈린다.
- `moveSkinClusterWeights` 의 To 목록은 `list(set(...))` - **진짜 동률이면 Kangaroo 끼리도 실행마다 다르다**. 대조 씬은 동률을 피한다.
- `iBorderEdges != 0` 이면 `getBorderMask -> smoothValues2d(bLockArray)` 가 numpy 2.x 에서 IndexError(불리언 길이가 패딩 행만큼 짧음) - 원본 버그. 그 케이스는 성질로 검증.
- 테스트 스크립트는 환경 변수(`JUN_KANGAROO_DIR`)가 없으면 대조를 건너뛰게 만든다. 관련 [[maya-fbx-import-nonxyz-flip]]
