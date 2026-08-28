---
name: wip-a00130-ik-session
description: A00130_ControlRig_V02 Match 가 앞뒤로 IK 를 껐다 켠다. IK 는 연결이 아니라 솔버로 써서 막힌 걸로 안 보인다(조용한 거짓 성공), snapEnable 은 평가 중에 핸들을 써서 undo 를 깨뜨린다 (v02.03)
metadata:
  type: project
---

**`A00130_ControlRig_V02` 의 IK 편집 세션** (v02.03, 2026-08-28) — Match 가 앞뒤로
`D01_IK_handle` 의 IK 를 껐다 켠다. `app/core/ik_session.py`.
계획서 Phase 4 · 7-4. 관련: [[wip-a00130-v02-match]] · [[wip-a00060-ik-edit]].

```
IK 끄기  ->  매칭  ->  핸들 스냅 + 폴 벡터 역산  ->  IK 켜기
```

**IK 조인트는 "막힌 걸로 안 보인다"** ★ — IK 는 **어트리뷰트 연결이 아니라 솔버로** 쓴다:

```
connectionInfo("jnt_mid.rotateZ", isDestination=True)  ->  False
channel_group_state("jnt_mid", "rotate")               ->  free
```

그래서 `matchTransform` 은 **성공하고** 다음 평가에서 IK 가 도로 가져간다
(`직후 [15,25,35] -> 평가후 [0,0,0]`). **로그엔 `[OK] matched` 가 찍히는데 씬은 그대로다** —
조용한 거짓 성공. 잠금/연결 판정만으로는 절대 못 잡는다.

**끄고 켜는 것만으로는 부족하다** — `ikBlend` 를 되켜면 조인트가 **원위치**로 간다.
**핸들 스냅 + 폴 벡터 역산**까지 해야 남는다. 그 계산은 **다시 만들지 않고**
`A00060_jointTool_V03` 의 `begin_edit`/`end_edit`/`cancel_edit` 을 부른다.

**★ `snapEnable` 이 undo 를 깨뜨린다** (진짜 함정은 예상한 곳이 아니라 옆에 있었다)

켜져 있으면 **마야가 평가 중에 ikHandle 의 translate 를 직접 쓴다**(핸들을 이펙터에 붙인다).
그 쓰기가 편집 사이사이에 끼어들어 undo 큐가 재구성하지 못한다:

| | before | after | **undo** |
|---|---|---|---|
| `snapEnable` 그대로 | `[20,0,0]` | `[18,0,3]` | **`[19.063, 4.226, 0]`** ✗ |
| 껐다 켜기 | `[20,0,0]` | `[18,0,3]` | **`[20,0,0]`** ✓ |

→ **세션 동안 꺼 두고 스냅이 끝난 뒤에 되켠다.** `end_edit` 은 `xform` 으로 명시적으로
스냅하므로 결과는 같다.
곁가지 확인: **마야의 undo chunk 는 정상적으로 중첩된다** — 중첩은 원인이 아니었다.

**`ikBlend` 는 이 케이지에서 안 쓰인다**(사용자 확인 2026-08-28). 그래서 계획서 7-4 가
"최대 기술 리스크" 로 꼽은 **씬 전역 IK 정지**로 물러설 일이 없다 — 핸들별로 끈다.
**다만 가정하지 않는다**: `preflight()` 가 실행 시점에 `ikBlend` 가 구동되는 핸들을 찾으면
**크게 알린다**(전제가 깨졌다는 뜻이고, 그대로 두면 씬 전체 IK 가 꺼진 채 매칭이 돈다).

**나머지 계약**
- 세트 이름은 `template_map.json` 의 `ik_handle_set`. **조인트·세트·옵션 컨트롤러와 같은
  이름 해석**(네임스페이스 먼저) → 레퍼런스 케이지 지원
- 세트가 없으면 **조용히 세션 없이** 매칭(예전 동작) · 핸들 아닌 멤버는 **개수를 알리고** 무시
- **예외가 나면 체인을 시작 상태로 되돌리고** IK 를 켠 뒤 올린다 —
  반쯤 매칭된 체인에 IK 가 다시 붙는 게 제일 나쁘다
- A00060 이 편집 상태를 **핸들 어트리뷰트에** 남기므로, 지난 실행이 끊겨도
  `stranded_handles()` 로 알아챈다

검증 **IK 44 + Match 110 + Length 126 = 280항목**.
[[mayapy-headless-verify]] · [[undo-chunk-by-default]] · [[referenced-node-name-comparisons]]
