---
name: wip-a00060-curve-by-count
description: "A00060_V03 Create > From Curve 의 By Count (v03.12) - POCI turnOnPercentage parameter 0~1 등분 자리 = pointOnCurve = API kWorld (실측 일치), 길이 등분이 아니다, 닫힌 커브는 끝이 겹친다"
metadata:
  node_type: memory
  type: project
---

`A00060_jointTool_V03` **Create > From Curve > By Count** (v03.11 -> **03.12**,
2026-09-22 사용자 요청). 개수(2 이상)를 정해 커브마다 조인트를 만든다. 코어
`app/core/curve_joint_manager.joints_by_count()` · `parameter_fractions()`.

**Why:** CV / Edit Point 자리가 아니라 **개수**로 놓고 싶을 때. 요청 규칙은
"3 이면 POCI 입력 0 · 0.5 · 1.0 자리".

**How to apply:**
- ★ **POCI(`turnOnPercentage=1`) · `cmds.pointOnCurve(shape, pr=f, turnOnPercentage=True)` ·
  `MFnNurbsCurve.getPointAtParam(lo + (hi-lo)*f, kWorld)` 는 같은 월드 좌표다** — 실측으로
  확인했다(부모에 이동·회전·스케일, degree 1/3, 주기 커브 포함). 그래서 셋 중 아무거나 써도
  되고, 검증은 **실제 POCI 노드를 만들어 비교**하면 된다.
- ★ **파라미터 등분은 길이 등분이 아니다.** CV 간격이 불규칙하면 조인트 간격도 불규칙하다.
  길이로 고르게 놓는 것은 [[wip-a00400-curve-joints]] (A00400 Joints 탭) 쪽 규칙이다.
- **닫힌(주기) 커브**는 parameter 0 과 1 이 같은 점이라 마지막 조인트가 첫 조인트에 겹친다.
  자리를 비켜 놓으면 "POCI 와 같은 자리" 규칙이 깨지므로 **겹쳐 두고 로그로 알린다**.
- `Create as chain` 체크(기본 켬)를 끄면 조인트마다 선택을 비워 **루트**로 만든다. 분리 모드는
  조준할 자식이 없으므로 orient 를 건드리지 않는다(월드 정렬).
- 셰이프를 직접 넘긴다 — 트랜스폼 밑에 셰이프가 여럿이면 명령이 어느 것을 볼지 모른다.
- 검증 46항목(mayapy 2024 + 오프스크린 Qt).
