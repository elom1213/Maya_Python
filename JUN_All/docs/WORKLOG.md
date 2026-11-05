---
title: 작업 일지 (WORKLOG)
aliases: [WORKLOG, 작업일지, devlog]
tags: [worklog, maya-python]
updated: 2026-11-05
---

# 작업 일지 (WORKLOG)

git 커밋 기록을 근거로 하루 작업을 요약한다. 최신 날짜가 위.

**이 파일은 현재 월을 담는다.** 지난 달은 [`worklog/`](worklog/) 로 내려간다 —
파일 자체는 늘 이 경로에 있으므로 이 문서를 가리키는 링크는 깨지지 않는다.
트리거와 절차는 [`worklog/README.md`](worklog/README.md).

> [!info] 보기
> Obsidian 에서 `JUN_All/docs` 를 vault(또는 폴더)로 열면 속성/태그/링크가 동작한다.
> 굵게/링크가 별표째 보이면 소스 모드이므로 `Ctrl+E` 로 읽기/라이브 프리뷰 전환.

---

## 지난 달 보관

| 월 | 파일 | 작업일 |
|----|------|--------|
| 2026-10 | [`worklog/2026-10.md`](worklog/2026-10.md) | 14일 |
| 2026-09 | [`worklog/2026-09.md`](worklog/2026-09.md) | 16일 |
| 2026-08 | [`worklog/2026-08.md`](worklog/2026-08.md) | 18일 |
| 2026-07 | [`worklog/2026-07.md`](worklog/2026-07.md) | 18일 |
| 2026-06 | [`worklog/2026-06.md`](worklog/2026-06.md) | 12일 |

---

## 2026-11-05 (오늘)

> [!summary] A00110_animTool_V02 **v02.51 Bake > Bake 구간 밖 키 보존** `#A00110_animTool`
- 보고: 컨스트레인트를 걸고 Bake List 로 [10, 50] 만 구우면 그 밖의 기존 키가 지워진다(오브젝트는 Base + 다른 레이어에 키).
- 실측(mayapy): 레이어 없으면 정상. **레이어 멤버 채널**에서 `bakeResults -time -preserveOutsideKeys` 는 Base 커브를 [s, e] 의 41 키만 남기고 바꾸고
  (구간 밖 f70 tx 8.0 → 1.0), 합성값을 Base 에 써서 구간 안에서 위 레이어를 이중 계산. keep / bake down 둘 다 컨스트레인트는 남김.
- 수정 `BakeManager.bake_layered`: 컨스트레인트 켠 채 샘플 → 채널마다 대상 레이어(덮는 맨 위 override · 없으면 Base) 커브의 [s, e] 만 지우고
  (s-1 / e+1 fixed 모양 보존 — 듬성한 커브 보간 보호) `setKeyframe -animLayer 대상 -value` 역산. additive · override · 뮤트 · 잠김 처리.
- 덤으로 찾은 버그: `bakeResults -smart` 가 레이어 없이도 구간 밖 60 f 값을 바꿈 → dense + 구간 안만 Douglas-Peucker. `filterCurve -simplify` 는 허용오차 무시(실측).
- 한계: 키가 없던 채널은 원래 값이 컨스트레인트 순간 pairBlend 입력 0 → 마야 기본대로.
- 시험: `test_bake_layers.py` 19/19, 회귀 40 · 81 · 111 · 31. **GUI 확인 아직.**

## 2026-11-04

> [!summary] A00110_animTool_V02 **v02.50 Fix Sliding 크래시 수정** `#A00110_animTool`
- 보고: Fix Sliding 실행 중 마야 크래시 2 회(MayaCrashLog261104.1716 / .1749). 사용자 확인 = 두 번째 이후 실행, 디버그 커브가 그래프 에디터에 떠 있던 경우 있음.
- 분석: 버튼 → Python → `processEvents`(진행 팝업) → 그래프 에디터 paint → `AnimUISlice.dll TanimCurveCallbackManager::uiPainter` ACCESS_VIOLATION(0xFFFFFFFF).
  v02.49 `write_debug` 가 **undo 를 끈 채** 디버그 노드를 지우고 다시 만들었다 → 지운 커브가 바로 해제 → 그래프 에디터가 해제된 커브를 그림.
- 수정: ① 디버그 노드 · 커브 재사용(`MFnAnimCurve.remove` 7000 키 0.015 s, 노드 유지 — `cutKey -clear` 는 커브 노드까지 지워서 안 씀) · 옛 노드는 안내만
  ② Applying · Debug 동안 게이지는 단계 끝에만 ③ 그래프 에디터 `setUpdatesEnabled(False)` ④ 키 선택 비우기(`selectKey(clear=True)` 는 대상 없이 실패 → 골라진 커브를 remove).
- 시험: 40/40 · UI 15/15 · 회귀 81 · 21, KANA 두 번 연속 실행 — 노드 2 · 커브 8 재사용(UUID 동일), 33.4 s. 그래프 에디터 크래시 자체는 mayapy 에 GE 가 없어 재현 불가 → **GUI 확인 필요**.

> [!summary] A00110_animTool_V02 **v02.49 Fix Sliding 업데이트** `#A00110_animTool`
- 요청 4건: ① 디버그 노드를 TSL 오브젝트마다 `<이름>_debug_speed`(speed / smooth / threshold / result + source / info, 옛 단일 노드 정리)
  ② 그래프 에디터 커브 색 흰 · 밝은 하늘 · 빨강 · 초록(`animCurve.useCurveColor` + `curveColor`, mayapy 실측) ③ 탭에서 Layer 콤보 + Frames before (N)
  (처음 값 = Hot Key > Main, 펼칠 때 갱신, Hot Key 설정은 안 바뀜 — `run(layer=, offset=)` · `apply(layer=, offset=)`) ④ 공용 Expand 로 별도 창.
- 시험: `test_fix_sliding.py` 36/36 · `_ui` 15/15, 회귀 81 · 21 · 46. **GUI 확인 아직.**

> [!summary] A00110_animTool_V02 **v02.48 Bake > Fix Sliding** `#A00110_animTool`
- 계획서대로 구현: `core/fix_sliding_manager.py`(순수 함수 speeds · smooth · still_spans · merge_gaps · split_spans · blend_start + currentTime 샘플링 · preview · run · `_debug_speed`),
  `KeyframeManager._hold_curve / hold_range`(Shift+A 동작 불변), `HoldLayerManager.apply(force, ramp_start, hold_end)`, Bake > Fix Sliding 탭(TSL · 구간 · Speed · Spans · Keys · Preview / Fix Sliding · 진행 팝업 · optionVar).
- 정지 구간 [a, b] 마다 Hold + Layer Blend Key, B(Merge gap 4) → A(블렌드 시작 클램프) → D(b 에도 같은 레이어 값). 셋 끄면 순수 Shift+A.
- 시험: `test_fix_sliding.py` 30/30(핵심: 손으로 selectKey + run_hold 한 결과와 1e-9 일치 · 사용자 예시 [0,10]·[12,20] 에 f7 키 없음), UI 11/11,
  회귀 81 · 21 · 46 · 31 · 92 통과. **실측 KANA 씬**(사용자 제공, 저장 안 함): 6830 f 발 IK 둘, 191 구간, 34 s, 구간 안 월드 속도 0.69/0.82 → 0. **GUI 확인 아직.**

> [!summary] A00110_animTool_V02 **Bake > Fix Sliding 계획서** (`docs/plans/a00110_fix_sliding_plan.md`) `#A00110_animTool`
- 요구: `_SmartLayer` Fix Sliding 처럼 속도(원래 · 스무딩 · Threshold)로 정지 구간 [a, b] 를 찾되, 결과는 **그 구간 T/R 키를 고르고 Layer Blend Key 켠 채 Shift+A** 한 것과 같게.
  길이 > M 인 구간만(사용자 확정), Threshold = 최대 속도의 %, TSL 로 대상 리스트업, `_debug_speed` 4 커브.
- `_SmartLayer` 는 .pyc — 디컴파일 안 함, 툴팁 문구로 원리만 확인. 계획: Hold 커브 단위 리팩터 · `HoldLayerManager` `force` · 새 `FixSlidingManager`(순수 함수 + currentTime 샘플링) ·
  Bake > Fix Sliding 탭, 핵심 시험 = 손으로 selectKey + run_hold 한 결과와 1e-9 대조. 구현은 다음.
- 개정: 이웃 구간 블렌드 침범([0,10] · [12,20], N=5 → f7 키) 대안 A~E 를 §9 에 기록, **B(Merge gap, G 기본 4) → A(블렌드 시작을 앞 구간 끝에서 자름) → D(구간 끝 b 에 레이어 키 + flat)** 순서로 결정.

> [!summary] A00110_animTool_V02 **v02.47 Layer Blend 기준 = 고른 구간의 a** `#A00110_animTool`
- 요구: 현재 프레임 / −N 이 아니라, 그래프 에디터에서 [a, b] 를 고르고 Shift+A 하면 **a 와 a − N** 에 레이어 키.
- 구현: `HoldLayerManager.range_start()`(고른 키 최소 시간, Hold 전에), `run_hold` 가 frame=a 로 capture · apply, 없으면 현재 프레임.
  `values_at()` — a ≠ 현재 시간이면 undo 끈 채 시간 이동해 읽고 복귀.
- ★ 실측: 레이어가 있으면 `getAttr -time` · `MDGContext` 는 Base 값만, `currentTime -update false` 는 옛 값 → 실제 시간 이동만 맞다.
  `setKeyframe -animLayer -v` additive 역산은 키 시간 기준.
- 시험: 81/81(RA: [60,90] 선택 · 현재 100 → f60 · f50, 시간 복귀, undo 한 번, Current = f60 값, 키 없으면 현재 프레임) · UI 21/21. **GUI 확인 아직.**

> [!summary] A00110_animTool_V02 **v02.46 Current 축 키 누락 수정 + Auto-Focus 기본 ON** `#A00110_animTool`
- 보고: Layer Blend Key 로 AnimLayer1 에 찍힌 키를 보면 Pose Key `Current` 를 켠 축에 키가 없다.
- 원인: 키 축 = 축 체크만, Current 는 그 안에서 값만 바꿈(체크 ∩ Current) → 기본값(체크 rx rz ty / Current ry tx tz)이 안 겹쳐 Current 축이 통째로 빠짐.
- 수정: 키 축 = 체크 ∪ Current (`HoldLayerManager.effective_axes`, `set_pose_keys`, UI 수집, capture). + View > Graph Focus `Auto-Focus on Selection` 을 툴 열 때 ON.
- 시험: 73/73 · UI 21/21, 창 띄우는 기존 시험 5개(46 · 31 · 14 · 68 · 111) 통과. mayapy 는 scriptJob 이 None 이라 Auto-Focus 는 토글 · 설치 호출로 확인. **GUI 확인 아직.**

> [!summary] A00340_SelectionTool **v01.20 Share 덮어쓰기** `#A00340_SelectionTool`
- 보고: Buttons 의 `MUE_BCM` 을 Share 로 공유 쪽에 덮어쓰려 하면 "already exists" 팝업만 뜨고 막힘.
- 원인: `prefs.share_profile()` 이 공유에 같은 이름이 있으면 무조건 ValueError.
- 수정: Share 때 같은 이름이 있으면 **덮어쓸지 묻는다**(기본 No) → Yes 면 `share_profile(name, overwrite=True)` 로 교체 후 공유 것으로 전환.
  네임스페이스 매핑은 로컬에 있으면 그것, 없으면 공유 것 유지. 같은 드라이브는 `os.replace`, 다른 드라이브(NAS)는 복사 후 삭제.
- 시험: `test_shared_profiles.py` 51/51(prefs 덮어쓰기 · 매핑 두 경우 · UI No/Yes), `test_namespace_remap.py` 30/30. **마야 GUI 확인 아직.**

> [!summary] A00110_animTool_V02 **v02.44 Pose Key `Current` 축마다** `#A00110_animTool`
- 요구: `Use current values` 는 어트리뷰트마다 필요한 체크 → 전역 체크박스 대신 Pose Key 행마다 `Current`.
- 구현: `PoseKeyManager.set_pose_keys(current_axes=)`, `HoldLayerManager` 설정 `use_current` → `current_axes`(optionVar JSON, 옛 값은 체크 축 전부로 옮김),
  capture · apply 모두 축마다. 켠 행만 값 칸 비활성, Layer Blend 메시지 `current: tx`.
- 시험: 69/69(축마다 Pose Key · Layer Blend additive/override · 옛 설정 옮기기) · UI 19/19. **GUI 확인 아직.**
- **v02.45** 같은 날 추가 요청: `Current` 기본 켜짐 = rotate Y · translate X · translate Z(`DEFAULT_CURRENT_AXES`, 저장값 없을 때). 70/70 · UI 19/19.

> [!summary] A00110_animTool_V02 **v02.43 Layer Blend Key 보기 게이트** `#A00110_animTool`
- 요구: AnimLayer1 을 보며 그 구간 키를 골라 Shift+A 하면 Layer Blend 가 돌면 안 됨 → 고른 레이어(기본 BaseAnimation)를 볼 때만 동작.
- 구현: `HoldLayerManager.viewed_layers()`(에디터 선택 → preferred → 루트) · `view_gate()` — 보는 레이어가 정확히 그 하나일 때만,
  아니면 Hold 만 하고 `skipped - viewing '...'`. UI `Run only when viewing` 콤보(첫 항목 = 루트, 펼칠 때 갱신, optionVar `view_layer`, "" = 루트).
- 시험: 63/63(AnimLayer1 보며 그 커브 Hold → Layer Blend 건너뜀 · Base 에서 동작 · 둘 보기 · 게이트 반대 · preferred 폴백) · UI 19/19. **GUI 확인 아직.**

> [!summary] A00110_animTool_V02 **v02.42 Layer Blend Key = 선택한 오브젝트만** `#A00110_animTool`
- 요구: Layer 에 AnimLayer1 이 설정돼 있어도 AnimLayer1 의 모든 오브젝트가 아니라 **마야에서 선택한 오브젝트에만** 레이어 키.
- 조사(mayapy): v02.41 도 선택 오브젝트에만 찍힘 — 선택만 / 레이어 노드 · 세트 · 캐릭터 세트 섞임 / Use current values 켬끔 전부 A 만.
  Hold 쪽도 오브젝트 선택을 바꾸면 그래프 에디터 키 선택이 풀려 새지 않음. **재현 안 됨.**
- 방어: `selected_objects()`(ls -sl -objectsOnly, animLayer · objectSet · character 제외), run_hold 가 선택을 한 번 읽어 capture / apply 공유,
  메시지에 키 찍은 오브젝트 이름. 시험 51/51 · UI 16/16. **GUI 확인 아직.**

> [!summary] A00110_animTool_V02 **v02.41 Pose Key `Use current values`** `#A00110_animTool`
- 요청: Pose Key 에 "선택 컨트롤러의 체크 축에 지금 프레임 값으로 키" 체크박스, 켜져 있으면 Layer Blend Key 의 레이어 키도 같은 방식.
- 구현: `PoseKeyManager.set_pose_keys(use_current=)`(키 찍기 전에 전부 읽기), `HoldLayerManager` `use_current` 설정(optionVar) +
  `capture_current()` — `run_hold` 가 **Hold 전에** 값을 읽어 apply 에 넘김(Hold 가 커브를 바꾸면 움직여 둔 값이 사라지므로). 켜면 값 칸 비활성.
- 시험: 41/41(키 없이 바꾼 값 키 · additive/override 최종값 유지 · Hold 전 값 · undo 한 번) · UI 16/16. **마야 GUI 확인 아직.**

> [!summary] A00110_animTool_V02 **v02.40 Layer Blend Key 버그 수정** `#A00110_animTool`
- 보고: 컨트롤러가 AnimLayer1 에 있는데 Shift+A 가 Hold 만 하고 레이어의 현재 / −N 프레임 키를 안 찍음.
- 원인(mayapy 재현): DEV 리로드가 같은 깊이 모듈을 `sys.modules` 등록 순서로 reload → v02.38 세션에서 다시 열면 `hotkey_manager` 가 먼저 reload 돼
  **옛 `HoldLayerManager`** 를 잡음. UI 는 새 클래스에 설정, 핫키는 옛 클래스(enabled=False) → 메시지 없이 건너뜀.
- 수정: 설정 원본 = optionVar(update 쓰기 · apply 읽기), `run_hold` 는 호출 때 모듈 속성 조회, 예외는 뷰포트 에러 한 줄, `no layer chosen` 경고, 콤보 펼칠 때 레이어 갱신.
- 시험: 33/33(RL1 = 그 리로드 순서 재현 후 run_hold 가 키) · UI 12/12. **마야 GUI 확인 아직.**

> [!summary] A00110_animTool_V02 **v02.39 Shift+A Layer Blend Key** `#A00110_animTool`
- 요청: 계획서 `docs/plans/a00110_hold_layer_blend_plan.md` 대로 — Shift+A 가 Hold 에 더해 고른 레이어에 (현재 − N) 레이어 값 키 + 현재 프레임 Pose Key 키.
- 구현: `core/hold_layer_manager.py`(settings 저장소 + apply), `run_hold` 가 Hold + apply 를 한 undo 청크로, Hot Key > Main 에 `Layer Blend Key` 체크 · Layer 콤보(Refresh, missing) · Frames before,
  Pose Key 행 변경까지 push, optionVar 복원. 멤버 판정 = blend 사슬에 그 레이어 노드가 있는지.
- ★ 실측: additive 레이어에서 `setKeyframe -animLayer -value` 는 **최종값 역산** → −N 키는 커브에 직접(레이어 값 보존), Pose 키는 같은 호출로 **최종값 = Pose**.
  `getAttr -time` 은 레이어 blend 뒤 옛 값이 나올 때가 있다.
- 시험: 새 29/29(Additive · Override · 비멤버 · 없음 · 잠김 · 뮤트 · run_hold undo 한 번) + UI 11/11. **마야 GUI 확인 아직.**

> [!summary] A00210_FileManager **v01.46 화면 경로 표기 통일** `#A00210_FileManager`
- 요청: Store Repo 등에서 같은 경로가 `C:\...` 와 `C:/...` 로 다르게 보임 → 하나로.
- 구현: 슬래시(`/`)로 통일(NAS `//서버/...`). `app/core/paths.py` `ui_path`(normpath + /, UNC 유지) · `ui_text`(로그 안 Windows 경로만).
  프로파일 읽기(경로 키 8개) · 입력 마침 · Browse · `MainWindow.log`(모든 탭) · 툴팁 · 안내창 · Maya 탭(예전 normpath `\`) · `data_dir_of` 결과.
- 시험: 새 28/28(`\` 프로파일과 `/` 프로파일이 같은 글자, 로그, mayapy Browse), 기존 43/43 · 50/50 · 32/32(비교를 표기 무관으로 고침) · 31/31, A00480 44/44.

> [!summary] A00210_FileManager **v01.45 데이터 폴더 구조 (안 A) — 코드 · 리허설 완료, 원격 반영 대기** `#A00210_FileManager`
- 사용자: 안 A 확정 + `JUN_FileManager_data` Private 전환 → 확인(익명 API 404, 자격증명 없는 git 거부, 이 PC 자격증명 OK).
- 코드: Settings `Data Folder`(profiles/ 하위), 데이터 폴더 = `<Store Repo>/profiles/<folder>`(`prefs.data_dir_of`, A00211 공유), Push = 내 폴더만 → rebase → push(거절 재시도),
  클론 브랜치 확인 + `Switch to main`, 옛 프로파일 자동 변환(저장 폴더 이름 우선 → soundAliance=SA), 기본 브랜치 main, 비공개 URL → 공용.
- 시험: 새 43/43, 기존 50/50 · 32/32 · 31/31, A00480 Lineage 44/44. 실제 프로파일 10개 변환 = 계획 표.
- 리허설: `_migrate/`(백업 미러 2 + 클론, push 막힘) Dnable 265 · MUE 128 · SA 11 · src_rig 7 일치 · 기록 보존, 프로파일 10개 읽기 수 불일치 0.
  **다음: 계획서 §5 원격 반영(푸시 요청 턴). 그 전엔 A00210 Pull/Push 쓰지 말 것.**
- **반영(사용자 "푸시해")**: 데이터 저장소 `main` `8bc1d5b` + `archive/*` 태그 5개 푸시(옛 브랜치 유지), 이 PC 클론 `main` 전환(툴 `switch_branch`),
  Rig_Src · soundAliance · MUE store_dir → `JUN_FileManager_data`(프로파일 백업 후). **10개 프로파일 브랜치 OK · 파일 수 옛 클론과 같음.**
  남은 것: GitHub 기본 브랜치 `main`(사용자 — gh 미로그인), 1~2주 뒤 비공개 저장소 Archive · 옛 클론 · 옛 브랜치 정리.

> [!summary] **A00210 데이터 저장소 구조 변경 계획서** (`docs/plans/A00210_FileManager_data_folders_plan.md`) + FileManager 데이터 푸시 `#A00210_FileManager`
- 데이터 푸시: `JUN_FileManager_data` Dnable 미반영 82건(08-24 이후)을 `4690a34` 로 커밋 · 푸시(툴 Push 와 같은 형식). SA · src_rig · MUE 는 이미 원격과 같음.
- 관찰: 프로파일마다 브랜치(Dnable · SA · src_rig, 비공개 MUE) + 브랜치마다 클론, Dnable 한 브랜치에 프로파일 7개 데이터가 이미 섞임,
  **soundAliance 프로파일 branch=Dnable 인데 클론은 SA**(어긋남), master 는 06-19 이후 멈춤.
- 계획: `main` 하나 + `profiles/<data_folder>/`, 비공개는 저장소로 분리. 코드(prefs `data_folder` · `data_dir_of` · GitSync 내 폴더만 add + rebase 재시도 · check_branch · A00211)
  → 리허설 → (푸시 턴) 반영 → PC 전환 → 정리. **리허설 실측: 265=265 · 11=11 · 7=7 blob 차이 0, 기록 보존, 최장 경로 128자.**
- 개정: 비공개 저장소 폐지 요청 → MUE 도 `JUN_FileManager_data/profiles/MUE`. ★ 그 저장소가 **공개**(API 200)라 MUE 가 공개됨 →
  §0-A 결정(A Private 전환 후 기록째 권장 / B 공개 + 스냅숏 / C 공개 + 기록째). 리허설 MUE 128=128 blob 0, 기록째면 비공개 커밋 15 공개. 비공개 저장소는 Archive.

> [!summary] **A00220_BackupTool Save Cache 계획서** (`docs/plans/A00220_BackupTool_save_cache_plan.md`) `#A00220_BackupTool`
- 요청: 마야 저장을 SSD 캐시에 먼저 → 몇 초 뒤 원래 HDD 경로로 복사(덮어쓰기), n 개 파일, 체감 저장 속도 개선 + 저장 보장.
- 실측(이 PC C: NVMe · D: SATA HDD): python 쓰기 300MB 는 HDD 도 0.07s(OS 쓰기 캐시), 1.5GB 부터 1.7s(fsync 10s).
  **마야 실제 저장 426MB .mb · 904MB .ma 는 SSD = HDD (4~6s, 직렬화가 전부)** → 로컬 HDD 는 이득 거의 없음, NAS · 초대형 파일이 후보.
- 계획: 1단계 = 실제 씬 · NAS 실측 게이트(차이 없으면 중단). 진행 시 마야 저장 훅(rename → save → rename) + 파일 큐 + A00220 지연 복사기
  (최신만 · `os.replace` 원자 교체 · 충돌 사본 · 재시도 · 재시작 재개 · 종료/열기 훅). 구현은 사용자 확인 뒤.

> [!summary] **Framework `MOD_viewZoom_qt_v01` (리스트 · 트리 확대 / 축소 공용)** + A00110_animTool_V02 **v02.38 View > Layers 확대** `#Framework` `#A00110_animTool_V02`
- 요청: Layers 목록 행이 낮아 고르기 · Mute 체크가 불편 → 행을 키우거나, 확대 / 축소를 공용 기능으로 만들어 툴마다 공유.
- 공용: 뷰 하나에 붙이면 배율 하나로 글자 · 헤더 · 행 높이 · 체크박스 · 들여쓰기. Ctrl + 휠 · `Zoom [-] 150% [+]` · QSettings 기억 · 체크 칸 전체 클릭(행 선택 안 바뀜).
  ★ 아이템 뷰 체크박스는 스타일이 13px 고정으로 그려 qss 로 못 키움 → 델리게이트가 직접 그림. ★ 테마 qss `QWidget { font-size: 12px }` 가 `setFont` 를 덮음
  → 뷰 자신의 스타일시트에 px 로, 기준 = 부모 글꼴(Show 때 재적용). ★ 오프스크린 `QFontInfo.pixelSize()` 는 -1 → QFont 의 px / pt×DPI.
- A00110: Layers 기본 150%, Expand 창 440x600. 시험: 공용 **32/32 (PySide6 · PySide2)**, A00110 Layers 46/46 · 37/37. 테마 입힌 실화면 캡처 확인(오프스크린). **마야 GUI 확인 아직**.

> [!summary] A00110_animTool_V02 **v02.37 Bake > Locator — `Constrain Objects to Locators`** `#A00110_animTool_V02`
- 요청: LOC + Anim 으로 로케이터를 굽고 나서 각 로케이터가 각 오브젝트에 컨스트레인트를 걸게 — 기본 parent, point · rotate(orient) · scale 도.
- 구현: 체크 그룹(기본 끔) + Parent(기본) / Point / Orient / Scale, Parent ↔ Point·Orient 배타. 코어 `constrain_objects` — `mo=False`(로케이터 = 오브젝트 월드),
  잠긴 축 · 키 아닌 구동 축 skip, **scale 은 pairBlend 가 없어 키 있는 축에 scaleConstraint 가 실패 → 키 있는 축도 skip**(마야 Constrain > Scale 과 같음). 진행 팝업 `Constraining` 단계.
- 시험: 컨스트레인트 **34/34**(오브젝트 월드 오차 1e-15), UI 31/31, 기존 25/25 · 46/46 · 14/14. **마야 GUI 확인 아직**.

## 2026-11-03

> [!summary] **`SwingTwistEvaluatorNode` 대체 검토 + 계획서** (`docs/plans/A00590_SwingTwistNative_plan.md`) `#A00590_SwingTwistNative`
- 요청: MetaHuman for Maya 의 `SwingTwistEvaluatorNode`(Epic 플러그인) 의존 제거 — 마야 노드만으로 완벽 재현 가능한지 검토, 가능하면 계획서.
- 검토: 어트리뷰트 실측(입력 도 단위 · 트위스트 축 X 고정 · XYZ 고정 · jointOrient 무시) + UE RigLogic `TwistSwingJointsEvaluator` 수식과 일치 확인.
  `quatNodes`(Autodesk 동봉) 프로토타입 망 vs 원본 3000 샘플 **행렬 3e-15 · 오일러 3e-13°**, 특이 입력 22 개 오차 0 → **가능**.
- 주의: Pose Editor 의 DNA export 는 원본 노드를 찾으므로 변환 씬은 swing/twist 가 빠짐 → `Restore` 단계 계획. 구현은 사용자 확인(툴 위치 · 테스트 씬) 뒤.

> [!summary] A00210_FileManager **v01.44 Store Repo 칸 읽기 전용** `#A00210_FileManager`
- 요청: File Manager 의 Store Repo 경로가 붙여넣기만으로 바뀌어 실수가 생길 수 있음 → Browse 로만 바꾸게.
- 구현: `ipf_store_dir.setReadOnly(True)`(Remote 의 Store Repo · Local 의 Shared Folder 같은 칸) + 툴팁 안내. 선택 · 복사 · 코드의 setText(Browse · 모드 전환 · 프로파일 · 기본 경로)는 그대로.

> [!summary] A00110_animTool_V02 **v02.36 Bake > Locator — `LOC + Anim`(오브젝트마다 로케이터를 만들어 구간 월드 베이크)** `#A00110_animTool_V02`
- 요청: 마야에서 `_SmartLayer` 패키지로 쓰던 `LOC + Anim`(선택 오브젝트마다 로케이터 → 현재 타임라인 베이크)이 가끔 답답하거나 오류 → Bake 탭 하위 탭으로 새로.
  조건: 대상 오브젝트 TSL · 베이크 중 진행 팝업(게이지) · Start / End UI + `Get Current` · `Get Sel Range`.
- 구현: 새 하위 탭 `Locator`(Bake 다음). 코어 `LocatorBakeManager` — 로케이터 `<이름>_LOC`(월드, 회전 순서 복사) + 임시 parentConstraint(+ scaleConstraint)
  → **`bakeResults` 한 번** → 컨스트레인트 삭제 → 오일러 필터. 게이지는 **`MDGMessage.addTimeChangeCallback`** — simulation 베이크가 프레임마다 부른다(실측 201 회 / 200 프레임).
  구간을 쪼개면 첫 호출이 컨스트레인트를 끊어 안 됨 → 한 번 + 콜백. 실패 시 만든 것 삭제, undo 한 번. 구간 칸은 공용 timeRange + `Get Timeline`.
- 시험: 코어 **25/25**(월드 T/R 오차 1e-13 · 조인트 · 스케일 부모 · 이름 충돌 · 실패 정리 · undo), UI 오프스크린 **20/20**(진행 팝업 3단계 · 100% · 버튼들), 기존 시험 46/46 · 14/14 그대로.
  **마야 GUI 확인 아직**(실제 리그 · 팝업 모양).

> [!summary] A00400_CurveTool **v01.31 Display > Replace 두 리스트에 `Sort` 버튼** `#A00400_CurveTool`
- 요청: "A00400_CurveTool / Display / Replace 의 tsl 두개에 sort 버튼 추가해."
- 공용 TSL 에 이미 있던 Sort(이름순, UUID 유지)를 `show_sort=True` 로 켰다. 짝은 리스트 순서대로라 양쪽을 정렬하면 이름순 짝. **마야 GUI 확인 아직.**

> [!summary] A00510_release_builder **v01.04 마야 UI 테마 오염 수정 + `Run_ReleaseBuilder.bat` · 아이콘 바로가기** `#A00510_release_builder`
- 요청: "__dragDrop_A00510 툴을 마야에서 쓰니 마야의 모든 UI 가 이 툴의 UI 와 유사하게 변한다. 마야 UI 가 변하지 않도록. 그리고 실행 bat 파일과, 그 파일의 아이콘도 평소에 보이도록."
- 원인: `launch.run()` 이 마야 안에서도 `ThemeManager.load_theme_dev(app, ...)` 로 qss 를 **QApplication(=마야)** 에 입혔다. 덤으로 launch import 만으로 AUMID 를 지정해 마야 프로세스의 작업 표시줄 ID 도 바꿨다.
- 수정: 앱 전역(qss · 앱 아이콘 · AUMID)은 이 프로세스가 앱을 만들 때만, 마야 안에서는 `load_theme_to_widget(win)` 로 창에만. 다시 누르면 이전 창을 닫는다.
- bat: `Run_ReleaseBuilder.bat` — PySide6/2 있는 64비트 파이썬을 찾아 pythonw 로 실행(설치 없음). `.bat` 은 아이콘을 못 가지므로 `make_shortcut.py` 가 툴 아이콘 + AUMID 를 박은 `Release Builder.lnk` 를 같은 폴더에 만든다(공용 `shell_integration.create_shortcut`, 절대 경로라 gitignore, 스탬프로 바뀔 때만 재생성).
- 오프스크린 검증: 마야 상황(앱 선존재)에서 앱 qss · 다른 위젯 · AUMID 그대로, 창에만 qss · standalone 은 앱 qss 후 정상 종료 · bat `--no-launch` 로 바로가기 생성 확인. **실제 마야 GUI 확인 아직.**

> [!summary] A00210_FileManager **v01.43 Maya > Reference `Delete Display Layers` · `Delete Anim Layers`(기본 ON) + 탭 스크롤 제거** · Framework tabFit **PySide6 수정** `#A00210_FileManager` `#Framework`
- 요청: "각 탭 세로 길이를 줄이든 UI 에 맞게 조절되든 스크롤로 보지 않게. Maya / Reference 탭에 선택한 씬의 모든 레이어, 애니메이션 레이어를 지우는 체크박스(기본 둘 다 체크)."
- 원인: v01.42 의 탭 높이 자동 맞춤이 **PySide6 에서 한 번도 돌지 않았다** — `MOD_tabFit_qt_v01` 이 `int(QSizePolicy.Policy)` 로 TypeError → 매번 `fit skipped`. `_enum_int()` 로 고침(PySide2 동작 그대로).
  덤으로 `tabs_scroll` 안 탭의 hfw 보정 오차(Export 가 File Manager 높이로 열림)도 고침. 롤아웃 시험 **31 툴 · 134 검사 · 0 실패**.
- 축소: 공용 `MOD_fileTree_qt_v01` 에 `tree_hint_height`(기본 None = 그대로), A00210 의 리스트 · 트리 · 표 sizeHint 를 짧게, File Manager Settings 한 줄 절약.
  실화면 실측(작업 영역 2560x1552) File Manager 1480 → 1348 · Reference 987 · Export 1363, **모든 탭 스크롤바 없음.**
- 레이어: `ref_importer.delete_display_layers` / `delete_animation_layers` — 임포트 · 네임스페이스 뒤, 저장 전. 레퍼런스로 남는 것의 레이어는 건너뜀. 애니 레이어는 루트 삭제(`delete BaseAnimation;` 과 같음).
  mayapy 2024 실측: 디스플레이 3 · 애니 4 삭제, 남은 레퍼런스 레이어 `K:KEEP_LYR` 유지, 오브젝트 · Base 커브(0, 3) 유지. A00210 시험 32/32 · 50/50. **실제 파일 GUI 확인 아직.**

> [!summary] A00130_ControlRig_V02 **v02.30 Match 표 체크박스 — 체크된 행만 Match, 나머지 세트는 그대로** `#A00130_ControlRig_V02`
- 요청: "Match 탭 목록마다 체크박스, 체크된 것만 Match, 안 된 것은 방치. 기본은 전부 체크, 모두 체크 / 모두 해제 버튼."
- 구현(UI 만, `match_manager` 는 그대로): 행 0열 체크박스 + `Check All` · `Uncheck All` · `n / m checked`. `on_match` 가 체크된 행만 `match_manager.apply` 에 넘긴다. 체크 해제는 (조인트, 세트_wanted) 키 집합으로 기억해 표를 다시 그려도 유지. 다중 선택 전파는 공용 `JUN_mod_checkTree_qt_v01`.
- IK 세션은 체크와 무관하게 `D01_IK_handle` 전체 — 해제된 세트가 IK 체인이면 닫을 때 폴 평면 맞춤으로 움직일 수 있다(문서 §4.1e 에 명시).
- mayapy 2024 오프스크린 **13/13** (해제 행 원점 유지 · 체크 행 이동 · 갱신 후 유지 · Uncheck All 무동작 · Check All · 다중 전파). **마야 GUI 확인 아직.**

> [!summary] A00110_animTool_V02 **v02.35 Hot Key > Main `Animation Layers > Delete BaseAnimation` — MEL `delete BaseAnimation;` 과 같은 결과** · A00030_quickTool_V02 v02.10 에서 제거 `#A00110_animTool_V02` `#A00030_quickTool_V02`
- 요청: "delete BaseAnimation 이 mel 명령이 친 것과 같은 결과가 되도록 버튼을 추가." → 처음엔 A00030 v02.09 에 넣었다가 "A00110_animTool_V02 / Hot Key / Main 에 이식하고 A00030 에서 빼" 로 옮겼다. A00030 v02.10 은 코드가 v02.08 과 같다(이력만 남김).
- 구현: `AnimLayerManager.delete_root()` — 루트를 `animLayer -q -root` 로 찾아(이름을 박지 않음) `cmds.delete`. 마야가 자식 레이어 · blend 노드 · 레이어 커브를 지우고 Base 커브를 다시 직접 연결한다. UI 는 Hot Key > Main 의 새 `Animation Layers` 그룹 버튼 + 확인 팝업(기본 No), 지운 뒤 View > Layers 갱신. 되돌릴 수 없어 단축키는 걸지 않았다.
- mayapy 실측: 레이어 3단에서 mel 과 **남은 노드 · 프레임 1/5/10 값 · tx 입력 연결이 같다**. 이 삭제는 **undo 로 레이어가 돌아오지 않아서**(standalone, undo 켠 상태) 팝업을 둔다. 시험 `tests/test_anim_layers.py` **46/46**(D1~D6 추가). **마야 GUI 확인 아직** — 팝업 · GUI 에서의 undo.

---
