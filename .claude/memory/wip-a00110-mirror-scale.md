---
name: wip-a00110-mirror-scale
description: A00110 V02 Mirror Key 의 Scale 채널 — 미러하지 않고 소스 값을 그대로 복사한다(반사 행렬을 거치면 음수 스케일·셰어가 섞인다)
metadata:
  node_type: memory
  type: project
---

`A00110_animTool_V02` **Mirror Key > Channels > `Scale`** (v02.16, 2026-09-21, 기본 OFF).

**스케일은 미러하지 않는다 — 소스 `scaleX/Y/Z` 를 부호도 안 뒤집고 그대로 타겟에 넣는다.**
크기는 좌우가 같아야 하는 값이고, 반사 행렬(`refl * M * refl`)을 거쳐 다시 분해하면 축 순서에
따라 **음수 스케일이나 셰어**가 섞여 들어온다. 그래서 `Behavior` 를 켜든 끄든(= 월드 반사
모드에서도) **스케일 경로는 하나**다 — `_mirrored_values` 의 두 분기 모두 `_scale_values(src, t)`
를 쓴다. 사용자 요청도 "그대로 변화 없이 복붙" 이었다.

`mirror_key_manager` 에 `S_AXES` · `_scale_values()` · 각 진입점의 `do_scale=False` 인자
(끝에 붙여 기존 호출부는 그대로). `_settable_attrs(tgt, do_t, do_r, do_s)` 가 잠긴 채널을 거른다.
구간 미러 · 현재 프레임 미러 둘 다 적용되고, 세 채널을 다 끄면
`Enable Translate, Rotate and/or Scale.` 로 막는다. **Scale 만 켜고도 실행된다.**

곁가지: `_collect_times` 는 `cmds.keyframe(src, ...)` 로 **노드의 모든 커브** 시점을 모으므로
**스케일만 애니된 소스**도 `Source keys` 모드에서 그대로 잡힌다(따로 손댈 것이 없었다).

검증: mayapy 2024 헤드리스 30항목(두 모드 값 일치 · 음수 스케일 보존 · OFF 면 스케일 키 0 ·
Bake · 잠긴 채널 · 현재 프레임 per-channel 키잉 · 센터 self-mirror · undo 한 스텝 · 오프스크린
Qt 배선). 체크박스를 한 줄에 더해도 **창 최소 폭은 586 그대로**([[offscreen-size-needs-theme]]).
마야 GUI 에서는 아직 안 눌러 봄. 관련: [[mayapy-headless-verify]], [[framework-mirror-tokens]]
