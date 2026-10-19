---
name: wip-a00550-posemapper
description: "A00550_PoseMapper v01.00 (2026-10-19) — 음소 어트리뷰트 -> 블렌드셰이프 포즈(Pose Map, pm_NET + bw/clamp, json, Connect Skip 기본) + blendWeighted weight 편집 탭. blendWeighted: input 만 연결하면 weight 원소 없음 = UI 에 안 보이고 1.0 계산, getAttr weight[i] 는 원소를 만든다"
metadata:
  type: project
---

`A00550_PoseMapper` **v01.00** (2026-10-19). 계획 + 단계별 진행 기록: `JUN_All/docs/plans/A00550_PoseMapper_plan.md` §10.
테스트 씬 `D:\D__02.Art\...\D__Revision_Rig_0010\tmp\JP__CHN_Basic_1070_JALI_test.mb`(열기만, 저장 금지) — `jali_arkit_mapping_ctl.ma` 를
`JALI1:` 로 레퍼런스, BS `CHN_n_Face_xx_bs` 51 타겟 **전부 이미 구동** → 이 씬에 Build 하려면 Replace.

- **blendWeighted 함정 (실측)**: `input[i]` 만 연결하면 `weight[i]` 원소가 없어 Node Editor / AE 에 안 보이지만 **1.0 으로 계산**된다.
  ★ `getAttr bw.weight[i]` 는 **읽기만 해도 원소를 만든다** → 검사는 `getAttr -mi` 로만. 툴은 input 연결 때 weight 를 항상 같이 만든다.
- Pose Map: 타겟마다 `pm_bw_<t>`(weight = 포즈/Ref) + `pm_cl_<t>`, `pm_NET`(network) 이 message 로 source · target · 체인을 잡는다(이름 바뀌어도 OK).
  Ref 기본 10, 임의 실수(사용자 확정). 이미 구동된 타겟 기본 Skip(사용자 확정). 슬라이더 = `network.sync(only_targets=[t])`.
- Solo / Capture: 음소 plug 가 연결돼 있으면 값을 넣을 수 있는 위쪽 plug 로 올라간다(`JALI1:JALI_IN.AAA` → `JALI1:CNT_PHONEMES.AAA`).
  음소 목록 체크로 `Jaw` · `Lip` 같은 배율 입력은 기본 제외(0 으로 만들면 출력 전체 0).
- **Qt 함정 (v01.03)**: `QListWidget` 은 `item.setText()` 만으로도 `itemChanged` 를 쏜다 → 체크 변경 핸들러가 라벨 갱신에 반응해 Solo 를 껐다.
  라벨만 바꿀 때는 `blockSignals`, 체크 핸들러는 저장해 둔 상태와 비교해 실제 변경만. `editingFinished` 도 글자 그대로 포커스만 빠져도 온다.
  Solo 는 사용자가 체크박스를 끌 때 · 창 닫을 때만 끈다(사용자 요구).
- blendWeighted 의 weight 는 float32 — 되읽은 값 비교는 소수 4자리.
- 시험: tests/ 5개 74항목(mayapy). 마야 GUI 확인 전. 2단계: Jaw/Lip 축 배율 · 이름 유사 매칭 · 코렉티브.

관련: [[wip-a00540-jalilipsync]], [[jun-jali-repo]], [[mayapy-headless-verify]]
