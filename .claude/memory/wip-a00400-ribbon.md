---
name: wip-a00400-ribbon
description: A00400_CurveTool Create > Ribbon (v01.29) — 커브를 따라 납작한 NURBS 서피스, 마야 loft 와 CV 동일, 임시 커브 둘 + loft 로 만든다(cmds.surface 는 undo 불가), GUI 확인 아직
metadata:
  type: project
---

`A00400_CurveTool` **Create > Ribbon** (v01.29, 2026-10-30). 리스트의 커브마다 리깅용 **리본**
(납작한 NURBS 서피스) 하나. 코어 `app/core/ribbon_manager.py`
(`create_ribbons / build_ribbon / offset_direction / plane_normal / curve_data`), 회귀 `tests/test_ribbon.py` 75.

**Why:** 사용자 샘플 `C:\Users\USER\Desktop\JP\0001_tmp_01\sfcTest\sample_001.mb` 의 `curve` →
`loftedSurface` 를 재현하는 기능. 리본에 본 · 오브젝트를 어태치하려는 리깅 용도. 넣을 곳은 커브 중심
툴인 A00400 의 Create — 만든 서피스를 받는 `Edit > Joints`(바인드) · A00170 `AttachCrv`(어태치)가
이미 있어 흐름이 닫힌다. 어태치는 중복 구현하지 않고 로그로 안내.

**How to apply:**
- 샘플 구조(실측): **U = 커브의 CV · 차수 · 노트 그대로**, **V = CV 를 X 로 `-1, -⅓, +⅓, +1` 옮긴
  네 줄**(차수 3, 노트 0 0 0 1 1 1) = 복제 둘을 `loft -d 3` 한 것과 CV 동일. 샘플은 U 가 커브와 반대였다
  (`Reverse U` 옵션으로 재현, 기본은 커브 방향).
- **`cmds.surface` 는 undo 가 안 된다** → [[maya-surface-cmd-not-undoable]]. 그래서 월드 CV 로
  **임시 커브 둘**(`cmds.curve(p, k, per)`) → `loft`(ch 없음, `autoReverse=False`) → 삭제.
  정규화(0..1) · 뒤집기는 임시 커브의 노트 · CV 순서에 미리 반영(rebuild/reverseSurface 없음).
  `loft -d 1` 은 V 범위가 `0..2` → V 만 `rebuildSurface kcp kr0`.
- **원본 커브를 복제하지 말 것** — 부모가 회전돼 있으면 로컬 이동이 월드와 어긋난다(T5).
  `MFnNurbsCurve.cvPositions(kWorld)` 의 CV 와 `knots()`(= `(CV수 + 차수 - 1)` 개, `cmds.curve -k` 가 받는
  형식 그대로, 주기는 겹치는 CV 포함) 로 새로 만든다.
- Direction Auto = CV 공분산 최소 고유벡터(순수 파이썬 3x3 야코비 — [[maya-2023-compat]] numpy 없음).
  직선은 선과 가장 수직인 월드 축(동률 X, Y, Z 순) + 노트, 비평면은 최적 평면 + 노트, 한 점은 거부.
- 옵션: Width 2 · Direction Auto/X/Y/Z · Across cubic(4줄)/linear(2줄) · Normalize U(켬) · Reverse U · Name(`<curve>_ribbon`, 네임스페이스 뗌).
- **남은 일**: 마야 GUI 확인(탭 높이 · 결과). 관련 [[wip-a00400-curve-joints]], [[wip-a00170-attachcrv-tab]], [[mayapy-headless-verify]].
