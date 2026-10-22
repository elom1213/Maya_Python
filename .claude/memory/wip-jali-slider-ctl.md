---
name: wip-jali-slider-ctl
description: "JALI 슬라이더 컨트롤러 리그 A0020_jali_slider_ctl.ma (2026-10-22) — angela 어트리뷰트 1:1 슬라이더 22 + JaLi 박스, output_min/max 리맵(remapValue), DUMMY_IN/OUT 3쌍, global_scale. 생성·검증은 JUN_JALI examples/build_jali_slider_ctl.py. 실측: textCurves 는 mayapy 에서 된다, remapValue 는 입력을 클램프"
metadata:
  node_type: memory
  type: project
  originSessionId: b7b47afb-4f2d-4c79-8c4d-370ee2905395
  modified: 2026-10-22T00:39:46.488Z
---

`C:\Users\USER\Desktop\JP\0035_maya_src_rig\02_Cage_JALI\A0020_jali_slider_ctl.ma` (2026-10-22, Maya 2024). 계획서 JUN_JALI `docs/0090_jali_slider_ctl_plan.md`
(§0-A 확정표 · §0-B 실측). 생성 · 검증 = JUN_JALI `examples/build_jali_slider_ctl.py` (`mayapy … <out.ma>` / `--verify <out.ma>` T1~T6 301항목).
A0010(`jali_arkit_mapping_ctl.ma`) 의 채널박스 전용 `CNT_PHONEMES/COARTIC` 를 뷰포트 슬라이더로 바꾼 것. **사용자 GUI 확인(S5) 아직.**

- 구조: `JALI_SLIDER_RIG`(`global_scale`) > `JALI_CTL_GRP`(`PH_<attr>_grp` 16 · `CO_<attr>_grp` 6 · `JALI_box_grp`/`CNT_JaLi`) + `JALI_DUMMY_GRP`
  (`DUMMY_IN/OUT_JALI · _PHONEMES · _COARTIC`). 슬라이더 = `<tag>_grp > _deco(Reference: 트랙·눈금·textCurves 라벨) + _drv > CTL_<tag>`(ty 0~1 제한, `output_min/max` 채널박스만).
- 노드망: `DUMMY_IN.X → _drv.ty`(손 조작과 더해짐) → `pma_<tag>` → `rv_<tag>`(remapValue, outputMin/Max ← 컨트롤러 attr) → `gs_<tag>`(× global_scale, Jaw/Lip 은 없음) → `DUMMY_OUT.X`.
- 이름 충돌 `LNTD GK FFF`(PHONEMES · COARTIC 양쪽) 때문에 더미는 3쌍. angela 의 `Project Enunciate dummy` 는 **어디에도 연결 없음** → 제외.
- 라벨은 ref 식(`LNTDm GKm MMMm FFFm WAp YAp`) + 머리글 `PHONEMES/COARTIC/JALI`. JaLi 박스는 tx/ty 0~1(기본 0.6 = 9), 보이는 크기는 부모 scale 2.
- **실측 (mayapy 2024)**: `textCurves(f="Arial")` 헤드리스에서 된다(폰트 크기 경고만) · `remapValue`/`setRange` 둘 다 입력을 범위로 클램프(1.3 → outputMax) · 부모 ty 연결돼도 자식 ty 는 settable.
- 미리보기 그림: CV 덤프 → 시스템 python(PIL 있음)으로 그렸다. JUN_JALI `.mfa/env/python.exe` 는 matplotlib 임포트에서 죽는다(exit 127, conda 미활성).
- 안내 문서 JUN_JALI `docs/0100_jali_dummy_out_attrs_guide.md`(2026-10-22): 어트리뷰트마다 angela 실측(음소 = 10, Jaw/Lip 9)으로 턱 각도 · 입술 근육 · 혀 조인트 변화. **COARTIC 실측 정정**: `LNTD` `GK` 는 혀만(음소 쪽보다 1.6배 · 3배, 턱 0), `MMM` `FFF` 는 `EXP_COARTIC_Lip` = (턱 각도)/30 이 곱해져 **턱이 닫히면 0** (0040 의 "단독 변화 없음" 은 혀를 빼고 잰 것), `WA/YA_PEDAL` 은 음소와 무관하게 상수(0.48 / 0.37·0.27·0.12).
- 후속(S6): `A00540` 은 `CNT_PHONEMES` 를 리그 표식으로 찾아 새 파일을 인식 못 함 → `DUMMY_IN_*` 매핑 json(scale 1) + `scene.RIG_MARKER` 설정화.

관련: [[jun-jali-repo]], [[wip-a00540-jalilipsync]], [[wip-a00550-posemapper]], [[mayapy-headless-verify]]
