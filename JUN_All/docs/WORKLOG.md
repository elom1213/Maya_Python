---
title: 작업 일지 (WORKLOG)
aliases: [WORKLOG, 작업일지, devlog]
tags: [worklog, maya-python]
updated: 2026-09-18
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
| 2026-08 | [`worklog/2026-08.md`](worklog/2026-08.md) | 18일 |
| 2026-07 | [`worklog/2026-07.md`](worklog/2026-07.md) | 18일 |
| 2026-06 | [`worklog/2026-06.md`](worklog/2026-06.md) | 12일 |

---

## 2026-09-18 (오늘)

> [!summary] A00380 By Weight — **블렌드셰이프 타겟 Edit 가 켜진 메시**에서 Apply 에러 수정(v01.12)
- 원인: `sculptTarget` 이 셰이프 `tweakLocation` 을 `bs.inputTarget[g].vertex[0]` 에 연결하면 `setAttr shape.pnts` 가 타겟 델타로 **더해지면서** `RuntimeError` 를 낸다(구간 쓰기는 원소 누락까지). `move -r -os` 는 정상이지만 1만 버텍스 11초 · undo 14초.
- 수정: 새 `app/core/sculpt_target.py` — Edit 중인 아이템(`5000 + 1000 × sculptInbetweenWeight`)의 `inputPointsTarget` / `inputComponentsTarget` 에 이동량을 더해 setAttr 두 번(1만 버텍스 0.03초, undo 한 번). 라이브 타겟이면 타겟 메시 `pnts` 를 옮긴다(origin world 면 공간 변환). 로그에 `into sculpt target ...`.
- mayapy 2024 43항목: Edit 없음 · w=1 · 조인트 둘 · 기존 델타 · w=0.5 · origin world/local + 회전·스케일 · 라이브 · 인비트윈 0.5 가 마야 `move` 결과와 일치, undo, pnts 안 건드림. 라이브 + origin world 는 **마야 자체 편집이 어긋나** 공식과 대조해 일치. 마야 GUI 에서는 아직 안 눌러 봄.
- 남은 것: Match > Default · Peak 은 Edit 중인 메시에 쓰면 같은 에러. #A00380

> [!summary] Framework **리로드 뒤 `super(type, obj)` TypeError 수정** — A00380 `Apply By Weight` 중 `MOD_log_qt_v01.eventFilter` 에서 터지던 것
- 원인: 툴 실행(`run(True)`)이 DEV_MODE 에서 `Framework` 를 `importlib.reload` 한다. 이미 떠 있던 창의 로그 위젯(옛 클래스 인스턴스)은 툴 창에 eventFilter 를 걸어 둔 채 남는데, `super(JUN_mod_log_qt_v01, self)` 의 클래스 이름이 이제 **새 클래스**를 가리켜 옛 인스턴스와 맞지 않는다. 그 창에 이벤트가 올 때마다(씬 변경 → 다른 툴 창 갱신 등) 에러.
- 수정: `Framework/qt` 10개 파일의 `super(Class, self)` 32곳을 zero-arg `super()` 로 — 메서드가 정의된 클래스(`__class__` 셀)에 묶여 리로드 뒤에도 맞다. 전부 자기 클래스 메서드 바로 안인지 AST 로 확인 후 치환.
- mayapy 2024: 로그 위젯 생성 → eventFilter 설치 → 모듈 reload → 이벤트/eventFilter·expand·collapse 호출. 수정 전 같은 TypeError 재현, 수정 후 전부 통과. 마야 GUI 에서는 아직 안 눌러 봄. #Framework

> [!summary] A00380 **Apply Match 진행률 팝업**(v01.11) — 공용 `JUN_mod_progress_qt_v01` 을 그대로 씀(새로 안 만듦)
- 단계 `Reading meshes`(30) / `Writing vertices`(70), 메시마다 이름을 띄운다. 미리보기 세션이 있으면 읽기가 끝나 있으므로 Writing 만(자리를 남기면 게이지가 30% 에서 시작해 보인다).
- 코어에는 `from_pairs(..., progress=None)` · `commit(weight, progress=None)` 콜백만. 로그에 걸린 시간.
- mayapy 오프스크린: 팝업 5번 전부 보인 채 100% 도달 후 닫힘, 미리보기 뒤 Apply 는 Writing 한 단계, 기존 Match 12항목 그대로 통과. #A00380

> [!summary] A00380 Match > Default 를 **좌(Source) / 우(Targets) 리스트**로(v01.10) — 우측 메시들을 좌측 모양으로, 좌 1개 = `1 <= n`, 여러 개 = `n <= n`
- 개수가 다르면 작은 쪽 수만큼 짝짓고 남는 메시는 로그에 이름 · 순번으로. 짝 미리보기 표 + 모드 줄. 코어 `match_manager.pair_meshes` / `MatchSession.from_pairs`(같은 Source 는 한 번만 읽음).
- 테스트에서 잡은 것: 리스트를 바꿔도 **옛 미리보기 세션으로 Apply 가 확정**됐다 → 리스트가 바뀌면 되돌리고 버린다. 로그 이름은 셰이프가 아니라 트랜스폼으로.
- 창 최소 435x651 → 540x732(좌우 TSL). TSL `Order` 체크박스를 빼서 한 쪽 291 → 238px — 메시 오브젝트는 고른 순서가 원래 유지된다.
- mayapy 2024 + 오프스크린 12항목 통과. 마야 GUI 에서는 아직 안 눌러 봄. #A00380

> [!summary] A00290_V02 **`Target > Delete`** — 체크한 타겟을 blendShape 노드에서 지우기(v02.03). `Target` 하위 탭 = `Naming` · `Delete` · `Target Order` (처음엔 `Edit` 아래 두 겹으로 묶었다가 요청대로 한 겹으로)
- 노드 지정 → 타겟 체크 목록 → `DELETE CHECKED TARGETS`(확인 대화상자). 공용 `JUN_mod_checkList_qt` + Filter, 필터에 가려진 체크는 안 지운다.
- 삭제는 마야 Shape Editor 와 같은 MEL `blendShapeDeleteTargetGroup` — `inputTargetGroup` 통째 삭제는 undo 로 델타가 안 돌아오는데, 이 MEL 은 잎부터 지워 Ctrl+Z 한 번에 델타 · 인비트윈까지 복원(실측). lock 된 weight 는 회색으로 잠금.
- mayapy 2024: 코어(삭제 · lock 거절 · undo/redo) + 오프스크린 UI 12항목 통과, 최소 창 586px 로 가로 스크롤 없음. 마야 GUI 에서는 아직 안 눌러 봄. #A00290

> [!summary] A00220 `Settings` 접이식을 **기본 접힘**으로(v01.17)
- 시작 창 높이를 본문 높이만큼 줄여 파일 목록 크기는 그대로. 오프스크린(런치 테마) 실측: 접힘 612px → 펼침 890px(수정 전 기본과 같음) → 다시 접으면 612px. #A00220

> [!summary] A00380 Match 를 하위 탭 **Default / By Weight** 로(v01.09) — By Weight = 스킨 웨이트를 마스크로 메시들을 타깃 쪽으로 `웨이트 × 델타`
- **요청**: 기존 Match 는 Default 로 이식. By Weight 는 스킨 메시 M_w 의 조인트를 체크 목록으로, 타깃 M_tgt 한 칸, 옮길 메시 M_j TSL — 블렌드셰이프 마스크와 같은 결과.
- `new = cur + mask × Strength × (M_tgt − cur)` (오브젝트 공간, 인덱스 대응). 짝짓기 두 방식: **Joint k -> Mesh k**(기본, jnt_01→M_01) / **Sum -> every mesh**. 짝 미리보기 표.
- 조인트 목록은 공용 `MOD_checkList_qt` + `MOD_filter_qt`. 웨이트는 `MFnSkinCluster.getWeights` 한 번, 이동은 Match 의 `MatchTarget`(pnts 구간 setAttr) 재사용 → Ctrl+Z 한 번.
- 창 크기: 그대로 넣으면 최소 435x615 → 660x1002. 스크롤 + 긴 그룹 제목 줄임 + 라디오 세로 배치(테마에서 라디오 하나 245px)로 435x651(하위 탭 바만큼).
- mayapy 2024: 코어 11항목(예시 0.2/1.0 · 짝 · 합 × 0.5 · undo · 토폴로지 불일치 · 스킨 없음) + Qt 오프스크린 탭(로드 · 회색 조인트 · 짝 표 · 적용 · undo) 통과. 마야 GUI 에서는 아직 안 눌러 봄. #A00380

> [!summary] `A00480_FileTool` 규칙에 걸린 **숨긴 메시를 마야에서 선택** — Check 와 막힌 Export 둘 다 (v01.04 -> 01.05)
- **요청**: Check 를 하고 하이드된 메시가 있다면 그 메시를 마야 씬에서 선택.
- `RuleResult.nodes`(문제 노드, 전체 경로) 추가 → `run_rules` 가 `(passed, logs, nodes)`. UI 는 받은 노드를 `select(replace)` 하고 로그. 앞으로의 규칙도 nodes 만 채우면 같은 동작.
- 막힌 Export 뒤에도 선택(같은 검사). 모두 통과면 선택을 건드리지 않는다.
- mayapy 2024 29항목(Check 선택 = 숨긴 4개 · 막힌 Export 선택 · 통과 시 선택 유지 · 중복 없는 전체 경로). #A00480

> [!summary] `A00480_FileTool` `Check Hide Mesh` 는 **메시 자신만** 검사 — 숨겨진 그룹 · 조인트 등은 괜찮다 (v01.03 -> 01.04)
- **요청**: 메시에 대해서만 검사, 메시가 아닌 오브젝트는 hide 되어 있어도 좋다.
- 조상을 거슬러 올라가던 검사를 메시의 **쉐입 + 트랜스폼** 둘로 줄였다. 그래서 켜진 메시가 숨겨진 그룹 안에 있는 경우도 이제 안 걸린다.
- mayapy 2024 24항목(숨긴 그룹/조인트 아래 메시 · 숨긴 로케이터는 통과, 메시 자신의 원인 5종은 여전히 잡음, 걸리면 FBX 0개). #A00480

> [!summary] `A00480_FileTool` Export 에 **규칙** — 내보내기 전에 모든 세트를 검사, 하나라도 걸리면 파일을 하나도 안 쓴다. 첫 규칙 `Check Hide Mesh` (v01.02 -> 01.03)
- **요청**: 내보낼 때 여러 규칙을 추가·선택 적용. 첫 규칙 Check Hide Mesh — Set's Name 세트 안 메시 중 visibility 가 꺼진 것이 있으면 내보내기를 시작하지 않고 어떤 세트 · 어떤 메시인지 경고. 규칙은 계속 늘고 여러 개를 동시에 적용. (중간 추가 요청: 도중에 멈추지 말고 한 개도 내보내지 말 것)
- `app/core/export_rules.py` — 레지스트리 `EXPORT_RULES`(한 줄 = 규칙) + `run_rules`: 켠 규칙을 **전부** 돌리고 모든 세트를 먼저 검사, 실패면 `export_sets` 를 부르지 않는다. 규칙 예외도 실패로 친다.
- 숨김 판정 = 씬에서 실제로 안 보임: 자기 · 쉐입 · **조상**의 visibility / lodVisibility / 디스플레이 레이어 / 드로잉 오버라이드. intermediate(Orig) 쉐입 제외. 원인을 로그에.
- UI 는 Type Filter 옆 `Rules (n/m)` 드롭다운 + `Check`(내보내지 않고 검사) — 규칙이 늘어도 창 크기 그대로(HEAD 와 나란히 재서 같음).
- mayapy 2024 24항목(원인 6종 · Orig 무시 · 하위 세트/컴포넌트 · 조인트 아래 · 실패 시 FBX 0개 · 통과 시 내보냄 · Check). #A00480

> [!summary] `A00130_ControlRig_V02` `Orient & Place` 표에 **필터** — Joint · Rule · Note 에서 글자 찾기, `In` 으로 열 선택 (v02.25 -> 02.26) + 공용 필터 `tree_columns`
- **요청**: 검색으로 joint 혹은 Rule, note 에 어떤 글자가 있는지 찾고 걸러 보기.
- 공용 `JUN_mod_filter_qt` 는 트리를 한 열만 봤다 → `tree_columns`(여러 열) + `set_tree_columns()` 추가. 단어마다 어느 열이든, 단어끼리는 AND, 열 사이엔 줄바꿈을 끼워 경계를 넘은 글자는 안 맞게. 기존 `tree_column` 사용처(A00275 · A00330)는 그대로.
- 표 필터는 **보이는 것만** 바꾼다 — Orient & Place 는 여전히 모든 규칙(툴팁·문서에 명시).
- mayapy 2024 44항목(113행 x `In` 4 x 검색어 8 전수 대조 · Check 뒤 유지 · 가려진 척추도 정렬) + 공용 위젯 PySide6 6항목. #A00130 #Framework

> [!summary] `A00130_ControlRig_V02` `Orient & Place` 에 **손 규칙** — `hand_l` = `lowerarm_l` 과 같은 방향, `hand_r` = 왼손의 미러 (v02.24 -> 02.25)
- **요청**: hand_l 은 상위 본 lowerarm_l 과 회전값이 같도록, hand_r 은 hand_l 을 미러한 방향.
- 팔 `tail` 에 `parent`(끝 조인트 = 부모의 월드 방향, arm_l) · `mirror`(A2 는 안 건드리고 늦은 미러가 덮음, arm_r) 추가. 전에는 둘 다 `preserve`.
- 오른손은 원래 늦은 미러가 덮고 있었다 — `preserve` 표시와 겹쳐 보이던 것을 `mirror` 로 정리.
- **발견**: 오른팔 A2 는 `+Z`→월드 `+Z` 라 왼팔의 Behavior 미러가 아니다 → 왼손을 미러한 `hand_r` 은 `lowerarm_r` 대비 X 180도(실측). 요청대로 미러를 따르고 보고.
- mayapy 2024 9항목 — 템플릿 두 벌 대조로 두 손 말고 전부 예전과 같음(2e-13). #A00130

> [!summary] `A00130_ControlRig_V02` `Orient & Place` 에 **쇄골 규칙** — `clavicle_l` 의 `+X` 가 `helper_upperarm_l`, `+Y` 가 월드 `+Y` (v02.23 -> 02.24)
- **요청**: helper_clavicle_l 의 바로 하위본(helper_upperarm_l)을 X forward 로, up 은 Y 축.
- A1(`aim_groups`)에 `aim_at` 추가 — 리스트 밖 조인트를 **겨누기만**. upperarm 을 리스트에 넣으면 방향까지 잡아 A2 팔 규칙과 겹친다.
- **오른쪽 쇄골도 규칙으로** — 이른 팔 미러가 정렬 전 왼쪽을 복사하므로 왼쪽만 넣으면 좌우가 어긋난다. `-X` / `-Y`→월드 `+Y` 가 왼쪽의 Behavior 미러와 행렬 단위로 같다(4e-16).
- mayapy 2024 10항목 — 템플릿 전체 두 벌(예전/새 규칙) 대조로 **쇄골 둘 말고는 전부 예전과 같음**(1e-13). 규칙 없는 조인트는 `helper_root` 하나. #A00130

> [!summary] `A00060_jointTool_V03` `Orient > Aim` 에 **Mode `Chain` / `Root`** — Root 는 루트 하나로 모든 최하위 자식까지, 루트마다 pole 하나 (v03.10 -> 03.11)
- **요청**: A00145 Mirror 탭의 Mode 처럼 라디오 두 개. Chain 은 지금처럼 Start/End, Root 는 그 자리에 Root 리스트 하나 — 리스트의 각 루트부터 최하위 자식까지 aim, 루트에 대응하는 pole tgt 하나를 향하게.
- 분기점은 **첫 번째 자식**을 조준(마야 `Orient Joint` 와 같은 규칙), 나머지 가지도 끝까지. 계산은 Chain 과 같은 `_apply_tasks` 공유.
- **발견한 버그(두 모드 공통)**: X 를 자식으로 조준해도 자식이 제자리에 남는 건 자식이 이미 부모 X 축 위에 있을 때뿐 — 분기점의 다른 가지, 정렬 안 된 체인은 위치가 틀어졌다(실측 1.49, 가이드는 "완전 보존"). 돌린 직후 움직인 자식만 원위치시키도록 고쳤다. 정렬된 체인은 예전과 결과 차이 0.
- mayapy 2024 34항목(분기 계층 X/보조축/위치 · undo · 잘못된 입력 · pole 부족 · Chain 예전 일치 · 비정렬 위치 보존 · 잠긴 자식 경고 · UI 전환/실행). #A00060

> [!summary] `A00240_PathTool` Shrink 세로를 **A00220 과 같은 155px** 로 (v01.12 -> 01.13)
- **요청**: 줄었을 때 세로가 A00220 이 줄었을 때와 같도록 - 지금(78px)은 작다.
- `SHRINK_HEIGHT` 78 -> 155. 78px 에 트리를 넣으려던 창 여백 2px 조정은 필요 없어져 걷어냈다(기본 여백).
- 트리는 줄 높이에 맞춰 커진다 - 한 행 26.6px 에서 칸 2px(아이콘 20 x 24, 선 4px). 코드 변경 없이 기존 배치 계산 그대로.
- 오프스크린 PySide6: A00220 실제 줄인 크기(350 x 155)와 같음 · 여백 불변 · 반복/복원 8항목 + 캡처. #A00240

> [!summary] `A00240_PathTool` Shrink 애니메이션 피드백 — **무한 반복** · 맨 밑 한 쌍 제거(5행) · 선 2px (v01.11 -> 01.12)
- **요청**: 처음부터 끝까지 무한 반복, 맨 밑의 아이콘 1 · 2 제거, 전체 선 굵게.
- 반복은 단계마다 0.5초씩 보이게(파일 0 → 둘까지 → 완성 → 처음) 한 바퀴 1.5초 — 완성 직후 바로 되감으면 완성된 트리가 한순간만 보여서. 머무는 구간엔 다시 그리지 않는다.
- "전체 선" = 연결선 + 아이콘 테두리로 보고 둘 다 2px(아이콘 10 x 12). 5행이 되어 한 행 14.8px 에 들어간다.
- 오프스크린 PySide6 시각별 아이콘 수 · 실시간 3.4초 반복 확인 + 캡처 6장. #A00240

> [!summary] A00460 FK & IK 에 **Skip End Joints**(v01.07) — FK 에서 체인 끝 n 개 조인트는 컨트롤러를 만들지 않는다
- **요청**: 정수 칸(기본 0), FK 모드에서 최하위 자식 n 개 생략 — `jnt_01>02>03>04`, n=2 → 01, 02 만.
- Bone Root 는 **가지마다**: 조인트의 높이(가장 깊은 잎까지 거리) < n 이면 그 아래 전부 건너뜀. 가장 긴 가지 기준이라 남긴 조인트의 부모가 빠지지 않는다. Bone Chain 은 리스트 마지막 n 개. IK 에서는 칸이 꺼지고 무시.
- 건너뛴 조인트는 컨스트레인트도 없이 부모 조인트를 따라가고, 로그에 이름이 나온다.
- mayapy 2024 17항목(기본 체인 · n=0 · n≥길이 · IK 무시 · Chain · 분기 · 칸 활성/비활성 · UI 실행 + undo) 통과. #A00460

> [!summary] `A00240_PathTool` Shrink **파일 트리 애니메이션** — 파일 0 → 0.5초 뒤 셋이 펼쳐지고 → 다시 0.5초 뒤 하나씩 더 (v01.10 -> 01.11)
- **요청**: 계획대로 애니메이션 작업. 계획서 확인 5가지는 전부 추천안(다 자라면 정지 · 줄었을 때 여백 2px · 0.25초 ease-out · 테마 글자색 · 켤 때마다 재생).
- `app/ui/file_tree_anim.py` — 7x9 픽셀 파일 아이콘을 QPainter 로(공룡과 같은 방식). 펼침 = 진행값 하나로 위치(부모 자리 → 자기 줄, 부채꼴) · 연결선 길이 · 투명도가 함께.
- 다 자라면 타이머를 멈춘다(줄여 둔 창은 오래 켜 두는 상태). 여백 2px 로 그릴 자리 190 x 74, 한 행 10.6px.
- 오프스크린 PySide6 14항목(시각별 아이콘 수 · 크기 · 여백 복원 · 재재생 · 실시간 완료 후 정지) + 시각별 캡처 7장 눈 확인. #A00240

> [!summary] `A00220_BackupTool`(v01.16) · `A00240_PathTool`(v01.10) 에 **Help 메뉴**(공용 메뉴 바) + A00240 **Shrink** — 애니메이션은 계획서
- **요청**: 두 툴에 Help 메뉴(공통 기능 그대로). A00240 에도 Shrink - A00220 이 줄었을 때의 가로, 세로 절반. 줄어든 뒤 파일 트리가 자라나는 애니메이션 계획서.
- 공용 `JUN_mod_menuBar_qt_v01` 를 `setMenuBar` 로 — 레이아웃 인덱스가 안 바뀌어 A00220 Shrink(공룡을 index 1 로 옮김)와 안 부딪힌다. 줄어든 동안은 메뉴 바도 감춰 A00220 은 155px 그대로.
- A00220 줄었을 때 **350 x 155**(green_mid 실측) → A00240 **350 x 78**. 78px 에선 버튼 행 아래로 그릴 자리가 20px 뿐이라, 애니메이션 자리를 **버튼 옆**에 두어 172 x 56 확보.
- 계획서 `docs/plans/A00240_PathTool_shrink_animation_plan.md` — 7행을 56px 에 넣는 게 핵심 제약(한 행 8px). 줄었을 때만 여백 2px 로 한 행 10px · 7x9 픽셀 아이콘 추천, 확인 5가지.
- 오프스크린 PySide6: 두 툴 Help > Copy Tool Name 클립보드 · A00220 155px 유지 · A00240 350x78 ↔ 원래 크기. #A00220 #A00240

> [!summary] A00145 Attribute > **Set Value** 하위 탭(v01.51) — 옛 Number Tool 이식: 여러 오브젝트의 **공통** 어트리뷰트에 값을 한 번에, 종류별 입력칸
- **요청**: `JUN_PY_numberTool_V01_01` 은 실수 하나로만 넣어 enum 도 정수로 넣어야 했다 → 정수 · 실수 · 간격 점프 · enum 은 **텍스트로 골라서**, 그리고 A00145 Attribute 탭으로 이식.
- 목록은 **교집합**(모두가 가진 것), float/int/bool/enum 만, `Channel Box Only` 기본 ON. float/int = `Start` + `Step`(리스트 순서대로 누적) + `Repeat every N`, enum/bool = 콤보에서 **항목 이름** + 항목 Step(끝에서 처음으로). enum 은 이름으로 오브젝트마다 값을 다시 찾는다(`Off:Low=5:High` 처럼 값이 건너뛰어도 맞다).
- 적용 전 미리보기 표(현재 → 새 값, 건너뛸 이유), `Clamp to range`(마야는 범위 밖을 자르지 않고 에러), 키 걸린 plug 는 키 + setAttr, undo 한 번.
- 원본도 `JUN_PY_numberTool_V01_02.py` 로 새 버전(maya.cmds, 같은 기능). V01_01 은 그대로.
- mayapy 2024: core(enum 이름/간격 순환 · clamp · 키 · 잠김 건너뛰기 · 각도 단위) + Qt 오프스크린 탭(enum/int Repeat/float + undo) + V01_02 로직(UI 창 빼고) 통과. 마야 GUI 에서는 아직 안 눌러 봄. #A00145

> [!summary] 공용 다중 체크 동작 `MOD_checkList_qt_v01` 을 **4개 툴 6개 목록**으로 확대 — A00145 Create(v01.50) · A00290_V02 Mix Targets(v02.02) · A00275 By Weight(v01.28) · A00210 Scan/Folders(v01.31)
- **요청**: 방금 만든 공용 위젯으로 바꿀 수 있는 툴 교체.
- A00275 는 자체 eventFilter(56줄, 공용 동작의 원본)를 지우고 공용으로. A00290 Sources 는 한 번에 바뀐 행마다 라벨을 다시 써야 해서 helper 가 `checksChanged` 를 `itemChanged` 보다 **먼저** 쏘게 바꿨다.
- helper 수정: **비활성(회색) 행은 건너뛴다** — A00290 Targets 에서 소스로 잠긴 행이 고른 범위에 들어와도 체크되지 않는다(Qt 기본과 같다).
- 제외: 트리/표(A00210 미리보기 · A00275 Layer · A00420 · A00280), 옛 버전 A00290 V01.
- mayapy 2024 실제 클릭(A00145 Create 3 · Edit 14 · A00275 5 · A00290 9) + PySide6 오프스크린(A00210 3) 통과. #Framework #A00145 #A00290 #A00275 #A00210

> [!summary] `A00145_RigConnect` Attribute > Edit 에 **Shift/Ctrl 다중 선택 + 다중 체크** — 공용 동작 `Framework/qt/MOD_checkList_qt_v01` 신설 (v01.48 -> 01.49)
- **요청**: Edit 목록에서 Shift 클릭으로 다중 선택·다중 체크. 이 성질의 목록 UI 를 공용으로 만들지 판단.
- **판단: 공용으로 만든다. 단 새 위젯이 아니라 기존 `QListWidget` 에 붙이는 동작으로.** 체크박스 목록이 6개 툴에 있고, Qt 기본 처리는 체크박스 누르기가 선택을 한 행으로 풀어 다중 체크가 한 번밖에 안 된다(A00275 실측) - 툴마다 다시 짜면 같은 함정을 또 밟는다. 필터·라벨은 그대로 둔다.
- 고른 행의 체크박스(또는 Space) = 보이는 고른 행 전부, 선택 유지. 필터에 가려진 행은 안 바꾼다. `itemChanged` 는 한 번.
- mayapy 2024 실제 클릭 14항목 + PySide6 오프스크린 통과. #A00145 #Framework

> [!summary] `A00145_RigConnect` `Attribute > Create` 의 `Add` / `Edit` 로 **enum · string** 어트리뷰트도 정의해 만든다 (v01.47 -> 01.48)
- **요청**: Create 탭 Add 버튼으로 Enum, String 종류도 생성.
- enum: `Items`(`,` 또는 `:` 구분) + 항목 이름 콤보로 기본값. 저장은 **항목 번호** — 범위 밖 번호는 마야가 조용히 0 으로 만든다.
- string: `addAttr -dataType string` 뒤 `setAttr -type string` 으로 기본값(`addAttr` 은 문자열 기본값을 못 받는다). 키를 못 걸어 `Keyable` 체크가 **`Channel Box`** 로 바뀐다.
- core 는 직전 세션(컴퓨터 종료로 끊김)이 미커밋으로 남긴 것을 이어받고 편집 창을 붙였다. 끊기기 전 커밋 4개(A00220 Shrink · A00400 Controls/Replace/Palette)도 mayapy 34항목 + UI 클릭 + 오프스크린으로 재진단, 이상 없음. #A00145

> [!summary] `A00400_CurveTool` `Create > Controls` 색에 **팔레트 팝업**(임의 RGB) — `ref_01.mel` 과 같은 `overrideRGBColors` 방식 (v01.16 -> 01.17)
- **요청**: `ref/ref_01.mel` 참고, 정해진 색이 아니라 팔레트에서 고른 색으로. 팔레트는 별도 팝업.
- `Color Palette...` + 마지막 색 견본(누르면 재적용). 코어 `set_color_rgb()` 는 ref 와 같은 어트리뷰트를 쓴다.
- **인덱스 색과 임의 색은 `overrideRGBColors` 스위치로 갈린다** — 넣을 때마다 맞춰 주지 않으면 값만 들어가고 화면 색은 그대로다. Reset 도 함께 되돌린다.
- 팔레트는 마야 `colorEditor` 대신 Qt 팔레트(PySide 창이라 부모·테마가 맞물린다). mayapy 2024 16항목 통과. #A00400

> [!summary] `A00400_CurveTool` 셰이프 교체를 **`Display > Replace`** 하위 탭으로 분리 — 두 칸을 **TSL** 로, 개수가 다르면 **적은 쪽만큼** 1:1 (v01.15 -> 01.16)
- **요청**: Control 탭의 Shape Replace 를 잘라 Display 하위 탭 `Replace` 로 이식, `Shapes to replace` · `Replacement` 를 TSL 로, 두 리스트 개수가 같으면 1:1 · 다르면 더 작은 개수만큼.
- TSL 이라 Add/Del/Up/Down 으로 순서를 손보며 여러 번 돌릴 수 있다. 교체본이 하나면 전부에, 여럿이면 순서대로 1:1, 개수가 다르면 `min` 쌍만 하고 몇 쌍인지 로그.
- Display 설명을 "형상 불변" → "어떻게 보이는지(굵기 · 컨트롤의 셰이프)" 로 고쳤다 — Replace 는 셰이프를 바꾸지만 사용자는 "어떤 모양으로 보이게 할까" 로 찾는다.
- mayapy 2024 13항목 통과. #A00400

> [!summary] `A00400_CurveTool` **`Create > Controls`** 신규 — `bs_controls` 이식(컨트롤러 커브 34종 · 색 · 셰이프 교체), 셰이프 데이터는 **Framework 공용**으로 (v01.14 -> 01.15)
- **요청**: 마야 셸프에서 `bs_controlsUI` 로 쓰던 툴을 A00400 새 탭으로 이식. 이어서 **셰이프 CV 데이터를 특정 툴이 아닌 공용 데이터로** 관리.
- 데이터·로더를 `Framework/rules/control_shapes.json` + `Framework.core.control_shapes` 로 승격(`mirror_tokens` 와 같은 자리). 릴리스는 툴+Framework 를 복사하므로 어느 툴에서 써도 따라간다.
- 탭은 원본 창처럼 세 섹션(Create / Color / Shape Replace). 원본과 달리 `cmds.error` 대신 로그 경고, 버튼 한 번 = undo 한 스텝, 색 바꿔도 선택 유지, `matchTransform` 사용.
- 실측: 좌표를 6자리로 반올림하면 8개 셰이프가 원본과 `1e-5` 어긋난다 → 원본 값 그대로 저장. 셰이프 없는 노드에서 원본 `Reset Color` 는 `UnboundLocalError` 로 죽는다.
- mayapy 2024 33항목 통과(34종 전부 원본과 CV 단위 일치 포함). #A00400 #Framework

> [!summary] `A00220_BackupTool` 에 **`Shrink` 토글** — 공룡만 남기고 창 세로를 788 → 155px 로 (v01.14 -> 01.15)
- **요청**: `Pinned` 버튼 옆에 `Shrink` 토글. 누르면 공룡 애니메이션만 보이고 `Shrink` · `Pin` 말고 다른 버튼은 안 보이게.
- 공룡이 `Control` 그룹 안에 있어 그룹을 숨기면 같이 사라진다 → 줄이는 동안 공룡을 **창 레이아웃으로 옮겼다가** 되돌린다(이동이라 애니메이션이 끊기지 않는다).
- 다시 누르면 줄이기 전 높이로 복귀, 접어 둔 `Settings` 는 접힌 채. 백업은 줄여 둔 채로도 계속 돈다.
- 오프스크린 PySide6 21항목 통과 + 실제 폰트 캡처로 확인. #A00220

---

## 2026-09-17

> [!summary] `A00130_ControlRig_V02` Match 표 **행 더블클릭 → 그 Cage set 을 마야에서 선택** (v02.22 -> 02.23)
- **요청**: 리스트업된 Cage set 줄을 더블클릭하면 해당 set 이 마야 씬에서 선택되도록.
- 세트 노드 자체를 `noExpand=True` 로(그냥 select 는 멤버로 펼친다), 누르는 순간 네임스페이스로 다시 찾는다. 없으면 선택 유지 + 경고.
- mayapy 2024 6항목 통과(실제 클릭 이벤트). #A00130

> [!summary] `A00130_ControlRig_V02` Length 탭 **`Total` 기본값을 `sum`** 으로, 콤보 맨 위로 (v02.21 -> 02.22)
- **요청**: Length 의 Total 기본 세팅이 sum 이 되고 sum 위치도 맨 위로.
- `length_map.json` `total_mode: "sum"` + 폴백 `TOTAL_DEFAULT = sum`, 콤보 순서는 `TOTAL_MODES` 한 곳. `straight` 는 그대로 고를 수 있다.
- mayapy 2024 8항목 통과(굽은 체인 3+4 에서 total 7). #A00130

> [!summary] `A00130_ControlRig_V02` Match 탭 **`Check Position`** — 케이지 세트마다 멤버들이 같은 월드 위치·회전인지 Status 에 초록 OK / 빨강으로 (v02.20 -> 02.21)
- **요청**: 각 Cage set 에 있는 오브젝트들이 모두 월드 기준 같은 위치·회전인지 진단해 Status 에, OK 는 초록 · 아니면 빨강.
- 기준은 첫 멤버. 위치는 **월드 rotate pivot**(Match 와 같은 기준), 회전은 **쿼터니언 각도**라 rotateOrder · 360° 차이는 같다고 본다. 빨강에는 어느 멤버가 얼마나 다른지.
- 실측: 컴포넌트 멤버는 `xform` 이 오브젝트 행렬을 조용히 돌려줘 OK 로 오판 → 이름으로 먼저 거른다. 비균등 스케일 부모의 shear 는 matchTransform 도 못 맞춘다(15.14°, 진짜 불일치).
- mayapy 2024 22항목 통과, 씬 불변. #A00130

> [!summary] `A00145_RigConnect` Constrain > Constraint — 종류를 **체크박스**로, `Parent` + `Scale` · `Point`/`Orient`/`Scale` 2~3개를 한 번에 (v01.46 -> 01.47)
- **요청**: Parent 와 Scale 을 동시에, Scale · Point · Orient 중 2개 · 3개를 동시에 체크해 한 번에 constraint 세팅.
- 규칙은 **구동 채널이 겹치지 않는 것**(실측: Parent → Point / Orient 는 `already connected`). 겹치는 것을 체크하면 먼저 켜진 쪽이 꺼지고, `Point On Poly` 는 혼자.
- 한 follower 에서 한 종류가 실패해도 나머지는 계속 걸고 `[WARN]` 으로 남긴다. 종류별 개수 로그, Undo 한 번.
- 실측 곁가지: 이미 `pointConstraint` 가 있는 곳에 `parentConstraint` 를 걸면 에러 없이 **`pairBlend`** 가 끼어든다(가이드에 주의 추가).
- mayapy 2024 37항목 통과. #A00145

> [!summary] `A00130_ControlRig_V02` **`Match` 를 한 번만 누르면 된다** — 부모부터 맞추고, 다른 매칭에 밀려난 것은 다시 맞춘다 (v02.19 -> 02.20)
- **보고**: `obj_01 > obj_02 > obj_03 > obj_04` 에서 obj_03 을 맞춘 뒤 obj_01 을 옮기면 obj_03 이 어긋나서 Match 를 여러 번 눌렀다. 원인은 매칭을 매핑 표 순서대로 돌린 것(실측: 목표 `(3,7,-4)` → `(8.87,12,-3.96)`).
- **계층 깊이 순**(같은 깊이는 표 순서)으로 맞추고, 계층이 아닌 연결(컨스트레인트로 따라가는 그룹 등)은 한 바퀴 뒤 **월드 행렬을 비교해 밀려난 것만 다시** 맞춘다(최대 5바퀴, 순환이면 경고).
- mayapy 2024 13항목 통과 — **같은 테스트가 수정 전 코드에선 5항목 실패**. 잠금 판정 · IK 세션 · undo 한 스텝 유지. #A00130

> [!summary] Framework 공용 로그창 `JUN_mod_log_qt_v01` 에 **`Shrink`** 토글 — 누르면 로그가 사라지고 창이 그만큼 짧아지며, 다시 누르면 돌아온다
- **요청**: 공용 로그 위젯에 Shrink 버튼 — 누르면 로그창이 사라지고 다시 클릭하면 나타나는 토글.
- 버튼 순서 `Expand · Shrink · Clear · Copy`, 접히면 라벨 `Show`. **툴 코드 수정 없이 50곳 전부에 붙는다.**
- 숨기기만으로는 자리가 안 빈다(컨테이너 min/max) → 컨테이너 제약을 담아 두고 버튼 줄 높이로, 최상위 창도 줄인 만큼 줄였다가 **실제로 줄인 만큼만** 되돌린다.
- 잡은 함정: 제약을 되돌린 **뒤에** 창 높이를 재면 Qt 가 먼저 키운 것에 또 더해진다(600 → 692) · `self.layout` 속성이 `layout()` 을 가리는 툴(A00004).
- 위젯 28항목 + 툴 50곳 스모크 48/50(나머지 둘은 기존 import 문제, A00004 는 경로 보정 후 통과).

> [!summary] `A00330_NamingTool` 상위 탭 **`Rename`**(Token / Set Rename) — **Token** 탭은 칸 수 자유 토큰(`Custom` / `Numbering`) + **Profile**(json) (v01.06 -> 01.08)
- **요청**: Naming Dyn 을 Token 으로 바꿔 Set Rename 과 함께 Rename 탭의 하위 탭으로. 칸마다 규칙 콤보, Add/Delete Token 으로 원하는 자리에 칸 추가·삭제 + 가로 스크롤, 규칙을 A00145 Attribute > Create 처럼 프로파일로.
- **Numbering 개수 = 세는 대상**: 1 개 = 전체 순번, 2 개 = 오브젝트 / 오브젝트 안 노드(레거시 Index1 / Index2), 3 개 이상은 실행 안 함. 처음엔 레거시 규칙 `Default`(`dyn_asset_side_{번호}_{번호}`, Pad 2).
- 마야는 `01_a` 를 **조용히 `_a`** 로 만든다(실측) → Custom 은 영문·숫자·`_` 만, 숫자로 시작하는 이름은 실행 전에 막는다. `Preview` 줄로 미리 본다.
- mayapy 2024 61항목 통과 — `Default` 결과 = 레거시 `rename_dynamics`, 프로파일 전 흐름, 칸이 늘어도 창 최소 폭 불변. #A00330
- **v01.08** — 토큰 칸 폭 2/3(120 → 80px). 실제 폰트로 재니 `Numbering` 콤보 89px · `Start`+스핀 한 줄 107px 이라, 콤보 여백을 줄이고 라벨을 스핀박스 위로.

> [!summary] **`A00480_FileTool` 신규** — `A00040_file_exporter_V02` 와 quickTool 의 File · Import option 버튼을 **Export / Import / Path** 탭 한 창으로 (v01.00 -> 01.02)
- **요청**: 파일 임포트 · 익스포트 · 경로 설정/조작을 모아 계속 늘려 갈 툴. 이름은 `FileTool`, 원본 두 툴과 quickTool 버튼은 **보존**.
- **Export** 탭은 A00040_V02 화면 그대로 + Export Path 옆 **`Scene`**(씬 폴더를 바로 채움). FBX 플러그인이 없으면 트레이스백 대신 `[FAIL]` 로그.
- Paste 경로 정리를 UI 에서 `core.normalize_pasted_path` 로, 자체 `undo_chunk` 복제를 공용 `Framework.core.maya_undo` 로.
- mayapy 2024 54항목 통과 — 옵션 4조합에서 원본과 **파일 목록 · FBX 재임포트 계층 · 결과 로그가 동일**, 익스포트 후 씬 불변.
- **v01.01** — 창이 약 1290 x 890 으로 크게 뜨던 것을 원본 A00040_V02 와 같은 **960 x 853** 으로. 테마가 자식에 입혀지기 전에 크기를 재던 것이 원인 → show 다음 루프에서 최소 크기로 fit, 탭 테두리만큼 여백 상쇄.
- **v01.02** — 22px 로 줄인 Pin 버튼 글자가 테마 padding(8px)에 잘리던 것을, 크기는 그대로 두고 이 버튼만 위아래 padding 0 으로.
- 계획서 [`plans/A00480_FileTool_merge_plan.md`](plans/A00480_FileTool_merge_plan.md) · 가이드 [`A00480_FileTool.md`](A00480_FileTool.md). #A00480

> [!summary] `A00400_CurveTool` **`Edit > Joints`** 가 **NURBS surface** 도 받는다 — U / V 방향 한 줄로 조인트 + 바인드 + zro/con/ctl/tgt (v01.13 -> 01.14)
- **요청**: Joints 탭에서 커브뿐 아니라 nurbs surface 도 원하는 간격마다 조인트 · 바인드 · 스택 구조를 만들고, U 또는 V 방향을 고를 수 있게.
- **`Surface Direction`(U/V)** + **`Across`**(반대 방향 위치 0~1, 기본 가운데 줄). 커브와 서피스를 한 리스트에 섞어도 된다.
- By length 는 줄을 촘촘히 찍은 꺾은선 길이로 역보간, 닫힌 방향은 마지막 자리를 뺀다. Aim 은 X = 줄 접선, Y = 서피스 노멀(`Z = X × N` 직교화).
- mayapy 2024 22항목 통과 — 커브 기존 결과(0, 5.5, 11) 그대로, UI 생성이 undo 한 번에 사라짐.

> [!summary] `A00030_quickTool_V02` **`File > Open Scene Folder`** 신규 — 현재 씬이 저장된 폴더를 탐색기로 연다 (v02.02 -> 02.03)
- **요청**: File 칸에 Open Scene Folder 버튼 — 누르면 마야 씬이 저장된 폴더가 탐색기로 열리도록.
- 씬 파일이 있으면 **파일을 선택한 채로** 연다(`Framework.core.file_opener.open_path`). 파일이 없으면 폴더만, 미저장·폴더 없음은 경고만.
- 로직은 `core.open_scene_folder()` 에, UI 는 `SECTIONS` 표 한 줄 + 핸들러. mayapy 2024 8항목 통과(탐색기 호출은 가로챔).

> [!summary] `A00275_skinTool_V01` **`Select > By Weight`** 신규 — 체크한 조인트의 웨이트가 Value 이상/이하인 버텍스를 메시 전체 또는 저장한 버텍스 안에서 선택 (v01.26 -> 01.27)
- **요청**: 스킨된 메시 M 의 바인드 조인트를 TSL 에 체크박스와 함께 올리고, [0, 1] 실수 i 를 받아 체크한 조인트에
  대해 웨이트가 i 이상/이하인 버텍스를 선택. M 전체에도, M 의 버텍스 일부만 골랐을 때 그 안에서도 동작. 새 탭 또는 하위 탭으로.
- 상위 탭 **`Select`** 를 새로 만들고 하위 탭 **`By Weight`** 에 넣었다 — 기존 세 카테고리(웨이트 이동 / 바인드 / 웨이트 불변 편집)
  어디에도 "씬을 안 바꾸고 고르기만" 은 맞지 않는다.
- **범위는 불러올 때 저장한다** — 결과를 고르면 선택이 결과로 바뀌고 조인트 행을 눌러도 조인트가 선택돼, 실행 시점 선택을 범위로 쓰면 Value 만 바꿔 다시 고르는 흐름이 깨진다.
- 여러 조인트 판정 `Any`(기본) / `All` / `Sum`, 경계값 포함(1e-6). 웨이트는 `getWeights` 한 번 — 19,802 버텍스 0.03초.
- 체크박스 클릭은 eventFilter 로 직접 처리 — 기본 처리는 체크 전파는 되지만 다중 선택을 한 행으로 풀었다(QTest 실측).
- 검증: mayapy 2024 + 오프스크린 Qt **43항목 통과** (결과를 `skinPercent` 로 센 답과 비교, 실제 마우스 클릭 포함).
  파일: `tools/A00275_skinTool_V01/app/core/weight_select_manager.py` · `app/ui/weight_select_tab.py` · `app/ui/main_window.py` ·
  `app/config/version.py` · `docs/A00275_skinTool_V01.md` `#A00275`

> [!summary] `A00240_PathTool` Tree 탭 — **Filter 로 검색해도 트리를 펼치지 않는다** (v01.08 -> 01.09)
- **요청**: Filter 로 검색하면 모든 트리가 펼쳐져 보인다 → 검색해도 펼쳐지지 않게.
- **원인**: `_mark_matches` 가 보이는 폴더마다 "자식 중 맞은 게 있으면" `setExpanded(True)` 를 했다. 필터는
  **전체 경로**로 맞추므로 폴더 이름(`charA`)을 치면 그 **아래 경로가 전부 맞은 것**이 되어, 결국 하위 트리가
  통째로 열렸다.
- **수정**: 필터는 **보이기/숨기기만** 하고 펼침은 건드리지 않는다. 걸러진 트리가 지금 접힘 상태 그대로 보이고,
  필요한 곳만 직접 연다(Shift + 펼치기 규칙은 그대로).
  - 필터를 **지울 때도 접지 않는다**(`fold=False`) — 예전의 "지우면 기본 접힘" 은 필터가 열어 놓은 것을 치우려던
    것이라 이제 필요 없고, 남겨 두면 검색 중 **직접 열어 둔 폴더**가 닫힌다. Build / Depth / Show files 는 예전처럼 접고 시작.
- **검증(PySide6 오프스크린 + 임시 폴더) 17항목 전부 통과**, **같은 테스트를 수정 전 코드에 돌리면 7개 실패**
  (증상을 실제로 잡는 테스트) — 검색 후 펼침 0 · 폴더 이름 검색 · 걸러짐 · 검색 중 직접 연 폴더 유지 ·
  지워도 유지 · Build/Show files 토글 · Refresh 유지 · Shift 재귀 펼치기.
  파일: `tools/A00240_PathTool/app/ui/tree_tab.py` · `app/config/version.py` · `CHANGELOG.md` ·
  `docs/A00240_PathTool.md` `#A00240`

> [!summary] `A00145_RigConnect` Attribute > Edit — **`Maintain connections`**(기본 ON) : 순서를 바꿔도 연결은 이름 그대로 (v01.45 -> 01.46)
- **요청**: `obj_02` 의 `attr_02_a` / `attr_02_b` 순서를 바꾸면 연결이 **자리 기준으로 엇갈린다**
  (`attr_01_a -> attr_02_b`). 원래 이름끼리(`attr_01_a -> attr_02_a`) 유지되게, 기본 체크된 체크박스로.
- **★ 재현이 안 됐다.** mayapy 에서 core 직접 · `undo_chunk` 안 · DG/병렬 평가 · double/float/enum/bool/long ·
  잠금 · 여러 오브젝트 동시 · 키 · multi · blendShape 구동 등 **17가지**, 그리고 **별도로 띄운 마야 GUI(2024,
  병렬 평가)에서 실제 툴 핸들러(`on_aedit_move`)** 로도 돌렸는데 **이름 · API 연결(`MPlug.connectedTo`) ·
  실제 값 흐름이 모두 유지**됐다. Node Editor 는 순서를 바꿔도 행을 옛 순서(A·B·C)로 그려 채널 박스와
  다르게 보인다는 점만 확인했다.
- 그래서 원인을 고치는 대신 **결과를 보장**하도록 만들었다 — 옮기기 **전** 연결을 플러그 이름으로 적고,
  옮긴 **뒤** 비교해 **어긋난 것만** `connectAttr -force` 로 되돌리고 낯선 연결은 끊는다. 어긋난 게 없으면
  **재연결 0회**(씬을 안 건드림). 로그: `Maintain connections : all N connection(s) kept.` /
  `[OK] ... fixed N connection(s)`.
  - `unitConversion` 은 `skipConversionNodes=True` 로 **실제 양 끝**을 비교 — 변환 노드 이름이 바뀌어도
    멀쩡한 연결을 끊지 않는다. 끊을 때는 받는 쪽에 **직접** 붙은 플러그를 찾는다.
  - 여러 오브젝트는 **전부 적고 → 전부 옮기고 → 전부 확인** (서로 연결된 둘을 함께 옮길 때 대비).
- 체크박스는 `Up`/`Down` 줄 **아래 한 줄**(같은 줄에 두면 오른쪽 열이 넓어진다).
- **검증(mayapy 2024 + 오프스크린 Qt) 36항목 전부 통과** — 증상은 옮긴 직후 연결을 **일부러 엇갈리게**
  만들어 흉내 냈다: 사용자 시나리오 복구 + 값 흐름 · OFF 면 그대로 · 멀쩡하면 connect/disconnect 0회 ·
  잠긴 dst · unitConversion(복구/무변화) · 나가는 연결 · 서로 연결된 두 오브젝트 동시 · 키 커브 · multi 원소 ·
  낯선 연결 제거 · 소스가 사라진 경우 경고 · 이미 맨 위 · UI 기본 체크/ON·OFF 전달. 기존 17가지 변형 회귀 없음.
- **그 과정에서 본 기존 결함 둘(이번에 안 고침)**: ① **컴파운드**(`double3`) 는 자식까지 목록에 올라와
  자식 `deleteAttr` 에서 멈추는데, 그 전까지 **순서가 반쯤 바뀐 채** 남는다 ② **alias** 가 붙은 어트리뷰트는
  `listAttr -ud` 가 alias 이름을 돌려줘 "not user defined" 로 못 옮긴다.
  파일: `tools/A00145_RigConnect/app/core/attr_order_manager.py` · `app/ui/main_window.py` ·
  `app/config/version.py` · `docs/A00145_RigConnect.md` `#A00145`

> [!summary] **A00400 `Edit > Combine` 기본 배치 변경** — Source 를 Target 월드 위치(rotate pivot)로 옮긴 모양으로 합친다 (v01.13)
- **요청**: Combine Shapes 가 Source 커브 쉐입을 보이던 자리 그대로 붙이던 것을, Source 를 Target 월드 위치로 이동한 뒤의 모양으로.
- `Keep world position` 체크박스를 **`Placement` 라디오 3 개**로 교체 — `Move to Target position`(기본) / `Keep Source world position` / `Keep local CV values`.
- 기준은 `matchTransform -pos` 와 같은 **rotate pivot** (mayapy 실측). 회전·스케일은 Source 것 유지.
- 검증: mayapy 2024 + 오프스크린 Qt 12항목 통과 (결과 == 복제본에 `matchTransform -pos` 한 모양).

> [!summary] **공용 메뉴 바 `JUN_mod_menuBar_qt_v01` 신규** — 모든 툴 `Help` 메뉴에 **`Copy Tool Name`**(툴 폴더 이름을 클립보드로). PySide 툴 42곳 + maya.cmds 툴 7곳
- **요청**: 각 툴 창 위 `Help` 메뉴에 `Copy Tool Name` — 누르면 그 툴 코드가 있는 폴더 이름(예: `A00060_jointTool_V03`)을
  클립보드로. 앞으로 **모든 툴 공통 항목이나 다른 메뉴가 늘어날 수 있으니** 그 성질이면 공용 위젯으로 만들고 Help 도 그걸 쓰게.
- **공용으로 만들었다 — 세 조각.** ① `Framework/core/tool_menu.py` : 공통 항목 **레지스트리**(`COMMON_MENUS`) +
  툴 이름 판정 + 동작(maya/Qt 비의존) ② `Framework/qt/MOD_menuBar_qt_v01.py` : `QMenuBar` 대체 위젯
  ③ `Framework/ui/MOD_menu_v01.py` : maya.cmds 메뉴용 함수. **두 UI 계열이 같은 목록을 읽어서**, 앞으로
  항목 추가는 레지스트리 **한 줄**이면 49툴 전부에 생긴다(새 메뉴 제목이면 그 메뉴가 생긴다).
- **드롭인 교체** — PySide 툴은 전부 `self.menu_bar = QMenuBar()` → `addMenu("Help")` 모양이었다.
  `addMenu("제목")` 을 **"있으면 돌려주고 없으면 만든다"** 로 바꿔, 툴은 **생성 한 줄**만 바뀌고 `About` 등
  기존 항목은 그대로 붙는다. cmds 툴은 `About` 다음에 `JUN_mod_menu.add_common_items('Help', tool_file=__file__)` 한 줄.
- 공통 항목은 **메뉴가 열릴 때(`aboutToShow`) 구분선과 함께 맨 아래로** 옮긴다(생성자에서 먼저 들어가서
  그냥 두면 About 가 그 아래에 붙는다). 툴이 새로 만든 메뉴는 **Help 왼쪽**에 끼운다 — `A00180` 은 `Operations | Help`.
- 툴 이름은 `__file__` 에서 **부모가 `tools` 인 폴더**, 없으면 `app` 을 담은 폴더. 결과는 창 안 공용 로그창에
  `[Copy Tool Name] Copied to clipboard : <name>`, 로그창이 없으면 print. 못 찾으면 클립보드를 건드리지 않는다.
- **★ PySide2 에서 `QAction.menu()` 가 메뉴를 지웠다.** 처음엔 기존 메뉴를 `action.menu()` 로 찾았는데, 이
  서브클래스에서 한 번 부르자 곧바로 `Internal C++ object (QMenu) already deleted`. 메뉴를 **만들 때 파이썬 목록에
  기억**하고 `menu()` 를 쓰지 않도록 바꿨다.
- **검증(mayapy 2024 + 오프스크린 Qt)** — 위젯 **28항목** · PySide 툴 **42곳 전수 스모크 42/42**(실제 MainWindow
  생성 → Help 맨 오른쪽 하나 · 기존 항목 유지 · 맨 아래 Copy Tool Name · 클립보드 = 폴더명 · 로그 기록) ·
  cmds 헬퍼 5항목 + 7개 파일 컴파일. **cmds 메뉴 실물은 standalone 에 UI 가 없어 마야 GUI 확인이 남았다.**
- 42툴 `version.py` +0.01. 메뉴 바가 없는 창(템플릿 2개 · `A00090` · `A00210` · `A00240` 등 15곳)은 대상이 아니다.
  파일: `Framework/core/tool_menu.py`(신규) · `Framework/qt/MOD_menuBar_qt_v01.py`(신규) · `Framework/ui/MOD_menu_v01.py`(신규) ·
  `Framework/qt/__init__.py` · `Framework/ui/__init__.py` · `tools/*/app/ui/main_window.py` 42 · cmds 툴 7 ·
  [`docs/Framework_MOD_menuBar_qt.md`](Framework_MOD_menuBar_qt.md)(신규) · `docs/portfolio/portfolio_EN.md` · `portfolio_KR.md`
    #Framework #menu #widget

> [!summary] `A00470_MaterialTool` — **`Copy Material`** 탭 추가 : 소스 메시 M(UUID 로 기억)의 면별 머티리얼을 M_i 에 똑같이 (v01.04 -> 01.05)
- **요청**: 메시 M 을 UUID 로 기억, TSL 에 M_i 를 담고, `Copy Material` 로 M 의 면마다 붙은 머티리얼을 M_i 의 같은 면에.
- 면별 배정은 `MFnMesh.getConnectedShaders` 로 읽는다(A00275 에서 확인한 방식). 머티리얼이 하나면 셰이프째,
  아니면 머티리얼마다 **연속 면 구간**으로 한 번씩 `forceElement`. **면 개수가 다르면 건너뛴다.**
- 적용 후 **되읽어 소스와 비교** — 다르면 성공으로 세지 않는다. 이 확인이 실제로 두 가지 함정을 잡았다:
  - **★ 면 하나를 `sets -remove` 해서는 안 비워진다** — 오브젝트째 배정이면 무시, 면별이면 `initialShadingGroup` 으로 되돌아감.
    → 비울 면이 있으면 대상 배정을 전부 걷어낸 뒤 다시 건다.
  - **★ 면별 배정을 걷어낸 메시에서 `getConnectedShaders` 는 세트에 없는 면을 `initialShadingGroup` 으로 보고한다.**
    → 비어야 할 면은 `listSets(object=face)` 멤버십으로 재확인.
- **검증(mayapy + 오프스크린 Qt) 24항목 전부 통과** — UUID(이름·부모 변경) · 단일 Undo · 면 수 불일치 · 빈 면 3종 ·
  네임스페이스 SG · 셰이프 2개 · 4만 면 체커보드 1.15초 · UI.
  파일: `tools/A00470_MaterialTool/app/core/material_copy.py`(신규) · `app/ui/copy_material_tab.py`(신규) ·
  `app/ui/main_window.py` · `app/config/version.py` · `docs/A00470_MaterialTool.md` `#A00470`

> [!summary] `A00145_RigConnect` Attribute — **`Copy`+`Delete` 를 `Edit` 한 탭으로** 합치고 **어트리뷰트 순서 바꾸기(`Up`/`Down`)** 추가 (v01.43 -> 01.44)
- **요청**: 체크박스로 고른 어트리뷰트를 `Up` / `Down` 으로 옮겨 **씬의 실제 어트리뷰트 순서**를 바꾼다.
  새 탭 `Move` 대신 **기존 탭을 묶는 개념의 탭**으로. (결정: 탭 이름 `Edit`, `Create` 는 합치지 않는다)
- **★ 마야에는 어트리뷰트를 재정렬하는 명령이 없다.** `addAttr` 에도 `attributeQuery` 에도 순서 플래그가
  없다. 유일한 방법이 **`deleteAttr` → `undo`** — 지웠다 되돌리면 그 어트리뷰트가 **목록 맨 뒤로** 간다.
  원하는 순서대로 한 바퀴 돌리면 결과가 정확히 그 순서다. mayapy 실측: **200개 전체 재정렬 0.004초**,
  **값 · 커넥션 · 키 전부 유지**(undo 가 원래 상태를 되돌리는 것이라 다시 이어 줄 필요가 없다).
- **★ 그 방식이 가진 위험 셋을 전부 실측으로 확인하고 막았다.**
  ① **`deleteAttr` 이 실패한 자리에서 `undo()` 를 부르면 남의 작업이 되돌아간다** — 실측에서 사용자가
  만든 노드가 사라졌다. → **성공했을 때만** undo 를 부른다.
  ② **undo 가 꺼져 있으면 어트리뷰트를 그대로 잃는다** → 시작 전에 `undoInfo -q -state` 를 보고 거부한다.
  ③ **이 작업 자체는 `Ctrl+Z` 로 안 돌아간다**(delete+undo 가 짝이라 큐에 아무것도 안 남고, 오히려 **그
  전에 하던 작업**이 취소된다) → 실행할 때마다 로그가
  `Reorder cannot be undone with Ctrl+Z` 라고 알리고 문서에도 적었다.
- **탭을 합친 이유**: `Copy` 와 `Delete` 는 화면이 이미 같았다 — 오브젝트를 담고 → 나열하고 → 고른 것에
  무언가를 한다. 다른 건 **마지막 버튼 하나**뿐인데 목록은 두 벌을 따로 채웠다. 순서 바꾸기도 성격이
  같아서, `Move` 를 더 만들면 같은 나열을 **세 번** 하게 된다. `Create` 는 씬을 읽지 않고 **저장된
  프로파일**로 만드는 작업이라 합치지 않았다.
- **고르는 방법이 선택 → 체크박스로** 바뀌었다. 필터를 바꿔도 체크가 남아 `arm`, `leg` 를 번갈아 걸러
  **여러 번에 걸쳐 모을 수 있다.** 목록은 **이름순 정렬을 하지 않는다** — 보이는 순서가 곧 채널 박스
  순서이고 `Up`/`Down` 이 바꾸는 것이 그것이라, 정렬하면 화면과 씬이 어긋난다.
- **`Include attributes hidden by the filter`**(기본 **OFF**): 가려진 체크를 대상에 넣을지. 끄면 "보이는
  것이 작업 대상", 켜면 가려진 것까지. **어느 쪽이든 몇 개가 가려졌는지 로그로 말한다** — 뺐으면
  "고른 게 빠졌다", 넣었으면 "안 보이는 것까지 건드렸다" 를 모르고 지나가면 안 된다.
- 빌트인(`translate` 등)은 `deleteAttr` 대상이 아니라 **못 옮긴다** — 회색으로 표시하고, 체크돼 있으면
  이름을 짚어 경고한 뒤 **나머지만** 옮긴다(조용히 넘어가면 "왜 아무 일도 안 일어나지" 가 된다).
- **검증(mayapy + 오프스크린 Qt) 27항목 전부 통과** — 씬 순서 유지 · 체크/필터 상호작용 4 ·
  가림 경고 양방향 · 두 오브젝트 동시 재정렬 · 값 보존 · 끝에서 멈춤 · 되돌아오기 · 빌트인 거부 ·
  Copy prefix/값 · Delete · 빈 입력. core 단위 테스트 25항목도 통과.
  파일: `tools/A00145_RigConnect/app/core/attr_order_manager.py`(신규) · `app/core/attribute_manager.py`
  (`list_attributes_multi`) · `app/ui/main_window.py` · `app/config/version.py` ·
  `docs/A00145_RigConnect.md` `#A00145`

> [!summary] `A00400_CurveTool` — **`Edit > Combine`** 추가 : Source 커브 쉐입을 Target 커브에 합친다, 인스턴스가 아닌 복사본으로 (v01.10 -> 01.11)
- **요청**: 좌 TSL 커브들의 쉐입을 우 TSL 커브에 합치기. 참고 MEL(`parent -s -add`)은 A 를 B 에 붙인 뒤
  A 를 지우면 B 에 붙은 쉐입도 사라지는 문제가 있다.
- **★ 원인 — `parent -s -add` 는 인스턴스다.** 노드 하나에 부모 둘(`allParents` → `['A','B']`).
  mayapy 로 지우는 방법별로 확인: **계층째 삭제 · 쉐입 경로 삭제 → B 쪽도 삭제**, 트랜스폼만 삭제 → 남음.
  지우지 않아도 A 의 CV 편집이 B 에 그대로 보인다.
- **해결**: `duplicate`(upstream 없음) → 새 쉐입을 `parent -r -s` 로 **이동** → 임시 트랜스폼 삭제.
  **Keep world position**(기본 켬)으로 CV 를 원래 월드 위치로 되돌린다(`-r -s` 는 로컬 값을 가져가 모양이 튄다).
  옵션 **Delete Source** (밑에 Target 이 있는 Source 는 보존). Target 1 개 = 전부, 여러 개 = 행 순서 1:1.
- **검증(mayapy + 오프스크린 Qt) 22항목 전부 통과** — 인스턴스 아님 · Source 계층 삭제/CV 편집에도 유지 ·
  회전+비균등 스케일+닫힌 커브 월드 위치 · 단일 undo · 히스토리/스킨된/멀티 쉐입 Source · 짝 짓기 · UI.
  파일: `tools/A00400_CurveTool/app/core/combine_manager.py`(신규) · `app/ui/main_window.py` ·
  `app/config/version.py` · `CHANGELOG.md` · `docs/A00400_CurveTool.md` `#A00400`

> [!summary] `A00330_NamingTool` Copy Name — **`Search` / `Replace`** 추가 : Base 이름 속 단어를 바꿔서 Targets 에 복사 (v01.04 -> 01.05)
- **요청**: Set Rename 탭의 Search / Replace 를 Copy Name 탭에도. Base 에 올라온 이름 중 Search 단어를
  Replace 단어로 바꿔 Targets 이름을 고친다(예: `L_arm_jnt` + `jnt`→`ctrl` = `L_arm_ctrl`).
- core 는 Set Rename 의 `replace_in_name` 을 그대로 재사용 — `copy_name(..., search, replace, case_sensitive)`.
  새 인자는 기본값이 있어 **Search 가 비면 기존 동작 그대로**.
- 치환은 **Base 이름에만**, `Prefix` / `Set suffix` 는 그 뒤에 붙는다. 결과가 **빈 이름**이면 건너뛰고 경고.
- **검증(mayapy + 오프스크린 Qt) 12항목 전부 통과**.
  파일: `tools/A00330_NamingTool/app/core/naming_ops.py` · `app/ui/main_window.py` · `app/config/version.py` ·
  `CHANGELOG.md` · `docs/A00330_NamingTool.md` `#A00330`

> [!summary] `A00030_quickTool_V02` — **`Shelf > Update Shelves`** 추가 : 셸프를 지금 디스크에 써서 새로 뜨는 마야가 바로 읽게 (v02.00 -> 02.01)
- **증상**: 셸프를 고쳐 놓고(툴의 `__dragDrop_*.py` 를 떨어뜨려 버튼이 생긴 것도 포함) **그 마야를 켠
  채 다른 마야를 새로 띄우면** 바뀐 것이 하나도 안 보인다. 고친 마야를 껐다 켜야 반영됐다.
- **★ 원인은 간단하다 — 마야는 셸프를 종료할 때 저장한다.** 그래서 디스크의 `prefs/shelves/shelf_*.mel`
  은 계속 옛 내용이고, 새로 뜨는 마야는 그걸 읽는다. 버튼은 그 저장을 **지금** 해 버린다
  (`saveAllShelves($gShelfTopLevel)`).
- **★ 그런데 `saveAllShelves("")` 는 빈 인자에도 조용히 성공한다**(mayapy 실측). 그대로 부르면
  헤드리스나 UI 가 없는 상황에서 **아무것도 안 쓰고 "됐다" 고 말하게 된다.** 그래서
  ① `$gShelfTopLevel` 과 탭 레이아웃으로 **UI 가 있는지 먼저 보고**
  ② 저장 **전후의 파일 수정 시각을 비교**해 실제로 쓰였는지 확인한다.
  하나도 안 바뀌었으면 성공이라 하지 않고 폴더가 쓰기 가능한지 보라고 경고한다.
- 로그에 **몇 개 중 몇 개가 쓰였는지 + 폴더 경로**를 적고, 일부만 쓰였으면 **어느 셸프가 빠졌는지**
  짚어 준다.
- **한계는 문서에 적었다** — 이미 떠 있는 다른 마야는 갱신되지 않고, **종료할 때 자기 상태로 덮어쓴다.**
  즉 **마지막에 종료하는 마야가 이긴다.**
- 버튼은 새 **`Shelf` 섹션**에 넣었다. `MainWindow.SECTIONS` 표에 한 줄 더한 것이 전부다
  (재작성 때 그렇게 설계해 둔 것이 값을 했다).
- **검증(mayapy + 오프스크린 Qt) 12항목 전부 통과** — UI 섹션·버튼·툴팁 3 · UI 없는 곳에서
  트레이스백 없이 경고 2 · **아무것도 안 썼을 때 잡아내기** 2 · 쓰인 개수 정확 보고 3 ·
  일부만 쓰인 경우 2(빠진 셸프 이름 포함) · MEL 실패 1. 기존 22항목도 다시 돌려 회귀 없음.
  파일: `tools/A00030_quickTool_V02/app/core/quick_ops.py` · `app/core/__init__.py` ·
  `app/ui/main_window.py` · `app/config/version.py` · `docs/A00030_quickTool_V02.md` `#A00030`

> [!summary] `A00310_SearchTool` Rules — 방향 규칙 **`No Upstream` · `No Downstream`** 추가 (v01.03 -> 01.04)
- **요청**: 리스트업된 오브젝트 중 **업스트림이 아무것도 연결되지 않은 것**, **다운스트림이 아무것도
  연결되지 않은 것**을 고르는 규칙 두 개.
- **★ 코드는 규칙 함수 둘 + 등록 두 줄이 전부다.** 어제 만든 레지스트리 설계가 의도대로 동작하는지
  확인된 셈이다 — UI 는 한 줄도 안 고쳤고, 목록·툴팁·설명줄·AND 조합·탈락 사유 로그가 전부 따라왔다.
- 공용 헬퍼 `_foreign_connections(own)` 에 **방향 인자**(`source` / `destination`)를 더해 갈랐다.
  `Standalone` 은 둘 다 True 로 예전과 같은 동작을 유지한다.
  - **No Upstream** : 들어오는 연결 0 — 나를 구동하는 것이 없다(노드망의 **시작점**).
  - **No Downstream** : 나가는 연결 0 — 내가 구동하는 것이 없다(노드망의 **끝점**).
  - 탈락 사유도 방향에 맞췄다 — `driven by ...` / `drives ...`.
- **무시 목록은 셋이 공유한다**(`IGNORED_TYPES`) — 머티리얼 배정 · 디스플레이 레이어 · 평범한 셋.
  부모-자식도 DG 연결이 아니라 세지 않는다.
- **`Standalone` 과 같지 않다** — 둘을 함께 골라도 `Standalone` 쪽이 더 엄격하다(**히스토리까지** 본다).
  예: `polyCube` 히스토리가 달린 메시는 연결이 없어도 `Standalone` 에서는 빠진다. 문서에 적어 두었다.
- **검증(mayapy + 오프스크린 Qt) 22항목 전부 통과** — 등록 순서 · 내보내기만/받기만/중간/무연결
  네 경우의 방향 판정 8 · 한 방향만 있을 때의 통과·탈락과 **사유 문구** 4 · 머티리얼·레이어·셋 무시 2 ·
  부모-자식 2 · 스킨 메시(Upstream 탈락)와 바인드 조인트(Downstream 탈락) 2 · AND 조합과
  `Standalone` 과의 포함 관계 2 · UI 자동 등록 2. 기존 A00310 구조 검증도 다시 돌려 회귀 없음.
  파일: `tools/A00310_SearchTool/app/core/select_rules.py` · `app/config/version.py` ·
  `docs/A00310_SearchTool.md` `#A00310`

---

## 2026-09-16

> [!summary] `A00240_PathTool` Tree 탭 — **Refresh**(Selected · Recursive), **갱신해도 열어 둔 경로가 닫히지 않는다** (v01.07 -> 01.08)
- **요청**: 디스크를 다시 읽어 갱신하는 `Refresh` 버튼. `Selected` 는 고른 경로만, `Recursive` 는
  하위 전부. **갱신 후 지금 UI 상태가 그대로 유지**되고 바뀐 부분만 변할 것. (Selected 는 늘 체크)
- **★ 이 기능의 핵심은 "다시 그리지 않는 것" 이 아니라 "상태를 잃지 않는 것" 이다.**
  항목을 다시 만들면 `QTreeWidgetItem` **객체가 바뀌어 펼침 상태가 날아간다.** 그래서 **경로로
  펼침·선택·스크롤을 적어 두었다가 다시 입힌다** — 없어진 경로는 자연히 빠지고, 남은 경로는 객체가
  바뀌어도 열린 채로 남는다.
- **★ 실제로 밟은 것 — 갱신 끝에 부른 필터가 트리를 도로 접었다.** `_apply_filter` 는 필터가 비어
  있으면 **기본 접힘으로 되돌리는** 동작을 갖고 있었다(어제 넣은 규칙). Refresh 가 그걸 그대로
  부르는 바람에 **갱신할 때마다 열어 둔 경로가 전부 닫혔다.** 필터에 `fold` 인자를 두어 새로 그릴
  때만 접고 Refresh 는 접지 않게 갈랐다.
- **★ Recursive 를 끄면 한 겹만 읽는데, 그 결과로 캐시를 덮어쓰면 안 된다.** 덮어쓰면 아래가 통째로
  사라져 **열어 두었던 폴더가 비어 보인다.** 합칠 때 **이미 아는 하위는 그대로 둔다.**
- Depth 를 넘어서까지 읽지 않는다 — 화면에 안 보이는 것을 캐시에만 쌓으면 Depth 를 줄였다 늘렸을 때
  결과가 달라진다. `Show files` · `File Types` · `Filter` 는 갱신 뒤에도 그대로 걸려 있다.
- `Selected` 는 **기본 켬**이다(요청). 켠 채 아무것도 안 골랐으면 아무 일도 하지 않고 무엇을 해야
  하는지 알려 준다 — 모르는 새 트리 전체를 다시 읽는 것보다 낫다.
- **검증(오프스크린 Qt) 19항목 전부 통과** — UI 3 · 전체 갱신에서 펼침/선택 유지와 새 항목 반영 3 ·
  Selected 가 고른 폴더만 건드림 2 · Recursive OFF 에서 한 겹만 읽고 **하위 캐시·펼침 유지** 4 ·
  Recursive ON 에서 깊은 곳 반영 + 펼침 유지 2 · 삭제 반영 2 · 선택 없을 때 안내 2 · 빌드 전 안전 1 ·
  필터가 걸린 채 갱신 1. 어제 넣은 Pin/필터/Shift 검증 25항목도 다시 돌려 회귀 없음.
  - **테스트 메모**: 오프스크린에서 **모달 `QMessageBox` 는 프로세스를 죽인다**(세그폴트). 안내가
    떴는지만 가로채 확인했다. 그리고 `MainWindow()` 를 변수에 안 담으면 C++ 객체가 먼저 죽어 역시
    세그폴트가 난다.
  파일: `tools/A00240_PathTool/app/ui/tree_tab.py` · `app/config/version.py` · `CHANGELOG.md` ·
  `docs/A00240_PathTool.md` `#A00240`

> [!summary] `docs` **README · 포트폴리오(EN/KR) 최신화** — 9월 중순 작업 반영
- `README.md` 갱신 이력 표에 **`2026-09 중순`** 3행 추가 — 공용 로그창 Framework 승격과 47곳 일괄 적용 ·
  `A00290_BSTool_V02` / `A00030_quickTool_V02` 신규 · `A00310_SearchTool` Rules 레지스트리 + `A00240_PathTool`
  Pin / 트리 필터 / Shift 펼치기.
- `portfolio_EN.md` / `portfolio_KR.md` 툴 표의 `A00290_BSTool` 행을 V02 재편에 맞춰 갱신.
  파일: `README.md` · `docs/portfolio/portfolio_EN.md` · `docs/portfolio/portfolio_KR.md` `#docs` `#portfolio`

> [!summary] `A00240_PathTool` — **Pin** · Tree 탭 **Filter** · **기본 접힘 + Shift 펼치기 규칙** · **Copy file path** · 아이콘을 UI 색으로 (v01.06 -> 01.07)
- **Pin** — 창 오른쪽 위 토글. 켜면 다른 창들 위에 고정된다(라벨 `Pinned`). standalone 앱이라
  마야가 아니라 OS 의 다른 창들 위에 선다.
- **Tree > Filter** — 이름이든 경로든 찾는다. **전체 경로로 매칭**하므로 파일 이름(`skin_color`) ·
  폴더 이름(`tex`) · 경로 조각(`charA/tex`) 이 전부 걸린다. 여러 단어는 **AND**.
  맞은 것의 **부모 폴더를 함께 보여 주고 맞은 곳까지 펼친다**(안 그러면 찾아 놓고도 못 닿는다).
  - **★ 구분자를 통일해야 한다** — 저장된 경로는 윈도우라 `\`, 사람은 `tex/deep` 처럼 `/` 로도 친다.
    양쪽을 `/` 로 맞추지 않으면 **같은 경로를 쳐도 안 걸린다**(테스트에서 실제로 밟았다).
  - 공용 위젯 `JUN_mod_filter_qt_v01` 은 **최상위 항목만** 거르는 구조라 이 트리(최상위 1개)에는
    맞지 않아 탭 안에 계층 필터를 따로 구현했다. 다른 툴에서 또 필요해지면 그때 공용으로 올린다.
- **★ Tree 펼치기 규칙** — 예전에는 `expandAll()` 이라 **최하위까지 전부 펼쳐진 채**로 나왔다.
  이제 Build·Depth 변경 모두 **루트만 펼치고 그 아래는 전부 접는다.**
  그냥 펼치기 = 한 단계 / **Shift+펼치기 = 아래 전부** / **Shift+접기 = 아래 전부 접힘** /
  Shift 로 접은 뒤 그냥 펼치면 다시 한 단계. **모든 깊이에서 동일.**
  - **왜 Shift+접기가 필요한가**: Qt 는 부모를 접어도 **자식의 펼침 상태를 기억**한다. 그래서 그냥
    접었다 펼치면 예전에 열려 있던 만큼 다시 열린다. Shift+접기가 그 기억을 지우는 방법이다.
  - **`setExpanded` 가 `itemExpanded` 를 다시 쏜다.** Shift 가 눌린 채라 핸들러가 또 불려 같은 일을
    반복한다 — `_bulk` 플래그로 한 번만 돌게 막고, 깊은 경로를 대비해 재귀 대신 명시적 스택을 쓴다.
- **우클릭 `Copy file path`** — 폴더든 파일이든 **절대 경로**를 클립보드로. OS 네이티브 모양이라
  탐색기 주소창에 바로 붙는다(`A00030_quickTool_V02` 의 Copy Scene Folder 와 같은 규칙).
- **아이콘을 UI 색에 맞췄다** — UI 는 `yellow_mid` 인데 아이콘만 **보라**(옛 테마 잔재)였다.
  도형은 그대로 두고 qss 팔레트(`#c8b86f` / `#e6d68f` / `#a09150`)로 다시 칠해 `.svg` → `.png` +
  **다중 크기 `.ico`(16~256px, 9종)** 를 다시 구웠다.
  - **★ `dev/build_icons.py` 는 전 툴의 PNG 를 다시 굽는다.** 돌리면 다른 툴 아이콘 14개가 함께
    변경됨으로 잡힌다(내용은 같아도 바이트가 달라진다) — **A00240 것만 남기고 되돌렸다.**
  - `.ico` 는 이 스크립트가 만들지 않는다. Qt 는 ico **쓰기**를 지원하지 않으므로, 크기별 PNG 를
    메모리에 렌더한 뒤 ICO 헤더/디렉터리에 **PNG 바이트를 그대로** 실어 직접 썼다(Vista 이후 허용).
- **검증(오프스크린 Qt) 25항목 전부 통과** — Pin 3 · 기본 접힘과 Depth 변경 후 접힘 · Shift 규칙 7
  (하위 경로 재귀 포함) · 필터 9(이름/부모 표시/가지 숨김/자동 펼침/개수/AND/경로 조각/지우면 복원) ·
  Copy file path 2(파일·폴더) · 아이콘 3(파일 존재 · ico 9종 · PNG 가 노랑 계열).
  파일: `tools/A00240_PathTool/app/ui/{main_window,tree_tab}.py` · `icon/*` ·
  `app/config/version.py` · `CHANGELOG.md` · `docs/A00240_PathTool.md` `#A00240`

> [!summary] `A00030_quickTool_V02` **신규** — 레거시 maya.cmds 퀵툴(V01.16)을 **PySide 로 재작성** (v02.00)
- **요청**: `A00030_quickTool_V02` 경로에 기존 퀵툴을 PySide 로 재작성. UI 는 현재 PySide 툴들의 관례를 따를 것.
- **기능은 하나도 안 바뀌었다** — 섹션 6 / 버튼 10 그대로(Update window · Print · Import option ·
  Create · File · Display). 바뀐 것은 그릇이다.
  - 결과가 `print`/`cmds.warning` → **창 안 공용 로그창**(Expand/Clear/Copy)으로. 스크립트
    에디터를 안 열어도 보인다. **코어는 로그 문자열 리스트를 돌려준다**(UI 비의존 · 테스트 가능).
  - 로직을 `app/core/quick_ops.py` 로 분리, UI 는 `app/ui/main_window.py`.
  - Pin 은 레거시가 창을 Qt 위젯으로 **감싸서** 하던 것을, 창이 Qt 라 바로 한다.
  - 색은 코드에 박힌 RGB → 공용 테마 qss(`slate_dark`).
  - **버튼 표 `MainWindow.SECTIONS` 한 줄이면 버튼이 는다** — 레거시는 인덱스 상수
    (`idx_updateWin`…`idx_display`)와 중첩 리스트를 짝맞춰야 했다.
- **★ 재작성하면서 하나 고쳤다 — FBX 버튼.** `FBXProperty` 는 MEL 기본 명령이 아니라
  **`fbxmaya` 플러그인이 등록하는 프로시저**다. 플러그인이 안 올라와 있으면 V01 은
  `Cannot find procedure "FBXProperty"` **트레이스백**으로 죽었다(mayapy 에서 실제로 재현됐다).
  V02 는 **플러그인을 먼저 올려 보고**, 그래도 안 되면 로그에 이유를 적는다.
- **V01 은 그대로 둔다** — 창·로그 확장창의 `objectName` 이 갈려 동시에 띄울 수 있다.
  셸프 라벨 `QuickToolV2`, 드롭 파일 `__dragDrop_A00030_V02.py`.
- **검증(mayapy + 오프스크린 Qt) 22항목 전부 통과** — 섹션·버튼 순서가 레거시와 동일 · 전 버튼 툴팁 ·
  `playbackOptions -view` 실제 변경 · 선택 없을 때 경고 · 조인트 3단 **계층 트리**와 중복 스킵 ·
  FBX 설정(트레이스백이 로그로 새지 않음) · `file`+`place2dTexture` 연결 · **선택 2개 → 클러스터 2개** ·
  미저장 씬 경고 · `displayLocalAxis` 실제 변경과 **컴포넌트 선택 시 부모 transform** · Pin 토글 ·
  `run()` 재실행 시 보이는 창 하나. 파일: `tools/A00030_quickTool_V02/**`(신규) ·
  `docs/A00030_quickTool_V02.md`(신규) `#A00030`

> [!summary] `A00040_file_exporter_V02` — Export Path 에 **`Paste` 버튼** 추가 (v02.07 -> 02.08)
- **요청**: `Browse` 옆에 Paste 버튼을 두고, 클립보드에 복사해 둔 경로를 바로 꽂게 해 달라.
  (원하는 경로를 복사한 뒤 대화상자를 거치지 않고 붙여넣기)
- **★ 사람이 복사해 오는 모양을 그대로 받게 했다.** 클립보드 글자를 그냥 넣으면 실제로는 잘 안 맞는다 —
  - 윈도우의 **`경로로 복사`**(Shift+우클릭)는 **따옴표로 감싸서** 준다 → 벗긴다.
  - 역슬래시를 이 툴이 쓰는 `/` 로 바꾼다(`Browse` 도 같은 처리를 한다).
  - 앞뒤 공백을 떼고, 여러 줄이 들어오면 **첫 줄**만 쓴다.
  - **파일 경로면 그 폴더**를 쓴다 — `경로로 복사` 는 대개 파일에 쓰는 기능이라 이 경우가 흔하다.
    바꿨다는 사실은 로그에 남긴다.
- **없는 경로여도 넣어는 준다** — 아직 안 만든 폴더나 지금 연결 안 된 네트워크 경로일 수 있다.
  대신 `[WARN] Pasted path does not exist yet` 을 남겨 Export 에서 실패하기 전에 눈에 띄게 했다
  (코어는 경로가 비었는지만 본다).
- **빈 클립보드는 기존 값을 건드리지 않는다.** 실수로 눌러 이미 잡아 둔 경로가 날아가지 않도록.
- 경로 칸은 그대로 **읽기 전용**이다 — 타이핑으로 오타가 들어갈 자리는 여전히 없다.
- **검증(mayapy + 오프스크린 Qt) 14항목 전부 통과** — 버튼이 Export Path 그룹 안에서 `Browse` 뒤에
  있고 툴팁이 있음 · 역슬래시/따옴표/공백/여러 줄/파일경로/따옴표+파일경로 6가지 붙여넣기 ·
  없는 경로는 넣되 경고 · 빈 클립보드와 공백뿐인 클립보드가 기존 값을 안 건드림 · 읽기 전용 유지.
  파일: `tools/A00040_file_exporter_V02/app/ui/main_window.py` · `app/config/version.py` ·
  `docs/A00040_file_exporter_V02.md` `#A00040`

> [!summary] `A00470_MaterialTool` — 머티리얼 이름 규칙 **`Basic_v001` 추가** (v01.03 -> 01.04)
- **요청**: `MT_MANU_CH_{character}_{part}_{extra...}` 규칙을 `Basic_v001` 로 추가.
  앞 네 자리(`MT` · `MANU` · `CH` · `character`)는 `Set_v001` 과 동일, **`part` 는
  `Body` / `Head` / `Eye` / `Tooth` / `Hair` 중 하나**, `extra` 는 기존대로 몇 개든.
- **★ 코드는 한 줄도 안 고쳤다.** 이 툴은 처음부터 **규칙이 코드가 아니라 데이터**라
  `data/profiles/<이름>.json` 한 장이 규칙 한 벌이다. 파일을 넣자 콤보에 저절로 나타나고
  패턴 라벨·진단·오타 제안이 전부 따라왔다 — 설계가 의도대로 동작하는 것을 확인한 셈이다.
- `Set_v001` 과 다른 것은 **`set` 자리가 없다**는 것과 **`part` 목록**뿐이다(세트 쪽은 의상 부위,
  이쪽은 신체 부위). 꼬리 숫자 규칙은 공통으로 적용된다.
- **콤보 기본 선택이 `Basic_v001` 로 바뀐다** — 목록이 이름순이라 그렇다(`Basic` < `Set`).
  고정 기본값이 필요하면 별도 요청으로 처리한다.
- **검증(mayapy, 마야 무의존) 22항목 전부 통과** — 프로필 목록·이름·패턴 · 통과해야 하는 이름 8종
  (부위 5종 · extra 0/1/다수 · `_01` 처럼 갈라진 숫자) · 걸러야 하는 이름 8종(목록 밖 부위 ·
  `Top`/`Pants` 같은 Set 쪽 부위 · part 누락 · character/category/prefix 오류 · 소문자 ·
  꼬리 숫자) · **오타 제안**(`Tooht`->`Tooth`, `Haer`->`Hair`) · **두 프로파일이 서로의 이름을
  통과시키지 않음**. UI 에서도 콤보에 자동 등록되고 패턴 라벨이 따라오는 것 확인.
  파일: `tools/A00470_MaterialTool/data/profiles/Basic_v001.json`(신규) ·
  `app/config/version.py` · `docs/A00470_MaterialTool.md` `#A00470`

> [!summary] `A00290_BSTool_V02` — 창 **가로를 1400 → 620 (2.26배 축소)**, 가로 스크롤 없음 (v02.00 후속)
- **요청**: 가로가 너무 길다, **두 배 이상 줄이고 가로 스크롤이 없게** 해 달라.
- **★ 1400 은 제가 테마 없이 잰 값이었다.** 테마 qss 가 `font-size: 12px` 를 주므로 위젯 최소 폭이
  확 줄어든다 — 가장 넓은 페이지 기준 **1092 → 809px**. **오프스크린으로 창 크기를 잴 때는 테마를
  입히고 재야 한다**(`ThemeManager.load_theme_to_widget`). 이걸 빼먹어 창이 과하게 커졌다.
- **★ 그래도 좁혀지지 않던 진짜 이유 — 한 줄에 나란히 둔 것들.** 버튼·라디오·라벨을 가로로 늘어놓으면
  **그 줄의 최소 폭이 그대로 창의 최소 폭**이 되고, **좌우 스플리터 안에 있으면 두 배로** 올라온다.
  기능·버튼·라벨은 하나도 바꾸지 않고 **자리만** 내렸다.

  | 페이지 | 내린 것 | 최소 폭 |
  |---|---|---:|
  | Mix Targets | 버튼 셋(`Set to Selected`·`Use Scene Weights`·`Uncheck All`)을 한 줄씩 · `Checked:`/`Number:` 라벨을 제 줄로 · `Base mesh` 라벨을 라디오 위로 | 1092 → **573** |
  | Naming | 모드 라디오 3개(`Set Name`/`Search & Replace`/`Prefix / Suffix`)를 2줄 그리드로 | 792 → **498** |

- **결과 620 x 1000** — **일곱 페이지 어디에도 가로 스크롤이 없다.** 상위 탭 바도 1221 → 276px.
- **★ 세로는 반대로 움직인다.** 좁히면 글이 접혀 **필요한 세로가 늘어난다**(Shape Editor 918 ·
  Naming 894 · Mix Targets 756). 세로까지 없애려면 창이 약 **1195px** 이어야 하는데 **1080p 모니터에
  안 들어간다.** 그래서 화면에 들어가는 높이(1000)를 택하고 그 세 페이지는 세로 스크롤이 받게 뒀다 —
  페이지를 `QScrollArea` 에 담아 둔 것이 그래서다. 모니터가 크면 `win_height` 한 줄만 올리면 된다.
- **검증 25항목 전부 통과**(테마를 입힌 상태로) — 탭 구성·매핑 · 대표 위젯 20개 생존 ·
  **기본 크기에서 가로 스크롤 0** · 폭이 이전의 절반 이하 · 탭 바가 창 폭 안 · 타이머 7항목 ·
  V01 과 objectName 분리. 파일: `tools/A00290_BSTool_V02/app/ui/main_window.py` ·
  `docs/A00290_BSTool_V02.md` · `CHANGELOG.md` `#A00290`

> [!summary] `A00290_BSTool_V02` **신규** — V01 을 복제해 **탭을 카테고리 3 / 기능 7 의 2단**으로 재편 (v02.00)
- **계획서**: [`plans/A00290_BSTool_tab_reorg_plan.md`](plans/A00290_BSTool_tab_reorg_plan.md) —
  분석 · 권장 구조 · 대안 기각 사유 · 위험을 먼저 적고 그대로 진행했다. 사용자가 정한 것:
  **`Default` → `Extract`**, **스크롤 영역 + 스크롤이 안 생기게 창 키우기**, **V02 폴더로 분리**.
- **★ 문제는 실측으로 못박고 시작했다.** 상위 탭 바가 필요로 하는 폭 **1221px** vs 쓸 수 있는 폭
  **1096px** — **이미 스크롤 화살표가 떠 있었다.** 그리고 6개 중 `Edit BS` 만 2단이었는데 그건
  분류가 아니라 v01.21 에 `Naming` 을 넣을 자리가 없어서였다. 그래서 **`Naming`(이름 바꾸기)이
  `Default`(타겟 꺼내기)와 한 상자에** 있었다 — 이 오분류를 푸는 것이 재편의 핵심이다.
- **새 구조** — 기준은 "무엇을 바꾸는가"다.
  **Shape**(모양이 바뀐다: Shape Editor · Base Shape · Mix Targets) ·
  **Target**(버텍스는 안 움직인다, 이름·인덱스만: Naming · Target Order) ·
  **Node**(노드/리그를 통째로: Extract · Bake Delete). 탭 바가 **1221 → 최대 636px**.
  `Shape Editor` 가 첫 카테고리의 첫 하위 탭이라 **툴을 켜면 V01 과 같은 화면**이 열린다.
- **`Edit BS > Default` → `Node > Extract`** — `Edit BS` 상자가 없어지면 `Default` 는 부모 없이는
  뜻이 없는 이름이 된다. 버튼 셋(Key every target · Copy every target · Copy every frame)이 전부
  **꺼내기**라 하는 일로 이름을 붙이고, 툴팁에 `(was Edit BS > Default)` 를 남겼다.
- **★ 계획서 8장의 위험이 실제였다 — weight 폴링 타이머.** V01 은 `tabs.currentIndex() ==
  SHAPE_EDITOR_TAB(0)` 으로 타이머를 켰다. 2단으로 묶으면 인덱스 0 이 **"Shape 카테고리"** 가 되어
  **Base Shape · Mix Targets 를 봐도 계속 돌고**, 카테고리 순서를 바꾸면 반대로 **영영 안 돈다.**
  **둘 다 에러가 나지 않는다.** `_shape_editor_visible()` 이 **위젯 동일성**으로 판단하게 바꾸고,
  **상위·하위 두 탭 위젯의 시그널을 모두** 받도록 했다(하위만 바뀌는 전환은 상위 시그널이 안 온다).
- **★ 스크롤 없는 창 크기는 폭만으로 안 됐다.** 폭을 넓히면 `Shape Editor` 가 필요로 하는 세로가
  **959 → 839px** 로 줄지만 **839 에서 바닥을 친다**(1400 을 넘겨도 더 안 줄어든다). 그래서 세로도
  키워야 했고, 일곱 페이지 어디에도 스크롤바가 없는 최소가 **1400 x 1158** 이다(1500·1700 으로
  넓혀도 필요한 세로는 1144 밑으로 안 내려간다). ※ **1158 은 1080p 모니터에 안 들어간다** — 그때는
  `Shape Editor` · `Naming` 에 세로 스크롤이 생긴다(스크롤 영역에 담아 둔 이유). 두 줄만 줄이면 된다.
  덤: V01 의 `win_width = 660` 은 **실현되지 않는 값**이었다(실제 최소 1118 x 925, `Mix Targets` 의
  최소 폭 1092px 이 혼자 정하고 있었다).
- **V01 은 한 글자도 안 건드렸다.** `app/core/*` 도 모듈 헤더의 툴 이름만 바뀌었고 로직은 복제 그대로다.
  기존 `_build_*_tab()` 일곱 개도 수정하지 않았다 — **묶기만** 했다.
- **동시 실행 대비**: 창 · 타겟 확장창 · **로그 확장창**의 `objectName` 이 전부 `_V02` 로 갈렸다
  (같으면 Expand 창이 서로를 찾아 닫는다). 셸프 라벨 `BSToolV2`, 드롭 파일 `__dragDrop_A00290_V02.py`.
- **검증(mayapy + 오프스크린 Qt) 24항목 전부 통과** — 탭 구성·매핑 · 옛 `tabs_edit_bs` 소멸 ·
  대표 위젯 20개가 스크롤 래핑 뒤에도 생존 · 7페이지 전부 스크롤 영역 · **기본 크기에서 스크롤바 0** ·
  탭 바가 창 폭 안 · **타이머 7항목**(Shape Editor 에서만 돌고 Expand 창이 뜨면 어느 탭이든 돈다) ·
  V01 과 objectName 분리. 로그 위젯 **48툴 전수 스모크**도 돌려 이전과 같은 47/48.
  파일: `tools/A00290_BSTool_V02/**`(신규) · `docs/A00290_BSTool_V02.md`(신규) ·
  `docs/plans/A00290_BSTool_tab_reorg_plan.md` `#A00290`

> [!summary] 공용 로그창 — **Expand 로 띄운 창을 세로로 늘려도 로그가 안 커지던 문제** (위젯 수정 · 로그창을 쓰는 전 툴 공통)
- **증상**: `Expand` 로 로그를 팝업으로 띄운 뒤 그 창의 세로 길이를 늘려도 **로그창 높이는 그대로**였다.
  남는 자리는 전부 빈 공간이 됐다.
- **★ 원인 — 툴 창에서 걸어 둔 높이 제약이 확장 창까지 따라갔다.** `setMaximumHeight(160)` 같은 값은
  **"툴 창 안에서 로그가 차지할 몫"** 이지 확장 창에서까지 지킬 값이 아니다. 그런데 그 제약이 텍스트에
  그대로 붙어 있어서, 팝업을 1200px 로 늘려도 로그는 **160px 에 묶여** 있었다(실측).
  **크게 보려고 누른 버튼인데 크게 안 보이는** 상태였다.
- `expand()` 가 지금 값을 담아 두고 풀어 준다(`min=0` · `max=QWIDGETSIZE_MAX`). `collapse()` 가
  담아 둔 값을 되돌리므로 **제자리로 돌아오면 다시 원래 몫만** 차지한다. 확장 중에 툴이 높이를 바꾸면
  (드물지만) 텍스트에 걸지 않고 **되돌릴 값만** 갱신한다.
- **검증(mayapy + 오프스크린 Qt) 15항목 전부 통과** — `A00275`(Max 160) · `A00170`(Fixed 120) 둘 다
  팝업을 520→800→1200px 로 늘리면 로그가 498→778→1178px 로 **창을 1:1 로 따라가고**(늘어난 680px 를
  그대로 가져간다), 닫고 돌아오면 제약이 정확히 복원되며 툴 창을 1400px 로 늘려도 다시 160 / 120px 만
  차지한다. 확장 중 높이 변경 · 확장/복귀 왕복의 내용 보존(확장 중 들어온 로그 포함)도 확인.
  로그창을 쓰는 **47툴 전수 스모크**도 다시 돌려 이전과 같은 46/47.
  파일: `Framework/qt/MOD_log_qt_v01.py` · `docs/Framework_MOD_log_qt.md` `#Framework`

> [!summary] `A00310_SearchTool` — **탭을 Type / Token / Rules 세 개로 평탄화**하고 **Objects 리스트를 셋이 공유**하도록 (v01.02 -> 01.03)
- **제안과 결정**: "Selection 도 Search 의 하위 탭 Type 으로 옮기는 것 어때?" 라는 물음에서 시작했다.
  묶는 것은 맞다 — 셋 다 **"Objects 리스트에서 조건에 맞는 것만 고른다"** 이고 다른 건 *무엇으로*
  고르느냐(**타입 / 이름 / 상태**)뿐이다. 다만 그대로 옮기면 **상위 탭이 `Search` 하나만 남아**
  탭 하나짜리 QTabWidget 이 된다. 그래서 **중첩을 걷어내고 셋을 최상위로** 올렸다(사용자 확인).
- **★ Objects 리스트·Get·Source·Invert 를 탭 바깥으로 빼 공유한다.** 전에는 탭마다 따로라
  Token 에서 Get 해 놓고 Rules 로 넘어가면 **리스트가 비어 있었다.** 같은 대상을 다른 기준으로
  고르는 것이 이 툴의 전부인데 대상을 탭마다 다시 모으는 것은 앞뒤가 맞지 않는다. 이제 **한 번 Get
  하면 어느 탭에서나** 쓰고, Invert 도 한 곳에서 켜면 세 탭에 다 걸린다.
- **기능은 하나도 빠지지 않았다** — 옛 Selection 탭의 내용(Types 리스트 · List Types ·
  Select By Shape 4버튼 · Select By Type)이 그대로 Type 탭이다.
- **`List Types` 는 이제 씬 선택이 아니라 Objects 리스트를 본다.** 다른 버튼들과 같은 대상을 보게 해
  화면의 목록과 타입 목록이 어긋나지 않도록 했다(그래서 먼저 Get 을 눌러야 한다).
- 이름 정리 — 공유하는 것은 접두사 없이(`objs_tsl` · `rb_hierarchy`/`rb_selected` · `cb_invert`),
  탭 전용만 탭 이름을 붙인다(`type_types_tsl` · `token_le` · `rules_list`). 옛 `sel_*`/`sch_*`/`rul_*`
  접두사는 사라졌다.
- **검증(mayapy + 오프스크린 Qt) 16항목 전부 통과** — 최상위 탭이 Type/Token/Rules 이고 중첩이 없는지 ·
  Objects/Source/Invert 가 하나로 합쳐졌는지 · **Get 한 번 뒤 세 탭이 다시 Get 없이 동작하는지**
  (Type 의 List Types/Select By Shape/Select By Type · Token 검색 · Rules 선택) ·
  **Invert 가 세 탭에 함께 걸리는지** · 탈락 사유 로그 · `register()` 한 줄로 새 규칙이 UI 에 나타나는지 ·
  규칙 2개 AND. 파일: `tools/A00310_SearchTool/app/ui/main_window.py` · `app/config/version.py` ·
  `docs/A00310_SearchTool.md` `#A00310`

> [!summary] `A00310_SearchTool` — **Search 를 하위 탭 Token / Rules 로 나누고**, 리스트업된 오브젝트 중 **규칙에 맞는 것만 고르는 Rules 탭** 신규 (v01.01 -> 01.02)
- **요청**: 기존 Search 기능은 **Token** 하위 탭으로 내리고, **Rules** 하위 탭을 새로 만든다.
  Rules 는 TSL 에 리스트업된 오브젝트 중 **정해 둔 규칙에 맞는 것만** 선택한다. 첫 규칙은
  "어떤 노드에도 연결되지 않고 히스토리도 없는 노드"(컨스트레인트·스킨·어트리뷰트 연결 전부 제외).
  **규칙은 계속 늘어날 것**이므로 늘어나는 것을 받아 낼 수 있는 구조여야 한다.
- **★ 늘어나는 것을 받아 내는 구조 — 레지스트리.** 규칙은 `app/core/select_rules.py` 의
  `register(SelectRule(...))` 로 모이고, UI 는 `all_rules()` 가 주는 목록을 **그대로 그린다.**
  그래서 **규칙을 더하는 일 = 함수 하나 + 등록 한 줄**이고 UI 코드는 건드리지 않는다.
  테스트로 고정했다 — 새 규칙을 register 한 뒤 창을 다시 띄우면 목록에 저절로 나타난다.
  규칙을 **여러 개 고르면 AND** 이고, 판정 함수는 `(맞는가, 안 맞는 이유)` 를 돌려줘
  **빠진 것마다 이유가 로그에 남는다**("3개 맞았다" 보다 "나머지는 각각 이래서 제외" 가 쓸모 있다).
- **★ 규칙 이름은 `Standalone`.** 요청은 `Get Pure` 였고 더 좋은 이름이면 그걸로 하라 하셨다.
  `Get` 은 이 툴에서 **리스트를 채우는 버튼 이름**이라 규칙 이름에 넣으면 한 단어가 두 뜻이 되고,
  `Pure` 만으로는 **무엇으로부터 순수한지**가 안 드러난다. `Standalone` 은 "혼자 서 있다" 를
  그대로 말한다. 라벨 한 줄만 바꾸면 `Get Pure` 로 되돌릴 수 있게 해 두었다.
- **★ 판정은 추측이 아니라 실측으로 짰다.** mayapy 로 "깨끗한 노드"와 "엮인 노드"가 실제로 무엇을
  돌려주는지 먼저 재 봤고, 세 가지가 드러났다.
  - **`listHistory` 는 짧은 이름을 돌려준다.** `listRelatives(fullPath=True)` 의 롱네임과 그대로
    비교하면 **자기 셰이프조차 걸러지지 않아** 히스토리 없는 메시가 "히스토리 있음" 이 된다.
    양쪽을 `ls(long=True)` 로 정규화해야 한다.
  - **히스토리 없이 만든 폴리큐브에도 `initialShadingGroup` 이 붙어 있다.** 머티리얼 배정을 연결로
    치면 **어떤 메시도 통과하지 못한다.** 디스플레이 레이어 멤버십·평범한 셋 멤버십도 마찬가지로
    "리깅으로 엮인 것" 이 아니라서 무시 목록(`IGNORED_TYPES`)에 넣었다.
    (`shadingEngine` 은 `objectSet` 의 하위 타입이라 상속으로 판정하면 둘이 같이 걸린다 — 정확한
    타입 이름으로 본다.)
  - **부모-자식은 DG 연결이 아니다.** 그룹 밑에 넣었다고 그 노드가 구동되는 것은 아니므로 통과시킨다.
- **잡아내는 것**: 컨스트레인트(걸린 쪽도 **드라이버 쪽도**) · 디포머(`geometryFilter` 상속 전부) ·
  히스토리(생성 노드·애니메이션 커브) · 어트리뷰트 연결(들어오는 것도 **나가는 것도**).
- **덤으로 고친 것**: `_build_option_row` 가 `Selected` 라디오를 보관하지 않아 코드로 모드를 바꿀 수
  없었다. **배타적 라디오는 `setChecked(False)` 가 무시된다** — 켜려는 쪽을 직접 켜야 한다.
- **검증(mayapy + 오프스크린 Qt)**: 규칙 판정 **19케이스**(깨끗한 메시/그룹/조인트/커브/로케이터 ·
  히스토리 · 스킨 · 스킨에 쓰인 조인트 · 컨스트레인트 양쪽 · 어트리뷰트 입출력 · 키 · blendShape ·
  디스플레이 레이어 · 머티리얼만 · 면 단위 머티리얼 · 평범한 셋 · 부모만 있는 것) **전부 통과**.
  UI **13항목** — 상위 탭 유지 · 하위 탭 Token/Rules · **기존 Token 기능 그대로 동작** · 규칙 목록이
  레지스트리에서 그려짐 · 규칙에 맞는 것만 씬+TSL 선택 · Invert · 탈락 사유 로그 ·
  **register() 한 줄로 새 규칙이 UI 에 나타남** · 규칙 2개 AND — 전부 통과.
  파일: `tools/A00310_SearchTool/app/core/select_rules.py`(신규) · `app/core/__init__.py` ·
  `app/ui/main_window.py` · `app/config/version.py` · `docs/A00310_SearchTool.md` `#A00310`

> [!summary] `A00275_skinTool_V01` — **창을 늘리면 로그창이 자리를 다 먹던 문제**(공용 위젯 수정 · 36툴 공통) + **Layer 의 M_new 가 머티리얼을 하나만 입던 문제** (v01.24 -> 01.25)
- **★ 1. 로그창이 창 높이를 따라 커졌다 — 어제 전면 교체에서 들어간 회귀다.**
  증상은 툴 경계를 끌어 세로로 늘리면 로그창이 그만큼 커져, Weights 탭의 Layer · Migrate 등을
  보려면 스크롤을 내려야 했다. **원인은 높이를 내부 텍스트에만 건 것**이다 — 교체 전엔
  `QTextEdit` 자신이 `setMaximumHeight(160)` 을 갖고 있어 상한이 됐는데, 공용 위젯은 그 값을
  내부로 넘기고 **컨테이너에는 상한을 남기지 않았다.** 레이아웃은 컨테이너를 계속 늘리고
  텍스트는 160 에서 멈추므로 그 차이가 **빈 공간**으로 남는다 — 실측: 창 1060px 에서
  컨테이너 493px · 텍스트 160px, **333px 가 버려진 자리**였다.
  → `Framework/qt/MOD_log_qt_v01.py` 의 높이 3종을 **내부 텍스트 + 컨테이너(버튼 줄 높이를 더해)**
  양쪽에 걸게 고쳤다. 보이는 줄 수는 그대로면서 창을 늘려도 로그창은 커지지 않는다.
  **위젯 수정이므로 상한을 가진 36툴**(`setMaximumHeight` 23 · `setFixedHeight` 13)이 한번에 고쳐졌다.
  높이를 지정하지 않은 툴(로그를 늘어나는 칸으로 쓰는 템플릿 등)은 **의도대로 그대로 늘어난다**
  — 그쪽은 텍스트도 같이 늘어나 빈 공간이 생기지 않으므로 증상이 아니다.
- **★ 2. Layer > Create 로 만든 M_new 가 머티리얼을 한 벌만 입고 나왔다.**
  원본에 5개가 붙어 있어도 M_new 는 1개였다. 원인은
  `listConnections(shape, type="shadingEngine")` 의 **첫 번째를 메시 전체에 건 것**이다 —
  **그 목록에는 어떤 면에 무엇이 붙었는지가 없다.** 면에 따라 머티리얼이 다른 메시에서는
  나머지가 통째로 사라진다. 면별 배정은 **`MFnMesh.getConnectedShaders`** 가 알려 준다 —
  셀이딩 엔진 목록과 **면마다 그중 몇 번인지**를 함께 돌려준다(배정이 없으면 -1).
  rest 형상은 skinCluster 의 입력이라 베이스와 토폴로지가 같아 면 번호가 그대로 맞는다.
  → 면을 연속 구간(`f[0:511]`)으로 묶어 엔진당 `cmds.sets` 한 번으로 옮긴다(면을 하나씩
  이름으로 만들면 잔 메시에서 문자열이 수만 개가 된다). 머티리얼이 하나면 **면 단위가 아니라
  셰이프째** 걸고, 면 개수가 다르면 손대지 않고 경고를 남긴다.
- **검증(mayapy + 오프스크린 Qt)**: 두 증상을 먼저 재현해 수치로 박았고, 고친 뒤 **12항목 전부 통과** —
  `A00275` 는 창 760→1400px 에서 로그창 **182px 고정 · 늘어난 640px 를 탭이 전부** 가져가고,
  `A00170`(Fixed 120)도 창을 두 배로 늘려도 142px 그대로, `A00004`(상한 없음)는 의도대로 늘어난다.
  머티리얼은 5 / 3 / 1 개 메시에서 **면별 배정이 원본과 완전히 일치**(불일치 0면).
  로그 위젯 교체 47툴 전수 스모크도 다시 돌려 이전과 같은 46/47.
  파일: `Framework/qt/MOD_log_qt_v01.py` · `tools/A00275_skinTool_V01/app/core/weight_layer_manager.py` ·
  `app/config/version.py` · `docs/A00275_skinTool_V01.md` · `docs/Framework_MOD_log_qt.md` `#A00275` `#Framework`

> [!summary] **공용 로그창 전면 교체** — PySide 툴 **46곳**의 로그창을 `JUN_mod_log_qt_v01` 로 (이제 저장소 전체 47/47)
- **계획서**: [`Framework_MOD_log_qt_migration_plan.md`](Framework_MOD_log_qt_migration_plan.md) — 대상 선정 · 교체 규칙 ·
  예상 문제 · 배치 5개를 먼저 적어 두고 그대로 진행했다.
- **무엇을 얻나**: 모든 툴의 로그창이 **Expand**(별도 창으로 옮겨 크게 보기) · **Clear** ·
  **Copy**(전문 복사)를 갖는다. 템플릿 `A00004_base_QT` · `A00008_base_QT_maya` 를 같이 바꿨으므로
  **앞으로 만드는 툴은 기본으로** 이 로그창을 갖는다.
- **★ 드롭인이 된 이유는 먼저 세어 봤기 때문이다.** 로그 위젯에 실제로 부르는 메서드는 **10종뿐**이고,
  `isinstance(..., QTextEdit)` · `findChild` · `setStyleSheet` 호출은 **0건**이었다. 그래서 교체는 툴당
  **생성부 2~3줄**로 끝나고 `append` / `appendPlainText` 호출부 **43 + 17곳은 한 글자도 안 건드렸다.**
- **★ 높이는 컨테이너가 아니라 내부 텍스트에 걸린다.** `setFixedHeight(120)` 을 컨테이너에 그대로 걸었다면
  버튼 줄이 그 120 을 나눠 먹어 로그가 줄었을 것이다. 위젯이 내부로 넘기므로 **보이는 줄 수는 교체
  전과 같고**, 창만 버튼 줄(약 22px)만큼 커진다.
- **`object_name` 은 툴 폴더명을 그대로** — `JUN_<폴더명>_log_window`. 같으면 Expand 창이 서로를 찾아
  닫는다. 버전 병존 4쌍(`A00060` · `A00080` · `A00110` · `A00390`)이 동시에 떠 있을 수 있어 실제로 위험한 자리다.
- **결들면 손봐야 했던 곳** — `A00300_meshDoctor` 는 자기 `Clear Log` 버튼을 따로 갖고 있었어서
  같은 기능 버튼이 둘이 되지 않도록 **그 버튼과 연결 코드를 지웠다.**
- **건드리지 않은 것** — 미리보기/리포트/편집기는 로그가 아니다(`constraint_preview` · `te_bd_report` ·
  `txt_log_history` · `txt_new_note` · `editor`). `A00200_CSV_tool` 은 파일 구조와 import 스타일이 달라 **보류**.
- **검증(mayapy + 오프스크린 Qt)**: 툴 47개의 `MainWindow` 를 실제로 생성해 — 예외 없음 · 위젯 타입 ·
  **`object_name` 47개 전부 유일** · `append` 의 HTML 색 살아있음 · `appendPlainText` 가 `<tag>` 를 글자대로 남김 ·
  **파일에 적힌 높이 제약이 내부 텍스트에 걸렸음** · `expand()` → `collapse()` 왕복 후 내용 보존 — **46/47 통과**.
  유일한 실패 `A00008_base_QT_maya` 는 **이번 작업과 무관한 기존 결함**이다 — 존재하지 않는
  `tools.A00001_base_maya` 를 import 한다(2026-06-02 `86a8a45` 부터). 별도 안건.
- **남은 것 — Maya GUI 육안 확인**(오프스크린으로는 잡힐 수 없는 항목): 색깔 로그 3툴
  (`A00300` · `A00410` · `A00430`)의 색 · Pin 툴(`A00110` · `A00220` · `A00340` · `A00370`)과 Expand 창의
  항상-위 관계 · 창 높이를 스스로 계산하는 툴(`A00110` · `A00220`)의 섹션 접기/펼치기 ·
  `setFixedHeight` 계열 13곳의 +22px 가 거슬리는지.
- 커밋은 계획대로 **배치 5개**로 끊었다(문제가 나면 그 배치만 되돌릴 수 있도록) —
  템플릿 2 · 최상위 이득 5 · 상위 6 · 중위 12 · 하위 21. 툴마다 `app/config/version.py` 와
  `docs/<툴>.md` 를 함께 올렸다. `#Framework` `#로그창`

> [!summary] `A00145_RigConnect` Mirror > Create — **`A00170` AttachCrv 로 붙인 오브젝트가 미러가 안 되던 문제** 두 가지 수정 (v01.41 -> 01.42)
- **증상**: `A00170_driverTool` 의 `AttachCrv > Default + Maintain offset` 으로 만든
  `CRV -> vectorProduct -> POCI -> fourByFourMatrix -> multMatrix -> joint` 네트워크를 커브와 함께
  Mirror > Create 로 미러하면, **커브는 미러되는데 붙어 있던 오브젝트는 미러가 안 된 자리**에 남았다.
- **★ 원인 1 — `multiplyDivide` · `vectorProduct` · `plusMinusAverage` 는 셰이딩 노드를 상속한다.**
  `nodeType(inherited=True)` 가 `['shadingDependNode', 'multiplyDivide']` 다. 네트워크 수집이
  `shadingDependNode` 로 셰이딩을 걸러 내고 있어서, **리깅에서 제일 흔한 유틸리티 노드들이 통째로
  빠졌다.** 실측: 6개짜리 네트워크에서 3개만 복제되고 나머지는 원본 노드를 계속 바라봤다.
  → 셰이딩 판정을 노드 **분류**(`getClassification`)로 바꿨다. `multiplyDivide` 는 `math/operation`,
  `file` 은 `texture/2d`, `lambert` 는 `shader/surface`. 앞의 `drawdb/shader/...` 는 하이퍼셰이드
  그리기 분류라 유틸리티에도 붙어 있으므로 **버리고 뒤쪽 기능 분류만** 본다.
- **★ 원인 2 — `multMatrix` 에 값으로 박힌 maintain offset 은 원본 프레임 기준이다.**
  `matrixIn[0] = OPM0 · frame0⁻¹` 는 연결이 아니라 값이라 복제하면 그대로 따라오는데, 미러된 커브의
  프레임과 곱해지는 순간 오브젝트를 원본 쪽으로 끌어당긴다(YZ 미러 실측: `x = -4` 로 가야 할 조인트가
  `x = -10.1`). **오프셋의 미러는 "같은 상수" 가 아니라 "미러된 프레임 기준으로 같은 관계"다.**
  → 네트워크를 다시 세운 뒤 미러가 놓아 준 월드 행렬 `T` 로 돌아오도록 상수를 다시 푼다 —
  `OPM_need = OPM_now · P · W_now⁻¹ · T · P⁻¹`, `matrixIn[k] = 앞쪽곱⁻¹ · OPM_need · 뒤쪽곱⁻¹`.
  로컬을 직접 읽지 않고 현재 상태에서 역산하므로 피벗 · `jointOrient` · `rotateAxis` 와 무관하다.
- **덤 — Maintain offset 을 끄고 붙인 조인트**: 그쪽은 `rotate` 를 네트워크가 직접 구동하는데,
  미러가 회전을 `jointOrient` 로 옮겨 두면 두 회전이 겹쳐 엉뚱한 방향을 봤다. 이 경우 `jointOrient` 는
  **원본 값 그대로** 두고(= 커브 프레임에 대한 같은 로컬 오프셋) 로그에 남긴다.
- 검증(mayapy + `maya.standalone`): 어태치 6종(±X aim · norCrv 유무 · orient 유무 · 조인트/그룹 ·
  maintain offset 유무) + NURBS surface 어태치 + `multiplyDivide`/`plusMinusAverage` 네트워크 +
  셰이딩 노드 제외 — **미러 위치 일치 · 원본 커브와 무관 · 미러된 커브를 대칭으로 따라감** 전부 통과.
  파일: `tools/A00145_RigConnect/app/core/mirror_manager.py` · `app/config/version.py` ·
  `docs/A00145_RigConnect.md` `#A00145`

> [!summary] `A00470_MaterialTool` 머티리얼 표 — **칸 폭을 드래그로 조절** + **더블클릭으로 씬 선택**(한 번 클릭은 선택만) (v01.02 -> 01.03)
- **요청**: `Material` / `Status` / `Meshes` 칸을 드래그해 가로 폭을 조절 · 머티리얼을 더블클릭하면
  그 노드가 선택되도록.
- **★ 드래그로 폭을 바꾸려면 헤더가 `Interactive` 여야 한다** — 기존의 `Stretch`(0번) ·
  `ResizeToContents`(1·2번)는 **스타일이 폭을 계산해 버려 드래그 자체가 막힌다.** 세 칸을 전부
  `Interactive` 로 두고 초기 폭(250/90/70)만 주었으며, `setStretchLastSection(False)` 로 마지막 칸이
  남는 공간에 맞춰 늘어나는 것도 껐다(그러면 사용자가 정한 폭이 무시된다).
- **더블클릭 선택으로 옮겼다** — 그전에는 `itemSelectionChanged` 라 **행을 한 번 클릭만 해도** 씬
  선택이 바뀌었다. 그 상태로 더블클릭을 얹으면 더블클릭이 무의미하므로, 한 번 클릭은 행 선택만 하고
  **더블클릭에서만** 씬 선택을 바꾼다(목록을 훑어보다 씬 선택이 딸려 바뀌지 않는다).
  여러 행을 골라 두고 더블클릭하면 **고른 것 전부**를 선택하고, 무엇을 선택했는지 로그에 적는다.
  지워진 머티리얼이면 죽지 않고 사유를 남긴다.
- 검증(mayapy + 오프스크린 Qt + 실제 씬): **21항목**. 파일:
  `tools/A00470_MaterialTool/app/ui/name_check_tab.py` · `app/config/version.py` ·
  `docs/A00470_MaterialTool.md` `#A00470`

> [!summary] **공용 로그 위젯 `JUN_mod_log_qt_v01` 신규** — `Expand` / `Clear` / `Copy` 버튼이 달린 로그창을 Framework 로 승격하고 `A00470` 에 적용 (A00470 v01.01 -> 01.02)
- **요청**: 로그창에 작은 버튼 3개 — **Expand**(팝업으로 로그를 보여주는 창) · **Clear** · **Copy**.
  이것을 **공용 위젯으로 승격**해 A00470 이 쓰게 하고, 이후 로그창을 쓰는 모든 툴을 이걸로 교체할 계획.
- **★ 드롭인 교체가 되도록 설계했다.** 저장소 로그창은 두 계열이다 — `te_log`(QTextEdit) 25곳,
  `log_view`(QPlainTextEdit) 14곳. 호출하는 메서드를 전수 조사해 **그 이름을 전부 받는다**:
  `append` · `appendPlainText` · `setReadOnly` · 높이 3종 · `clear` · `setFont` · `setLineWrapMode` ·
  `moveCursor`. 나머지는 `__getattr__` 로 내부 텍스트에 위임 → 교체는 **생성 두 줄**만 바뀐다.
- **★ 내부는 `QTextEdit` 이어야 한다** — `A00300` · `A00430` · `A00410` 이 `append('<span style=…>')`
  로 **색깔 로그**를 쓴다. `QPlainTextEdit` 로 두면 그 세 툴에서 태그가 글자로 보인다. 대신
  `appendPlainText` 를 커서로 직접 구현해 **평문은 `<` 가 먹히지 않게** 했다.
- **★ 높이는 컨테이너가 아니라 내부 텍스트에 건다** — `setFixedHeight(110)` 을 컨테이너에 걸면
  버튼 줄이 그 높이를 나눠 먹어 로그가 줄어든다(공용 TSL 의 max-height 함정과 같은 것).
  결과적으로 **보이는 줄 수는 교체 전과 같고** 창만 버튼 줄만큼 커진다.
- **Expand 는 복제가 아니라 이동** (`MOD_expand_qt_v01` 과 같은 방식) — 확장 중에 들어온 로그도
  같은 위젯에 쌓여 동기화 문제 자체가 없다. 툴 창이 닫히면 `eventFilter` 로 자동으로 접어 미아 방지.
- **★ 첫 시도에서 버튼 글자가 안 보였다** — 모든 테마 qss 의 `QPushButton { padding: 8px; }` 이
  `setFixedHeight(20)` 과 만나 위아래 16px + 테두리 2px 로 **글자 자리가 2px** 만 남았다(글꼴 12px).
  버튼은 멀쩡히 보이고 클릭도 되므로 **크기만 보면 정상인** 버그다. 이 세 버튼만
  `padding: 0px 6px` 로 덮어써 내용 영역을 **72x2 -> 72x18** 로 되돌렸다(색·테두리는 테마 그대로).
  폭도 `setFixedWidth` 를 버리고 `setMinimumWidth(58)` 로 — 폰트가 큰 테마에서 같은 일이 가로로
  되풀이되지 않게.
- **★ 검증 방법도 한 번 틀렸다** — 버튼을 `grab()` 해 글자 픽셀을 세려 했는데, 오프스크린에서는
  `QLabel` 조차 고유 색이 1개다(**글자가 래스터화되지 않는다**). 멀쩡한 버튼도 0px 로 나와
  아무것도 가리지 못했다. `QStyle.SE_PushButtonContents` 내용 영역을 재는 방식으로 바꿨다.
- 검증(mayapy + 오프스크린 Qt): **56 + 55항목**(버튼 여백은 8개 테마 × 3버튼, 버그 재현 포함).
  파일: `Framework/qt/MOD_log_qt_v01.py`(신규) ·
  `Framework/qt/__init__.py` · `tools/A00470_MaterialTool/app/ui/main_window.py` ·
  `docs/Framework_MOD_log_qt.md`(신규) `#Framework` `#A00470`

> [!summary] `A00470_MaterialTool` **신규** — 메시에 붙은 머티리얼 이름이 명명 규칙(JSON 프로파일)에 맞는지 진단하고 고칠 이름을 제안 (v01.00)
- **요청**: TSL 에 메시를 담아 거기 붙은 머티리얼 이름을 보고, **정해진 규칙과 맞는지 · 어떻게 고칠지**를 로그로.
  규칙은 **profile 로서 json 파일**로 저장하고 골라서 적용. 첫 규칙 `Set_v001` 은
  `MT_MANU_{캐릭터}_{세트}_{부위}_{기타...}`. 리포트는 **클립보드 복사**(체크박스, 기본 켬)와 **자세한 로그** 기능까지.
- **규칙 = 데이터**: `data/profiles/Set_v001.json` 한 파일이 규칙 한 벌. 토큰 타입 `literal`/`enum`/`pattern`/
  `regex`/`any` + `optional`·`repeat`·`case_sensitive`·`hint`. 새 규칙은 툴 수정이 아니라 파일 추가다.
  (`SetXXX` 는 **3자리 숫자**로 읽었다 — 바꾸려면 JSON 의 `"digits": 3` 한 줄)
- **★ 토큰을 앞에서부터 붙이면 안 된다** — `MT_SYN_Sett002_Pantss` 는 `MANU` 가 빠진 이름이라, 순서대로 붙이면
  뒤가 전부 밀려 "전부 틀림" 이 된다(사람에게 쓸모없는 리포트). **정렬 DP**(Needleman–Wunsch 꼴, 짝짓기 /
  슬롯 비우기 / 토큰 버리기)로 풀어 요청한 그대로 **틀린 토큰 3개 + 생략된 `MANU`** 가 나온다.
  고칠 수 있는 오타에 가산점(+2)을 줘 "그 자리에 오려던 토큰" 으로 읽게 했다.
- **고칠 이름 제안**: `enum` 은 편집 거리로 가장 가까운 값(`SYN`→`SIN`, `Pantss`→`Pants`), `pattern` 은 알파벳/숫자를
  갈라 재조립(`Sett002`→`Set002`). **제안은 돌려주기 전에 자기 규칙으로 다시 검사한다** — 통과 못 하는 수정 제안은
  없느니만 못하다. 꼬리 숫자(`..._extra3`)는 경고 + `extra_3` 제안, `_002` 처럼 갈라진 숫자는 통과.
- **★ 한 트랜스폼에 셰이프가 여럿**이면 "첫 셰이프" 만 보는 순간 머티리얼을 놓친다 → non-intermediate 셰이프를
  **전부** 본다. 페이스별 할당도 같은 경로로 잡힌다(실측). 씬은 **읽기만** 한다.
- 검증(mayapy 2024 헤드리스): **규칙 엔진 85항목 + 마야 통합 25항목**. 마야 GUI 확인은 아직.
- 파일: `tools/A00470_MaterialTool/**`(코어 4 · UI 2 · 프로파일 1 · 아이콘), `docs/A00470_MaterialTool.md`,
  `docs/portfolio/portfolio_EN.md` · `portfolio_KR.md`, `README.md` `#A00470`

> [!summary] `A00470_MaterialTool` `Set_v001` 규칙 갱신 — 고정 토큰 **`CH`** 추가 : `MT_MANU_CH_{character}_{set}_{part}_{extra...}` (v01.00 -> 01.01)
- **요청**: `MT` 와 마찬가지로 **한 글자도 변하면 안 되는** `CH` 를 `MANU` 뒤에 넣는다.
- 코드는 그대로고 **프로파일 JSON 한 파일만 고쳤다**(`{"role": "category", "type": "literal", "value": "CH"}`) —
  규칙을 데이터로 둔 설계가 처음으로 값을 한 셈이다.
- **★ `CH` 와 `CHN` 은 편집 거리 1** 이라 서로 빨려들 수 있는 자리다. `MT_MANU_CHN_Set002_Top` 은
  **`CH` 생략 + `CHN` 은 캐릭터**로, `MT_MANU_CH_Set002_Top` 은 **`CH` 는 제자리 + 캐릭터 생략**으로
  읽혀야 한다. 정렬 점수(유효 +4 > 오타 +2)가 두 경우를 모두 옳게 고르는 것을 테스트로 못 박았다.
- 검증: 규칙 엔진 **102항목**(`CH` 슬롯 10종 신설) + 마야 통합 **27항목**. `#A00470`

---

## 2026-09-15

> [!summary] `A00080_KWI_creator_V03` **One node per setting node** 체크박스 — 같은 세팅 노드에 엮일 본들을 KawaiiPhysics 노드 하나로 모은다 (v01.04 -> 01.05)
- **요청**: 본마다 노드를 만들지 말고, **같은 피직스 세팅 노드에 엮인 본들은 모두 같은 KawaiiPhysics 노드**에
  있도록 하는 설정을 체크박스로. 직전에 LUN 머리카락 `ref_02.txt`(노드 120개 · `PS_hair_0~3` 에 30개씩)를
  손으로 4개 노드로 합친 작업을 툴 기능으로 옮긴 것.
- **규칙**: 툴은 이미 본 i 의 노드를 세팅 노드 `i % N` 에 엮는다 → 그룹 k = `tgtBones[k::N]`. 그룹마다 노드 하나
  (첫 본 RootBone, 나머지 AdditionalRootBones), `PS_base_k` 는 노드 k 에만, LD 는 전부에. 체인·위치 규칙은 그대로.
  N 이 본보다 많으면 빈 그룹은 노드를 만들지 않는다. Multiple 에서만 활성(Single 은 이미 노드 하나).
- 검증(plain python 36항목): **체크박스를 끄면 v01.04 출력과 바이트 단위 동일**(수정 전에 기준값을 떠 비교),
  켜면 LUN 본 120 · N=4 의 노드별 본이 ref_02 의 `PS_hair_0~3` 그룹과 정확히 일치, 링크·체인, 12본/N=5,
  N > 본 수. 덤으로 **Single 모드에 본이 하나면 죽던** 기존 버그(`additional_str` 미정의) 수정.
- 파일: `app/core/KWI_creator.py`, `app/ui/main_window.py`, `CHANGELOG.md`, `docs/A00080_KWI_creator_V03.md` `#A00080`

> [!summary] `A00145_RigConnect` Mirror > Apply 에 **`Keep Children in Place`**(기본 ON) + 리스트 이름 `Left`/`Right` → **`Source`/`Target`** (v01.40 -> 01.41)
- **요청**: Apply 로 오른쪽 리스트 오브젝트의 위치·회전을 바꿀 때, 그 **모든 자식은 영향을 받지 않고 수정 전
  월드 위치·회전을 지키는** 체크박스(기본 체크). 그리고 리스트 이름 `Left`/`Right` 를 적절한 이름으로.
- **이름 = `Source` / `Target`** — 원본은 읽기만 하고 옮겨지는 쪽이 따로 있다. **스왑(`Source=[a_l, a_r]`,
  `Target=[a_r, a_l]`)이 정상 사용법**이라 좌우 이름은 틀린 설명이었다. 모드 `Apply (Source -> Target)`,
  버튼 `Mirror to Target`, 코어 경고·로그 문구, 위젯 이름(`tsl_mirror_source/target`)까지 맞췄다.
- **방법**: 아무것도 옮기기 전에 Target 마다 **직계 자식**의 월드 행렬을 읽어 두고, 그 Target 을 놓은 직후
  `xform -ws -m` 로 되돌린다. 손자는 로컬이 그대로라 저절로 제자리다. 피벗 · `rotateOrder` · `jointOrient` 가
  있어도 월드 행렬로 되돌리므로 따로 보정할 게 없다.
  - **자식이 그 자신도 Target 이면 붙잡지 않는다** — 부모 -> 자식 순서라 뒤에서 제 미러 위치로 절대 배치되고,
    그 아래 자식은 다시 지켜진다. 컨스트레인트 노드는 건너뛴다.
  - 잠겼거나 연결된 자식은 Target 과 같은 `_channel_blockers` 판정으로 걸러 **부모를 따라간 채 두고 이유를 찍는다.**
- **★ 컨스트레인트가 구동하는 자식은 부모가 움직여도 이미 제자리다**(월드를 드라이버가 잡고 있다). 처음 테스트는
  "연결됐으니 경고가 나야 한다" 고 기대했는데 틀린 기대였다 — 되돌리기 전에 값부터 비교해 같으면 그냥 넘어간다.
- **★ Reflect 로 부모의 좌우손계가 바뀌면** 자식이 월드에서 그대로 있으려면 자기 로컬 손계가 바뀌어야 해
  **한 축 스케일이 음수**가 된다 → 이때만 scale 채널도 검사하고(`scaleY` 잠긴 자식은 경고), 그런 자식 수를 알린다.
- headless(mayapy 2024) — Orientation / Behavior / Reflect 각각 `keep_children` on/off 비교: Target 결과는 둘이 같고,
  on 이면 자식(피벗·rotateOrder 그룹 · 조인트 · 메시 · 손자 · Target 인 자식의 자식 · 조인트 Target 의 조인트 자식)
  월드 불변, off 면 로컬 불변, 잠김·scale 잠김·컨스트레인트 처리, undo 한 번, 메시지 이름, UI(기본값·제목·버튼·핸들러).

> [!summary] `A00275_skinTool_V01` Layer 수정 — lock 이 넘칠 때 **위 레이어부터 잘리도록** 방향을 바로잡음 (v01.22 -> 01.23)
- **피드백**: M_01[jnt_01_a, jnt_01_b], M_02[jnt_02_a, jnt_02_b] 를 아래에서 위 순서로 담고(베이스 M_01)
  jnt_01_a, jnt_02_a, jnt_02_b 를 lock 하고 Merge → **jnt_01_a 웨이트가 사라지고** jnt_02_a/b 만 남았다.
  jnt_01_a 도 lock 했으니 보존되길 원함.
- **진단(mayapy 재현)**: 버그가 아니라 v01.22 규칙대로였다 — 위 레이어 M_02 가 조인트를 **전부** lock 해 합 1.0 을
  가져가 베이스의 lock 이 들어갈 자리가 없었다(25 버텍스 중 0개). 순서를 바꾸면 24/25 에 남았다. 게다가 베이스의
  잘림은 `cut` 에 세지 않아 **경고도 없었다**. 원인은 Q3 답 "위 레이어에서부터 자르도록" 을 "위 레이어 우선" 으로
  **뒤집어 읽은 것**. 답을 받을 때 보여 준 예시가 합 0.9 라 넘침이 없어 방향을 가르지 못했다.
- **수정**: lock 을 **아래 레이어부터** 붓고 넘치면 위 레이어부터 비율로 줄인다. 베이스에 lock 이 없으면 베이스 전체
  행은 마지막에 **남은 몫을 채운다**(잘림으로 세지 않음). 잘린 버텍스는 모든 레이어에서 센다.
  lock 합이 1 을 넘지 않는 경우(처음 예시, Q1, Q2)는 결과가 그대로다.
- 검증: 피드백 시나리오(jnt_01_a 가 전 버텍스에서 M_01 값, jnt_02_a/b 가 `(1 - jnt_01_a) x M_02 비율`, cut 보고)를
  순수 계산·실제 메시 둘 다로 추가, 넘침 순서 테스트 기대값 반전. 문서 · UI 문구 · 툴팁도 방향에 맞춰 수정.
  `#A00275`

> [!summary] `A00275_skinTool_V01` **`Weights > Layer`** 신규 — 버텍스 순서가 같은 메시 N 개의 웨이트를 메시마다 lock + Blend 로 레이어처럼 합성해 새 메시로 만들거나 기존 메시를 갱신 (v01.21 -> 01.22)
- **요청**: M_01, M_02 … 가 각자 다른 조인트에 바인드돼 있을 때, 메시마다 조인트를 리스트업하고 **보존할 조인트를
  lock**, `Blend`(0~1)로 섞을 양을 정해 `Merge` 하면 합성된 `M_new` 가 생긴다. 먼저 계획서
  (`docs/plans/A00275_skinTool_V01_layer_tab_plan.md`, `169c2e2`)를 쓰고 질문 5개에 답을 받아 구현.
- **규칙(사용자 답)**: 위 레이어부터 `Blend x lock 웨이트` 를 **절대값**으로 넣고, 남은 몫을 넘는 레이어만 비율로
  줄인다(위 레이어 우선). 모자라면 재정규화. lock 이 0 인 버텍스는 아래 행이 그대로 옮겨진다. 베이스(맨 아래)도
  lock 가능(없으면 전 조인트), 결과 형상은 베이스. 추가로 **Update existing mesh 모드**와 조인트 **다중 선택·다중
  체크**(A00290 Shape Editor 식)를 요청받아 함께.
- **★ `MFnSkinCluster.setWeights` 는 undo 기록에 남지 않는다**(mayapy 실측 — 청크 안에서 써도 undo 할 것이 없다).
  갱신 모드는 Ctrl+Z 로 돌아와야 해서 버텍스마다 구간 `setAttr` 로 쓴다(19,881 x 8 에 0.57초, undo 0.27초).
  구간은 새 값과 기존 값의 인덱스를 모두 덮는다.
- **★ 새로 바인드하면 지금 포즈가 바인드 포즈가 된다** → `bindPreMatrix` 를 소스 skinCluster 에서 복사. 포즈 중에
  Merge 해도 lock 영역은 M_01, 나머지는 M_02 의 변형과 1e-4 이내로 일치(포즈를 더 바꿔도 유지).
- **★ Lock 리스트 항목에 `ItemIsUserCheckable` 을 주면 한 번 클릭에 두 번 토글**된다(델리게이트가 놓을 때 또 뒤집음)
  → 트리가 누를 때 직접 전환, 선택된 행 전부, 선택 유지. `setSelected(True)` 는 단일 선택 목록에서도 다른 줄을
  안 풀어 `setCurrentItem` 으로 고른다.
- 검증: mayapy 코어 47항목 + UI 33항목(실제 마우스 클릭) 통과, 19,881 버텍스 x 레이어 3 = 1.0초. 실제 마야 GUI 확인은 아직.
- 파일: `app/core/weight_layer_manager.py`(신규), `app/ui/layer_tab.py`(신규), `app/ui/main_window.py`,
  `docs/A00275_skinTool_V01.md` `#A00275`

> [!summary] `memory` **MEMORY.md 색인 정리** — 182 -> 88줄, 같은 툴의 기능 메모를 한 줄로 묶어 200줄 읽기 한도 아래로
- 링크 153개는 **전부 유지**(누락 파일 없음). 같은 툴의 기능 메모를 `- A00xxx — [a](..) · [b](..)` 한 줄로 묶었다.
- 색인 정리는 다른 세션이 시작하고 이어받아 마쳤다 — 한 파일이라 세션별로 나누지 않고 한 커밋.
- 함께 추가한 메모 링크 2개(A00170 세션): `parentmatrix-includes-offsetparentmatrix` · `surface-normal-handedness`.
  파일: `.claude/memory/MEMORY.md` `#memory` (ea3afa4)

> [!summary] `A00145_RigConnect` Mirror 탭에 **`Apply (Left -> Right)`** 모드 — 새로 만들지 않고, 이미 있는 반대쪽 오브젝트를 미러 위치·회전으로 옮긴다 (v01.39 -> 01.40)
- **요청**: Mirror 탭에 `Left` / `Right` 리스트 두 개를 두고, Left 를 미러한 결과의 위치·회전을
  같은 줄 Right 오브젝트에 적용. `Translation` / `Rotation` 체크박스(기본 ON), Mirror Plane · Mirror Type
  (Reflect 기본)은 그대로, 스킨·컨스트레인트 옵션은 쓰지 않는다. "리스트를 Objects 1개 / 2개 중
  고르는 UI" 제안의 적합성 검토도 함께.
- **UI**: 탭 맨 위 `Mode` 라디오 — `Create (Objects)` / `Apply (Left -> Right)`. 모드가 바꾸는 것은
  리스트(1개 ↔ 2개), 옵션 박스(`Options` ↔ `Apply`), 버튼 이름(`Mirror` ↔ `Mirror to Right`)뿐이고
  Plane / Type 은 두 모드가 공유한다.
- **규칙 = "Create 모드가 그 자리에 만들었을 트랜스폼"**: 같은 `_mirror_matrix`, 조인트 / 컨트롤러 줄,
  메시의 Orientation 폴백까지 그대로. 포즈를 준 왼쪽을 Apply 한 결과가 **같은 리그를 새로 Create 한
  결과와 행렬 단위로 일치**한다(mayapy). 스케일 **크기**는 Right 것을 유지하고, 조인트는 `jointOrient`
  를 두고 `rotate` 가 바뀐다(`xform -ws -m` 이 원래 그렇게 동작 — 실측).
- **★ Left 행렬을 옮기기 전에 전부 읽는다** → `Left=[a, b]`, `Right=[b, a]` 로 좌우 포즈 스왑이 한 번에.
  쓰기는 부모 -> 자식 순이라 자식을 먼저 담아도 밀리지 않는다.
- **★ `xform` 은 잠긴 채널을 에러 없이 건너뛰고 나머지만 바꾼다**(회전이 잠겼으면 이동만 되는
  반쪽 결과 — 실측). 그래서 쓰기 전에 막힌 채널(잠김 / 키가 아닌 연결)을 찾아 **그 오브젝트를 통째로
  건너뛰고** 이유를 로그에 남긴다. 키만 걸린 채널은 옮기고 "키는 안 찍었다" 고 알린다.
  좌우손계가 바뀌면(Reflect ↔ 나머지) scale 부호도 써야 하므로 scale 도 검사한다.
- 짝(인덱스)은 걸러내기 **전에** 정한다 — 한 줄이 없는 이름이라도 뒤의 짝이 밀리지 않는다.
- 검증: mayapy 코어 27항목(Reflect/Behavior/조인트/T·R 단독/스왑/잠김·컨스트레인트·키/부모-자식 순서/
  XY 평면 부호 뒤집힘/메시 폴백/잘못된 줄) + UI 14항목(모드 전환 시 리스트·박스 표시, 버튼 이름,
  버튼 실행 결과·로그, 둘 다 끄면 에러) 통과. 실제 마야 GUI 확인은 아직.
- 파일: `app/core/mirror_manager.py`(`mirror_onto`), `app/ui/main_window.py`, `docs/A00145_RigConnect.md`
  `#A00145`

> [!summary] `A00170_driverTool` AttachCrv > Default 의 대상 칸이 **NURBS surface** 도 받는다 — `JUN_PY_matrixPinning_V01_01` 이식 (v01.22 -> 01.23)
- **요청**: `Attachment Curve` 칸에 커브뿐 아니라 NURBS surface 도 넣어 동작하게. 참고는
  `_archive/legacy_tools/01_Modules/JUN_PY_matrixPinning_V01_01.py`(Chris Lesage `pin_to_surface`).
- ref 흐름 그대로: `closestPointOnSurface`(임시)로 최근접 **(u, v)** → `pointOnSurfaceInfo` →
  `fourByFourMatrix`. 뒷단(`multMatrix` · decompose / Maintain offset 의 `offsetParentMatrix`)은
  커브와 **같은 경로**를 탄다 — `_attach_one(kind=)` 한 곳에서 point-info 노드만 갈라진다.
  대상 판별은 `resolve_target()`(transform/shape 모두), 아니면 `NURBS curve or NURBS surface` 경고.
- **★ ref 의 행 구성 `[tangentU, normal, tangentV]` 는 왼손 좌표계다.** 진단해 보니 마야의 normal 이
  정확히 `tangentU × tangentV`(내적 `+1.0`) — 그 행렬은 det < 0 이라 decomposeMatrix 가 음수 스케일로
  풀고 `rotate` 만 연결하면 한 축이 뒤집힌다. **normal 을 업 시드로 직교 정규화**해
  `Z = tangentU × normal`(−tangentV 방향) 오른손 프레임을 쓴다. tangentU/V 가 직교가 아닐 때의 shear 도 같이 없어진다.
- norCrv 는 커브 전용 — 서피스를 넣으면 체크박스가 꺼진다(대상 칸 `textChanged` 로 동기화).
- **Distribute** 도 서피스에서: 새 `Surface Axis`(U/V) 방향으로 균일, 반대 방향은 **파라미터 범위의
  가운데**. ref 는 `v=0.5` 고정이라 `rebuildSurface -kr 2`(범위 0~4 × 0~2) 같은 서피스에서 가운데를 벗어난다.
- 노드 `<obj>_atc_POSI`, 세트 `<surface>_atcPOSI_SET`(커브 이름은 그대로). 로그의 파라미터는 `(u, v)`.
- headless(mayapy 2024) — 서피스 **139항목**(대상 판별 5종 · maintain offset × (+X/−X/orient off) 에서
  월드·채널 불변 / 서피스 이동·회전 추종 / CV 변형 뒤 강체 / undo · 스냅 모드 위치·X=tanU·Y=normal·오른손·
  최근접이 41×41 격자보다 가까움 · Distribute U/V/open/범위≠0~1 · UI 활성 동기화·빌드·분배·경고)
  + 커브 회귀 **148항목** 통과.

> [!summary] `A00170_driverTool` AttachCrv > Default 에 **`Maintain offset`**(기본 ON) — 어태치해도 오브젝트가 제자리·제 회전·제 스케일 그대로 (v01.21 -> 01.22)
- **요청**: `Attach to Closest Point` 를 누르면 Objects 리스트의 오브젝트가 전부 커브 위로
  옮겨지고 회전도 바뀐다. 체크박스 `Maintain offset`(기본 체크)을 두고, 켜져 있으면 기능 수행 후에도
  **원래 위치·회전(·스케일)이 보존**되게.
- **`translate`/`rotate` 대신 `offsetParentMatrix` 를 구동한다.** 오프셋 상수 =
  `OPM0 × 부모월드0 × inverse(프레임0)`, 네트워크 = `상수 × fourByFourMatrix.output × 부모.worldInverseMatrix`.
  빌드 순간엔 OPM 이 원래 값과 같고, 이후엔 커브 프레임이 움직인 만큼만 따라간다. 채널을 아예 안
  건드리므로 **피벗 · `jointOrient` · `rotateAxis` · `rotateOrder` 를 따로 보정할 필요가 없고**, 채널이
  비어 있어 컨트롤러면 그대로 키를 줄 수 있다.
- **★ 오브젝트 자신의 `parentMatrix` 에는 자기 `offsetParentMatrix` 가 들어 있다**(Maya 2024 실측:
  `parentMatrix == OPM × parent.worldMatrix`, `worldMatrix == matrix × parentMatrix`). 처음엔 기존
  경로처럼 `obj.parentInverseMatrix` 를 물렸다가 **자기 출력을 되먹어**, 부모 + OPM 값이 있는
  오브젝트만 월드가 어긋났다. 부모 transform 의 `worldInverseMatrix` 를 직접 쓴다.
- **★ 직선 norCrv 의 노멀은 커브를 평행 이동만 해도 부호가 뒤집힌다**(det `+0.95 -> -0.95`). ref
  프레임(Y=norCrv 접선, Z=norCrv 노멀)은 X 와 직교도 아니라, 오프셋을 들고 가면 오브젝트가 뒤집히거나
  shear 가 샌다. Maintain offset 일 때만 **X=커브 접선, 업 시드=norCrv 접선**으로 직교 정규 프레임을
  다시 짠다(OFF 경로와 Edge Loop 탭은 ref 프레임 그대로).
- `offsetParentMatrix` 가 이미 연결된 오브젝트는 노드를 만들기 전에 건너뛴다. Distribute 는 대상 아님.
- headless(mayapy 2024) **148항목** 통과 — 부모 회전·스케일 + 기존 OPM 값 + 피벗 + `rotateAxis` +
  `rotateOrder` 로케이터, `jointOrient` 조인트, 월드 널 × (norCrv +X/-X · 월드업 · orient off):
  빌드 후 월드/채널 불변, 커브 평행 이동·회전을 정확히 따라감, CV 변형 뒤 변화가 강체(shear·뒤집힘 없음),
  undo 한 번에 원복, 연결된 OPM skip, OFF 는 기존대로 스냅, UI 핸들러 스모크.

---

## 2026-09-11

> [!summary] `A00290_BSTool` `Edit BS` 하위 탭 2개 — **`Default`**(기존) + **`Naming`**(타겟 이름 = 언리얼 모프 타겟 이름 일괄 변경) (v01.20 -> 01.21)
- **요청**: `Edit BS` 에 하위 탭 `Default` / `Naming` 을 만들고, 기존 기능은 `Default` 로.
  `Naming` 에서는 주어진 blendShape 의 타겟을 나열해 **선택한 타겟의 이름을 원하는 대로**
  바꾼다 — **blendShape 노드가 간직한 이름이 바뀌어야** 하고, 목적은 언리얼로 임포트되는
  FBX 의 모프 타겟 이름이다. "마야 기본 기능으로 되면 사용법을 알려 달라" 도 함께.
- **마야 기본 기능은 하나씩만 있다** — Shape Editor 에서 **타겟 이름 더블클릭**이 곧
  `cmds.aliasAttr("새이름", "bs.weight[i]")` 다. 없는 것은 여러 개를 규칙으로 바꾸는 방법과
  바꾸기 전에 결과를 보는 방법이라, 그 부분만 탭으로 만들었다.
- **★ FBX 에 나가는 것은 별칭뿐이다**(Maya 2024 + FBX 2020.3.4 실측). ASCII 로 뽑아 보면
  `Geometry::<별칭>` 과 `SubDeformer::<bs>.<별칭>`(BlendShapeChannel) 만 있고 **타겟 메시의
  노드 이름은 파일 안에 한 번도 나오지 않는다** — 구운 타겟이든 라이브 타겟이든 같다.
  언리얼은 채널 이름에서 `<bs>.` 접두사를 떼어 모프 타겟 이름으로 쓴다. 그래서 별칭만 바꾼다
  (메시 이름도 같이 바꾸는 것은 씬 정리용 옵션으로 따로 뒀다).
- 모드 셋 — **Set Name**(`#` 이 번호, `Start` 부터) · **Search & Replace**(`Match case`) ·
  **Prefix / Suffix**. 미리보기 트리(Current / New / Note)가 타이핑하는 즉시 따라온다.
- **★ 같은 이름으로 다시 rename 하면 에러다.** `aliasAttr` 이 "이미 그 이름의 어트리뷰트가
  있다" 며 `RuntimeError` 를 던진다 — 안 바뀌는 타겟은 **호출 자체를 건너뛰어야** 한다
  (미리보기에서 회색 `unchanged`).
- **★ 같은 이유로 이름 맞바꾸기(A<->B)는 한 번에 안 된다.** 그래서 바뀌는 타겟 전부를
  **임시 이름 -> 최종 이름 2단계**로 넘긴다. 돌려쓰기(A->B->C->A)도 같은 경로로 지나간다.
- **★ 빨간 줄이 하나라도 있으면 아무것도 적용하지 않는다.** 금지문자 · 숫자로 시작 · 한글 ·
  노드에 이미 있는 어트리뷰트(`envelope` 포함) · 이번 작업 안의 중복을 **미리** 걸러 낸다.
  절반만 바뀐 상태가 가장 나쁘고, 실패가 터지면 이미 바꾼 것을 원래 이름으로 되돌린다.
- `-` 는 **마야가 받아 주지만 툴이 막는다** — `bs.a-b` 가 표현식에서 뺄셈으로 읽힌다.
- 베이스 지오메트리가 여럿이면 **한 타겟에 라이브 메시가 여러 개**다. 별칭은 인덱스 하나에
  하나라 정상이지만 메시 이름은 전부 같게 만들 수 없어 **손대지 않고 로그로 알린다.**
- 이어서 **`Also rename the live target mesh node` 를 기본 켬으로** 바꿨다 (v01.21 -> 01.22) —
  요청. 씬에 남은 타겟 메시 이름이 타겟 이름과 어긋난 채 쌓이는 게 더 헷갈린다는 판단.
  FBX 에는 메시 이름이 안 나가므로 언리얼 결과는 켜든 끄든 같다.
- headless(mayapy 2024) — 코어 **57항목** · UI 스모크 **31항목** · FBX 라운드트립 통과.
  타겟 400개에서 키 입력당 미리보기 `0.02s` · 적용 `0.16s` · undo `0.01s` (스로틀 불필요).
  (이름 짓기 · 사전 검사 7종 · 맞바꾸기/돌려쓰기 · undo 한 스텝 · 구운/라이브 타겟 ·
  베이스 여러 개 · 필터로 가려진 선택 제외 · 익스포트한 FBX 에 예전 이름이 없는지)

---

## 2026-09-10

> [!summary] `A00440_SetTool` 탭 2개로 — **`Edit`**(기존) + **`Create`**(오브젝트마다 `<이름>_Set` 세트) (v01.00 -> 01.01)
- **요청**: `Edit` / `Create` 탭을 만들고 기존 기능을 `Edit` 으로 옮긴다. `Create` 에는 TSL 을
  두고, **리스트업된 오브젝트를 하나씩 담는 세트**를 만든다 — 세트 개수 = 오브젝트 개수,
  이름은 `<오브젝트 이름>_Set`.
- 기존 `SetTab` 은 한 줄도 안 고치고 `QTabWidget` 의 첫 탭으로 넣었다. `CreateTab` 은 새 파일
  (`app/ui/create_tab.py`), 로직은 `set_manager.run_create_per_object()` — 로그창은 둘이 함께 쓴다.
- **★ 이름을 마야에 그대로 넘기면 조용히 고친다**(실측). `pCube1.vtx[0]_Set` -> `pCube1_vtx_0__Set`,
  **`1_Set` -> `_Set`(앞 숫자를 버린다)**, `rig:pCube1_Set` 는 **그 네임스페이스 안에** 만든다.
  그래서 경로·네임스페이스를 떼고 못 쓰는 문자를 우리가 먼저 `_` 로 바꾼다(`set_name_for`).
- **★ 앞 숫자는 마야가 어디서나 버린다** — 노드 `01_arm` -> `_arm`, 그룹 `9grp` -> `grp`,
  네임스페이스 `1ns` -> `ns`. 그래서 **씬에서 온 이름은 애초에 숫자로 시작할 수 없다**(테스트가
  이걸 가르쳐 줬다 — `rename` 이 조용히 바꾼 이름을 기대값으로 쓰고 있었다). 손으로 넣은
  이름 대비로 `_` 를 앞에 두는 것은 남겨 뒀다.
- **★ 세트를 그냥 `select` 하면 멤버가 펼쳐진다** — 세트 노드 자체를 고르려면 `noExpand`
  (`select_sets()`). 이 툴이 원래 Split 에서 조심하던 함정과 같은 것이다.
- 이름이 밀리면(`pCube1_Set` -> `pCube1_Set1`) **하나하나 경고로 짚는다** — 이름을 보고 찾을
  사람에게 조용히 밀리는 것이 가장 나쁘다. 세트가 아닌 노드가 이름을 차지해도 마찬가지다.
- 만든 세트는 기본으로 `Edit` 탭 리스트에 담기고 탭도 그쪽으로 넘어간다 — 방금 만든 것이 곧
  다음에 합칠 것들이라서다.
- headless(mayapy 2024) **34항목** 통과 (기존 71항목 스위트와 별도) — 탭 구성 · 오브젝트 수만큼
  세트 · undo 한 스텝 · 경로/네임스페이스 제거 · 이름 규칙 6가지 · 충돌 경고 · 짧은 이름이 같은
  두 오브젝트 · 가드 · `Edit` 로 보내기 · 보낸 세트로 Union · 세트 선택이 안 펼쳐지는지.


> [!summary] `A00060_jointTool_V03` `poleSlide` 에 **0.1 배율** — 같은 눈금으로 10배 섬세하게 (v03.07 -> 03.08)
- **요청**: 지금은 0.1 단위로 돌려도 오브젝트가 너무 많이 움직인다. 값에 **0.1 을 곱해**
  더 섬세하게 움직이게.
- `SLIDE_SCALE = 0.1` 을 두고 수식과 배선 양쪽에 같이 먹였다 — 한 칸(0.1)이 반현의
  **10% -> 1%**, "끝까지" 가 `±1 -> ±10` 이 됐다. 스핀박스 소수점은 네 자리로.
- **★ 노드는 하나도 늘지 않는다.** `_side` 의 Y 채널은 이미 `s/2` 를 나누고 있었으므로
  **나눗수를 `2` 에서 `2/SLIDE_SCALE = 20` 으로** 바꾸면 반으로 나누기와 배율이 한 번에 끝난다.
- **★ 배율을 바꾸는 변경은 이미 배선된 씬을 조용히 불일치하게 만든다.** 그냥 두면 한 씬 안에서
  예전 타깃과 새 타깃의 **감도가 10배 차이 난다** — 쓰는 사람은 원인을 모른다.
  그래서 버전 문자열이나 이름이 아니라 **살아 있는 나눗수 값을 읽어**(`slide_scale_of()`)
  다르면 `Create Selected` 가 한 번 재배선하고 로그로 알린다. 리네임도 레퍼런스도 타지 않는다.
- headless(mayapy 2024) core 51 + UI 13 항목 통과 — 한 칸이 반현의 1% · 씬 위치도 배율을 탄다 ·
  예전 나눗수(2.0)로 바꿔 놓으면 알아보고 한 번만 재배선 후 `kept` · v03.07 스위트 무회귀.


> [!summary] `A00060_jointTool_V03` `Chain > Pole Target` 에 **`Slide`** — 폴 타깃을 양 끝 사이로 옮기는 두 번째 어트리뷰트 (v03.06 -> 03.07)
- **요청**: 리스트에 A · B · C 가 있을 때 `Create` · `Create Selected` 로 세팅한 오브젝트에
  **실수 어트리뷰트를 하나** 더 붙이고, 양수면 A 와, 음수면 C 와 가까워지게.
- `poleSlide` 를 달았다. `A' = A + n*v + (s/2)(p1 - p3)` — 현 방향 평행이동이다.
- **★ 슬라이드를 `n` 에 섞지 않는 것이 핵심이었다.** 먼저 떠오른 설계는 기준점 `A` 를
  옮기고 거기서 `n*v` 를 가는 것(`A_s + n(p2 - A_s)`)인데, 그러면 가중치가 `(1-n)*s/2` 가
  되어 **`n > 1` 에서 부호가 뒤집힌다.** 폴 타깃은 보통 `n > 1` 이므로 쓰는 사람 입장에선
  "양수를 넣었는데 반대로 간다" 가 된다. 슬라이드는 **마지막에 더하는 평행이동**이어야 한다.
- **★ 이것도 가중치 합이 1 이라 여전히 `pointConstraint` 하나**다
  (`w0 = (1-n)/2 + s/2` · `w1 = n` · `w2 = (1-n)/2 - s/2`). v03.03 의 전개가 그대로 살아서
  공간 변환은 여전히 컨스트레인트가 공짜로 해 준다.
- **★ `s/2` 는 새 노드 없이 `_side` 의 Y 채널로** 계산했다 — `multiplyDivide` 는 한 노드가
  세 채널이고 `operation`(divide) 은 세 채널에 같이 걸린다. 늘어난 노드는 가중치를
  더하고 빼는 `plusMinusAverage` 둘뿐이다.
- **예전에 배선해 둔 타깃은 `Create Selected` 를 한 번 누를 때 다시 짓는다** — `poleSlide` 가
  없으면 구성이 달라 `kept` 로 둘 수 없고, 그대로 두면 버튼을 눌러도 슬라이드가 안 생긴다.
  대신 한 번만 재배선하고 다음부터는 `kept` 다.
- `Update Selected` 가 `Distance` 와 `Slide` 를 함께 넣는다. `A00130_ControlRig_V02` 는
  `slide` 를 안 넘기므로 놓이는 자리가 예전과 같다(기본 0).
- headless(mayapy 2024) core 41 + UI 11 항목 통과 — 씬의 실제 위치가 수식과 같고(두 모드) ·
  가중치 합 정확히 1 · `n > 1` 에서 부호 안 뒤집힘 · `bake` 가 늘어난 노드까지 치움 ·
  `slide=0` 은 예전과 동일(무회귀).


> [!summary] `A00130_ControlRig_V02` `Constrain` 이 `Pair` 가 맞춰 둔 **회전을 덮어쓰던 것** — maintain offset 기본 ON + 걸기 전후 검증 (v02.16 -> 02.17)
- **요청**: `Constrain` 버튼을 누르는 도중 maintain offset 이 되어 있는지 확인하고, 유지되지
  않으면 유지되게. 지금은 `Pair` 로 회전이 세팅된 pos 오브젝트의 회전이 변하는 것 같다.
- **맞았다.** `constrain_map.json` 의 `maintain_offset` 이 `false` 였다(마야 명령 기본값을
  따랐던 것). 재현: 포즈 오브젝트 회전 `(30, -20, 45)` 가 버튼 한 번에 드라이버의
  `(-70, 15, 120)` 으로 **통째로 덮인다.** 기본을 `true` 로 바꾸고, 키가 없어도 켠 것으로
  읽게 했다(`maintain_offset()`).
- **★ 앞 단계가 세워 둔 것을 다음 단계가 지우면 기본값이 틀린 것이다.** `mo=False` 는 마야
  명령의 기본값일 뿐, `Pair -> Constrain` 순서를 가진 이 파이프라인에서는 **앞 단계를 무효로
  만드는 설정**이다. 명령 기본값을 그대로 따른 것이 원인이었다.
- **★ 켰다고 믿지 않고 잰다.** 오브젝트마다 **걸기 전후의 월드 행렬**을 비교해 위치·회전이
  얼마나 움직였는지 확인하고, `on` 인데도 움직였으면 이름을 짚어 경고한다(마지막 줄에
  `N stayed exactly where they were, M moved`). 잠긴 채널이나 이상한 부모 밑에서는 `mo` 를
  켜도 어긋날 수 있다 — **조용히 틀리는 것이 가장 나쁘다.**
- **★ 회전 차는 오일러로 빼면 안 된다** — `180` 과 `-180` 이 다르게 나와 가만히 있는 것도
  움직인 것처럼 보인다. **세 축 사이의 각** 중 최대로 잰다(`drift()`). `Check` 미리보기도
  거리뿐 아니라 각도를 함께 잰다 — 위치가 같고 회전만 어긋난 짝이 있다.
- headless(mayapy 2024) **24항목** 통과 — 회전·위치 보존 · 드라이버를 움직이면 오프셋을 지킨
  채 따라감 · **대조군(`false`)이 증상을 그대로 재현** · `drift()` 가 5 / 90도 / 180도를 정확히
  읽음 · 잠긴 채널 사전 차단 · 두 번 눌러도 멱등.


> [!summary] `A00130_ControlRig_V02` 템플릿 폴 타깃 4개를 **거리 고정**으로 — 팔을 펴도 팔꿈치와의 거리가 그대로 (v02.15 -> 02.16, A00060 v03.05 -> 03.06)
- **요청**: `helper_polTgt_arm_l` 처럼 약속된 오브젝트 3개로 A00060 폴 타깃 기능을 쓰는
  조인트가 있다. 이걸 **`Fixed distance` 를 켠 상태**, 즉 B(가운데)와 거리가 계속 같은
  세팅이 되도록.
- `orient_manager._do_pole_targets()` 가 `ensure(fixed=True)` 를 쓰게 하고,
  `orient_map.json` 의 `pole_targets` 에 `"fixed": true` 를 두었다(끄면 예전 배선).
- **★ json 의 `distance` 를 그대로 넘기면 타깃이 팔꿈치에 달라붙는다.** 그 값(2.0)은
  **굽은 정도의 배수**로 잡아 둔 것인데 거리 고정 배선은 **씬 거리**를 받는다. 그래서
  A00060 에 `fixed_from_multiple()` 을 두어 **`d = (n-1)*|v|`** 로 환산했다 — 두 식이 같은
  점을 가리키므로 **처음 놓이는 자리가 v02.15 와 한 치도 다르지 않고**(테스트로 좌표 일치
  확인), 그 뒤로만 거리가 유지된다.
- 환산은 **지금 포즈**를 읽으므로 조인트마다 따로 잰다. 일직선이면 `|v|=0` 이라 0 이 되고,
  타깃은 가운데 조인트 자리에 머문다(경고는 그대로 나간다).
- headless(mayapy 2024) **23항목** 통과 — 네 개 전부 fixed 배선 · **옛 배수 결과와 좌표 일치** ·
  팔을 펴도(굽힘 4→0.5) 크게 굽혀도(→20) 거리 4.0 유지 · `fixed=false` 대조군은 4.0 → 2.25 로
  변함 · 두 번째 실행이 맞춰 둔 9.5 를 지키고 떠돌이 계산 노드 0 · `reset_distance` 강제 복원.
  A00060 의 25 + 22항목도 그대로 통과.


> [!summary] `A00060_jointTool_V03` `Chain > Pole Target` **`Fixed distance`** — 체인이 굽어도 가운데 오브젝트와의 거리가 그대로 (v03.04 -> 03.05)
- **요청**: A · B · C 의 위치가 바뀌면 만들어 둔 오브젝트와 B 의 거리가 계속 변한다.
  위치가 바뀌어도 **거리가 일정**하게.
- 근거를 먼저 식으로 확인했다 — 예전 배선의 거리는 `|A' - p2| = |n-1| * |v|` 라
  **굽은 정도(|v|)에 정비례**한다(측정: 굽힘을 키우자 2.0 -> 4.0). 팔을 펴면 타깃이
  팔꿈치로 빨려 들어오는 그 증상이다.
- **★ 정규화를 하면서도 컨스트레인트를 안 버린다.** `A' = p2 + d*v/|v|` 는 `A' = A + n*v`
  에서 **`n = 1 + d/|v|`** 와 같은 식이다. 그래서 `pointConstraint` 구성은 그대로 두고
  거기에 먹이는 `n` 만 상수에서 **계산된 값**으로 바꿨다 — 월드/부모 공간 변환은 여전히
  컨스트레인트가 공짜로 해 준다. 정규화가 필요한데도 노드망은 6개면 됐다.
- **★ `multiplyDivide` 의 0 나누기는 0 도 NaN 도 아니고 `100000` 이다**(실측, 경고만 낸다).
  더 위험한 건 `|v|` 가 **아주 작을 때** — `n` 이 1e9 로 뛰면 가중 평균이 큰 수끼리의
  뺄셈이 되어 자릿수가 통째로 날아간다. 나누기 앞에 `clamp` 로 하한을 잡아 일직선
  체인에서도 어긋남이 `d` 를 안 넘게 했다(타깃은 가운데 오브젝트 자리에 머문다).
- **★ 모드가 다르면 `kept` 가 아니라 다시 짓는다.** 체인이 같으면 `kept` 로 두던 규칙에
  걸려, 체크박스를 켜고 눌러도 **아무 일도 안 일어난 것처럼** 보인다. 재배선할 때
  컨스트레인트만 지우면 계산 노드가 떠돌이로 남으므로, 가중치에서 거슬러 올라가 **우리가
  만든 유틸리티 노드만** 골라 함께 지운다(`helper_nodes()`, `Bake Selected` 도 같은 경로 —
  예전 bake 는 한 단만 지웠다).
- 기본 ON 이고, 끄면 v03.04 까지의 배수 동작 그대로다. **`A00130_ControlRig_V02` 가 쓰는
  `ensure()` 의 기본값은 배수**로 두어 그쪽 템플릿 폴 타깃은 건드리지 않았다.
- headless(mayapy 2024) **25항목** 통과 — 네 포즈에서 거리 유지 · 방향 보존 · `poleDistance`
  가 거리에 1:1(음수는 반대쪽) · 일직선 안전 · undo 한 스텝 · bake/재배선 뒤 떠돌이 0 ·
  모드 전환 · A00130 경로 무변경 · `Check` 미리보기 == 실제. v03.04 스위트 22항목도 통과.


> [!summary] `A00060_jointTool_V03` `Chain > Pole Target` 에 **`Create Selected`** — 새 노드 말고 **고른 오브젝트**에 같은 배선을 건다 (v03.03 -> 03.04)
- **요청**: Pole Target 탭에 `Create Selected` 버튼. 기존 `Create` 의 세로를 줄여 그 빈 자리에.
  리스트에 오브젝트 3개가 있을 때, **씬에서 고른 오브젝트**가 `Create` 를 누른 뒤와 같은
  기능을 갖도록 그 오브젝트를 고친다.
- `pole_target_manager.create_on()` 을 더했다. 이미 있던 `ensure()`(A00130 이 쓰는 경로)를
  선택 목록에 돌리고 가드와 로그를 얹은 것이라 **배선 코드는 한 줄도 새로 안 썼다** —
  `Create` 와 같은 `_wire()` 다.
- **★ 체인 멤버를 고른 채 누르면 순환이 된다.** 리스트의 세 오브젝트 자신에게 이 배선을 걸면
  **자기 자신을 타깃으로 삼는 pointConstraint** 가 된다. 마야는 사이클 경고만 내고 씬은
  망가진 채 남으므로, 걸기 전에 긴 이름으로 비교해 건너뛰고 로그로 알린다.
- **★ 두 번째로 눌러도 거리를 안 덮어쓴다**(`kept`). `poleDistance` 는 실시간으로 맞추라고
  만든 값이라 누를 때마다 스핀박스 값으로 되돌리면 맞춰 둔 것이 매번 날아간다.
  바꾸는 길은 이미 `Update Selected` 로 따로 있다.
- 남이 건 컨스트레인트가 있는 오브젝트는 `ensure()` 가 원래대로 조용히 지우지 않고 건너뛴다.
  여러 개를 골라도 **전체가 undo 한 스텝**(`create_on` 이 통째로 감싼다).
- UI: `Create` 가 쓰던 폭을 **반으로 갈라**(254px씩) 그 옆에 `Create Selected` 를 세웠다.
  `Check` / `Create` / `Create Selected` 가 한 줄이라 **버튼 줄이 늘지 않고**, 아래
  `Update Selected` / `Bake Selected` 줄과도 자리가 맞는다.
- headless(mayapy 2024) **22항목** 통과 — 위치가 `A'` 와 일치 · 체인을 따라옴 · undo 한 스텝 ·
  여러 개 동시 · 체인 멤버 가드 · 리스트 3개 가드 · 두 번째 실행 `kept` · 남의 컨스트레인트 보존.
  coral_dark 테마 실제 창 캡처로 버튼 배치도 확인.


> [!summary] `A00410_SecondaryMotion` **`Rotate Axis` 체크박스 X / Y / Z** — 고른 축에만 기록하고 나머지는 손대지 않는다 (v01.07 -> 01.08)
- **요청**: 세컨더리 모션 키를 찍을 때 `rotateX` / `Y` / `Z` 중 **원하는 축만** 회전하도록
  체크박스 3개를 붙이고, Apply 가 체크한 축만 건드리게.
- Physics 박스 `Substeps` 아래에 `Rotate Axis  [x] X  [x] Y  [x] Z` 를 놓았다(기본 전부 켜짐).
- **★ 축은 물리가 아니라 기록의 문제다.** 솔버는 그대로 3차원으로 푸고(`chain_solver`,
  `pose_builder` 는 손대지 않았다), 커브를 만들고 키를 찍는 `bake_manager` 에서만
  `self.axes` 로 걸렀다. 그래서 빠진 축은 **덮어쓰는 것이 아니라 아예 건들지 않는** 상태가 된다 —
  `Override Layer` 는 그 축을 레이어에 등록하지 않고, `Bake Keys` 는 `cutKey` 조차 하지 않는다.
- **★ 축을 바꾸면 프리뷰 레이어를 지워야 한다.** 살아 있는 레이어에는 이미 예전 축의 커브가
  들어 있어서, 축을 끈 뒤에도 그 커브가 계속 원본을 덮어쓴다(끄는 것처럼 보이지 않는다).
  `set_axes()` 가 바뀜을 때만 프리뷰를 지우고, 샘플 캐시는 축과 무관하므로 **재샘플링은 없다**.
  Apply 쪽도 프리뷰 승격(promote) 판정 **앞에** 축을 확정해야 예전 축의 레이어가 승격되지 않는다.
- **★ 마지막 한 축은 꺼지지 않게** 했다. "축이 하나도 없음" 은 예외 경로를 열어야 하는 상태인데,
  체크를 되돌리면 그 상태 자체가 생기지 않는다.
- 결과는 "그 평면으로 시뮬레이션한 것" 이 아니라 **3차원 결과 중 그 축의 오일러 성분만 쓴 것**이다.
  문서(4.3)에 이 구분을 명시했다 — 스윙이 거의 없는 축만 남기면 결과도 거의 없다.
- headless(mayapy 2024) core 23 + UI 11 항목 통과 — 레이어에 고른 축의 커브만 들어가고 ·
  `Bake Keys` 가 다른 축의 **원본 키 시간을 그대로** 남기며 · 축 변경이 프리뷰를 재생성하고 ·
  **XYZ 세 축은 예전 결과와 완전히 동일**(무회귀) · UI 마지막 축 해제가 되돌려진다.


> [!summary] `A00145_RigConnect` Connect > `Pair` 에 **`Swap` 버튼** — 두 리스트를 맞바꿔 constraint 방향만 뒤집는다 (v01.38 -> 01.39)
- **요청**: Pair 탭의 두 TSL 을 swap 할 수 있게 `Swap` 버튼 추가.
- 버튼은 두 리스트의 `Sort` **아래에 상자 전체 폭**(573px)으로 놓았다. 리스트 하나에 딸린
  버튼이 아니라 **둘 다에 걸리는** 동작이라 폭이 맨 아래 `Connect` 와 같다. 동작은 Match 탭의
  `Swap`(`Targets` <-> `Followers`) 과 **같은 이름 · 같은 동작**이다.
- **★ 짝은 자리로 서 있으므로 행 순서를 그대로 맞바꾸면 된다.** `Match by Name` 이 세워 둔
  짝과 짝 없는 자리를 지키는 `(Null)` 행까지 그대로 따라가므로, **`List order` 로 세워 둔 짝을
  다시 담지 않고 방향만 반대로** 걸 수 있다. `Pairing` 라디오는 건드리지 않는다.
- headless(mayapy 2024) 확인 — `(Null)` 이 낀 3행짜리 두 리스트가 자리 순서 그대로 맞바뀌고,
  teal_dark 테마를 입힌 실제 창 캡처로 배치와 폭(573px = Set Up 상자 전체)까지 확인.

---

## 2026-09-09

> [!summary] 공용 falloff 커브 — **탄젠트(Bezier)**: 포인트 사이를 곡선으로, break 로 좌우 독립, 길이 조절 (A00410 v01.06 -> 01.07, A00275 v01.20 -> 01.21)
- **요청**: 지금은 포인트 사이가 선형뿐이다. 각 포인트에 **탄젠트 UI** 를 붙여 곡선 보간이
  되게 하고, 일반 탄젠트 / **break**(좌우 독립) / **길이 조절**까지. 쓰는 툴 전부에.
- `Interpolation` 에 **Bezier** 를 추가했다. 그 모드에서만 포인트마다 탄젠트가 붙고 구간이
  3차 베지어가 된다 — **나머지 보간은 탄젠트를 아예 안 보므로 예전 커브는 그대로**다.
  탄젠트 목록은 포인트와 나란한 **별도 인자**라 옛 호출(`evaluate(points, interp, t)`)도 그대로 돈다.
- **★ 각도를 '핸들이 뻗는 방향' 으로 잰다**(in 은 -x 쪽). 그래서 **끊지 않은 탄젠트는 두 각도가
  같다** — 화면의 "한 직선" 과 숫자가 어긋나지 않는다. 길이는 끊지 않아도 좌우가 따로 논다
  (마야 weighted tangent 와 같은 감각).
- **★ 커브가 함수로 남게 제어점 x 를 가둔다**(`x0 <= cx0 <= cx1 <= x1`). 핸들을 최대로 빼도
  x 가 되돌아가지 않아 "한 x 에 값이 둘" 인 상태가 생기지 않는다(단조성 테스트로 확인).
- **★ 포인트와 탄젠트는 반드시 같이 정렬한다**(`normalize_curve`). `normalize_points` 는 x 로
  정렬하므로 탄젠트를 따로 정리하면 **짝이 조용히 어긋난다**. 포인트 삭제/추가도 같은 자리에서 처리.
- A00275 쪽은 (포인트, 보간, 탄젠트)를 **콜러블 하나**(`_curve_fn`)로 묶어 내부에 넘기게 바꿨다 —
  커브를 이루는 값이 셋이 되면서 내부 함수마다 인자를 셋씩 나르던 것을 한 군데로 모았다.
- **테스트가 내 기대를 두 번 고쳤다**: (1) x 를 이분법으로 되찾으므로 y 는 **1e-7 수준**까지만
  맞는다(24회 → t 정밀도 6e-8). (2) **y=1 에서 위로 민 탄젠트는 `clamp01` 에 잘려 여전히
  평평하다** — `is_flat` 테스트는 아래로 밀어야 한다.
- 비용: 베지어 25,000회 평가 **0.29s**(linear 0.05s). 정점마다 부르는 Expand Bind 에서도
  체감되지 않지만 6배쯤 비싸다.
- headless(mayapy 2024) 46항목 통과 — 자동 탄젠트가 직선을 유지 · 포인트를 정확히 통과 ·
  길이가 셀수록 세게 끈다 · break/이어붙이기 · 핸들 드래그(핸들이 포인트보다 먼저 잡힌다) ·
  포인트를 지우면 탄젠트도 함께 · **A00275 바인드와 A00410 솔버까지 탄젠트가 전달**.
  기존 스위트 125항목도 전부 통과.


> [!summary] 공용 falloff 커브 위젯 — **포인트 값을 숫자로**(X / Y 입력칸 2개). 쓰는 툴 둘 다 함께 (A00410 v01.05 -> 01.06, A00275 v01.19 -> 01.20)
- **요청**: `MOD_falloffCurve_qt_v01` 에 실수 입력을 받아 그래프 포인트 값을 정하는 UI.
  가로축·세로축 **둘 다** 정할 수 있게 입력칸 2개. 이 코드를 쓰는 모든 툴이 쓸 수 있도록.
- 캔버스에 **선택된 포인트** 개념을 넣고(`selectionChanged`), 패널에 `Point [2 / 4] X [] Y []`
  줄을 붙였다. 공용 위젯이라 **A00275 Expand Bind 와 A00410 Graph 팝업이 자동으로** 얻는다.
- **★ 범위 규칙을 드래그와 한 곳에서 공유한다.** 숫자 입력이 드래그보다 느슨하면 커브가
  깨진다 — 양 끝 포인트는 x 가 0/1 고정이라 **X 칸을 꺼 두고**, 가운데는 이웃을 못 넘게
  X 범위를 이웃 사이로 좁힌다(`x_bounds()`). **클램프된 값은 칸에 되돌려 준다** —
  안 그러면 "왜 0.95 가 안 들어가지" 가 된다.
- **★ 되먹임을 빗장으로 막는다.** 칸 -> 커브 -> `changed` -> 칸 갱신 -> 칸 시그널 ... 로 도는 것을
  `_updating` 플래그로 끊었고, 같은 값을 다시 넣으면 `set_point` 이 아예 `changed` 를 안 낸다.
- **★ 스핀박스는 `setKeyboardTracking(False)`** — 값을 되쓰는 칸이라 타이핑 중간값을 받으면
  `0.1` 을 치는 도중 `0.100` 으로 잘린다([[qdoublespinbox-keyboard-tracking]]).
- 빈 곳에 더블클릭해 만든 포인트는 **바로 고른 상태**가 되어 곧장 숫자로 다듬을 수 있고,
  프리셋으로 포인트 수가 줄면 선택을 정리한다. 아무것도 안 골랐으면 두 칸 다 꺼진다.
- headless(mayapy 2024) 검증 38항목 — 실제 클릭 이벤트로 선택/해제, 클램프(양 끝 x 고정 ·
  이웃 넘지 못함 · 0~1), 칸<->커브 양방향 동기화, 되먹임 없음,
  **A00275 창과 A00410 Graph 팝업에서 숫자로 넣은 값이 각각 커브와 `SolverParams` 까지 도달**.
  기존 스위트(커브 33 · Loop 25 · 진행률 29)도 전부 통과.


> [!summary] `A00410_SecondaryMotion` **파라미터 커브(Graph)** — Stiffness/Damping/World Damp 를 체인 위치에 따라 + 커브 UI 를 Framework 로 승격 (v01.04 -> 01.05, A00275 v01.18 -> 01.19)
- **요청**: 세 슬라이더 옆에 `Graph` 버튼 → 커브 팝업. UI 는 `A00275` Expand Bind 의 Falloff
  curve 를 그대로(Interpolation · Curve presets 포함). 커브 값은 수치에 **곱해지고**, 가로축은
  체인의 처음→끝. 기본은 전 구간 1. 공용 UI 로 승격해도 좋다.
- **★ 승격이 곧 A00275 의 코드를 줄였다.** `app/core/falloff.py` → `Framework/core/falloff_curve.py`,
  `app/ui/falloff_curve_widget.py` → `Framework/qt/MOD_falloffCurve_qt_v01.py`. 커브 +
  Interpolation + Curve presets 세 줄을 공용 **패널** 하나로 바꾸면서, **프리셋이 보간까지 바꾸므로
  콤보를 맞춰 두던 동기화**(`_sync_eb_interp_combo`)가 툴에서 사라졌다 — 위젯이 맡는다.
- **★ 곱하는 순서를 예전 그대로 두는 것이 무회귀의 조건이었다.** fps 보정(`_fps_adjust`)은
  **커브를 곱하기 전 기본값에** 건다. 커브를 곱한 뒤 보정하면 커브가 평평해도 24fps 아닌 씬에서
  결과가 미세하게 달라진다. 커브는 노드마다 한 번만 평가해 배열로 들고 간다(안쪽은
  프레임 x 노드 x 서브스텝).
- **★ "커브를 안 건드린 상태" 를 `None` 으로 만든다.** UI 는 커브가 평평한 1.0 이면 솔버에
  `None` 을 넘긴다 — 평가를 아예 건너뛰어 예전과 **같은 코드 경로**가 되고, 버튼 표식(`Graph *`)
  판정도 같은 `is_flat()` 하나로 끝난다.
- **★ 대조군을 잘못 잡아 테스트가 한 번 틀렸다.** `falloff=0` 으로 대조군을 만들었더니 모든 노드의
  stiffness 가 같아 **체인이 통째로 강체처럼 늦어졌고**(자식 로컬 회전이 전부 0, 흔들림이 루트 회전
  하나로 감) 비교가 무의미했다. 대조군은 기본값 `falloff=0.5` 로. 또 "커브 왼쪽=1 이니 루트쪽은
  그대로" 도 틀린 기대였다 — 커브는 **노드 위치마다** 평가되므로 정확히 1.0 인 곳은 루트뿐이다.
- 검증(mayapy 2024, 33항목): **상수 0.5 커브 == 값을 절반으로 준 것과 완전히 동일**(세 파라미터
  모두, 대수적 확인) · 전 구간 0 인 World 커브 == `World Damp 0` · 평평한 커브 == 커브 없음 ·
  요청 예시(1→0.1)에서 느슨해지는 정도가 팁 쪽이 루트 쪽의 **3.8배** · `Loop` 와 함께 써도
  이음매 0.000000deg · A00275 창 생성/프리셋/콤보 동기화 무회귀.


> [!summary] `A00410_SecondaryMotion` **Loop 체크박스** — 구간을 사이클로 풀어 0f 와 100f 가 같아지게 (v01.03 -> 01.04)
- **요청**: Loop 를 켜면 세컨더리가 적용된 모든 컨트롤러/조인트가 **사이클**이 되게 할 것.
  0~100f 애니가 순환한다고 할 때 0f 와 100f 의 위치·회전이 같아야 한다. "0~100 을 두 번 돌려
  100~200 구간을 쓰는" 방식도 좋다. 0f 회전이 0 이 아니게 되어도 된다.
- **끄면 왜 루프가 아닌가**: 솔버가 **첫 프레임에 정지 상태로 출발**하기 때문이다. 원본이 완벽한
  루프여도 첫 프레임만 흔들림 0 이고 마지막 프레임은 흔들리는 중이라 이음매에서 튄다.
  그래서 요청대로 **프리롤**을 넣었다 — 같은 구간을 여러 바퀴 이어 붙여 풀고 마지막 한 바퀴만 쓴다.
  과도응답이 바퀴마다 기하급수로 줄어 **정상상태(limit cycle)** 가 된다.
- **★ 이어 붙이는 방식이 요점이다.** `targets[:-1] * (n-1) + targets` — **마지막 바퀴의 목표열이
  원본과 정확히 같아야** 잘라낸 구간의 f 번째가 원본 f 번째 프레임과 1:1 로 맞는다. 반대로 붙이면
  (앞을 원본으로 두고 뒤에 반복을 붙이면) 결과가 한 프레임씩 밀린 목표에 대응해 회전 재구성이 어긋난다.
- **★ 바퀴 수는 고정하지 않고 이음매를 재서 정한다.** 필요한 바퀴 수는 감쇠에 달렸다 →
  2 -> 4 -> 8 -> 16 으로 늘리며 닫힐 때까지(전부 다시 풀어도 총비용은 마지막 한 번의 2배 이내).
  `damping=0` 처럼 **정상상태가 아예 없는** 설정은 16바퀴 뒤에 못 닫았다고 정직하게 알린다.
- **★ 위치 오차는 회전 오차보다 관대해 보인다.** 허용 오차를 체인 길이의 1e-4 로 뒀더니 **위치
  이음매는 통과인데 회전 키가 0.05deg 벌어졌다**(체인을 내려가며 부모의 스윙 델타가 누적된다).
  한 바퀴 더 도는 값이 싸서 1e-6 으로 조였다 → 회전 이음매 **0.000000deg**.
- 입력 자체가 순환하지 않으면(첫/끝 포즈가 다르면) 로그로 먼저 알린다 — 루프의 전제라서
  결과를 보고 헤매기 전에 원인을 짚어 준다.
- headless(mayapy 2024) 검증 25항목 전부 통과 — 조인트 6본 x 0~100f 에서 **회전 키 0f == 100f
  (Loop OFF 는 1.484deg)**, Bake 후 **씬 실측** 월드 위치 차 0.000000 · 회전 차 0.000002deg,
  오프셋 그룹이 낀 컨트롤러 + Override Layer 경로도 0.000003deg, 길이 구속 유지,
  **Loop OFF 무회귀**(기본 False · 결과 동일 · 첫 프레임 = 원본).
- 성능: 20본 x 300프레임 솔브 0.034s -> **0.048s**(2바퀴), 프리뷰 0.043s -> **0.054s** — 루프를
  켜도 프리뷰는 그대로 실시간이다.


> [!summary] `A00410_SecondaryMotion` Apply — **0~100% 게이지 팝업**으로 계산 진행을 보여준다 + 공용 진행률 위젯 승격 (v01.02 -> 01.03)
- **요청**: Apply 를 누른 뒤 계산이 끝날 때까지 아무 안내가 없다. 0%~100% 게이지 팝업으로
  진행도를 알 수 있게 할 것.
- **★ 진행률을 이 툴 안에 두지 않았다.** 팝업은 `Framework/qt/MOD_progress_qt_v01.py`
  (`JUN_mod_progress_qt`) 로 **공용 위젯 승격** — DemBone 은 창에 붙은 게이지, Wrapper 는 로그
  줄로 각자 다르게 알리고 있었고, "무거운 작업이 도는 동안 뜨는 팝업" 은 어느 툴에나 같은 모양이다.
  단계 가중치 · 콜백 어댑터 · 갱신 스로틀을 위젯이 갖는다.
- **★ core 는 위젯을 모른다.** `prepare` / `solve` / `ensure_layer` / `write_curves` /
  `bake_keys` 와 `outputs.py` 의 출력 spec 이 전부 `progress(done, total, message=None)`
  **콜백만** 받는다. `None` 이면 예전 경로 그대로라 **13ms 짜리 프리뷰에는 아예 붙이지 않았다.**
- **★ 단계는 실제로 도는 것만 넣고 가중치를 재정규화한다.** 캐시가 살아 있으면 `Sampling scene`
  단계가 목록에서 빠지고 나머지가 0~100% 를 채운다 — 게이지가 중간에서 멈추거나 건너뛰지 않는다.
  가중치는 실측 비용에 맞췄다: 샘플링 30 / 솔브 5 / **Bake Keys 65**(노드 × 프레임 `setKeyframe`
  이라 압도적으로 무겁다) / 레이어 기록 40 / 프리뷰 레이어 승격 5.
- **★ 값은 늘 반영하고 `processEvents()` 만 묶는다.** 처음엔 퍼센트 갱신 자체를 30ms 로 스로틀했는데,
  그러면 **갱신이 뚝 끊긴 순간의 퍼센트가 화면에 영영 안 올라간다**(테스트가 이걸 잡았다).
  비싼 건 `setValue` 가 아니라 `processEvents` 다 — 스로틀은 그쪽에만.
- **덤으로 나온 버그 2개**: 프리뷰를 **끈 채** 슬라이더를 만지고 Apply 하면 앞서 만든
  `_last_writes` 를 그대로 써서 **옛 값이 구워졌다**(슬라이더는 캐시를 무효화하지 않는다)
  → Apply 는 항상 다시 푼다. 그리고 디바운스(40ms)가 터지기 전에 Apply 하면 **한 단계 전 프리뷰가
  승격**됐다 → 대기 중인 타이머를 먼저 반영한다.
- headless(mayapy 2024) 검증 24항목 전부 통과 — 가중치 환산/재정규화, 샘플링 콜백이 프레임마다
  40회 단조 증가, Bake total = 노드 × (프레임+1) 이고 마지막 보고가 정확히 100%,
  레이어 total = 2 × 노드, 승격 경로는 0/1 → 1/1, `progress=None` 무회귀.


> [!summary] `A00400_CurveTool` Edit > Smooth — **닫힌 커브에 한 번 적용하면 그 뒤로 아무것도 안 되던 것** 수정 (v01.08 -> 01.09)
- **증상**: 닫힌 커브에 Smooth 를 걸면 `Smooth 0.070 -> 1 curve(s), 12 of 12 CV(s) moved`
  까지는 되고, 그 다음부터 `Select some curve CVs first ...
  [RuntimeError: (kFailure): Object does not exist]` 만 떴다.
- **★ 뒤에 붙은 예외가 원인이 아니라 증거였다.** `Object does not exist` 는 **빈 선택에서
  `getRichSelection()` 이 던지는 것** — 즉 진짜 문제는 "적용하고 나면 선택이 사라진다" 였다.
  이 툴은 슬라이더를 놓을 때마다 선택을 다시 읽으므로, 한 번 풀리면 그 뒤로 아무것도 안 된다.
- **★ `cmds.curve` 는 만든 커브를 선택 상태로 만든다.** 임시 사본을 만드는 경로가 열린 커브는
  `cmds.duplicate`(선택을 안 건드린다), 닫힌 커브는 `cmds.curve`(감아 넣은 커브를 새로 만든다)라
  **닫힌 커브에서만** 증상이 났다. 이어서 `cmds.delete` 가 그 선택을 비운다.
- 선택을 건드리는 구간을 공용 `keep_selection()` 컨텍스트로 묶었다 — 임시 커브 **생성 · 삭제 ·
  `smoothCurve`** 세 군데 전부. 이 툴에서 선택을 지우는 마야 명령을 찾은 것이 이제 셋이라
  한 군데서 관리한다.
- headless(mayapy 2024) 검증 — 닫힌 · 닫힌+히스토리 · 열린 커브 각각 **연속 3회 적용** 후에도
  선택이 그대로 · 드래그 세션 중/후 선택 유지 · 임시 커브 잔여 없음 ·
  **그 다음 `capture()` 가 여전히 CV 를 찾는다**(리포트된 증상 그 자체).


> [!summary] `A00400_CurveTool` Edit > Smooth — **닫힌(주기) 커브**도 열린 커브와 똑같이 Smooth / Rough (v01.07 -> 01.08)
- **요청**: 지금은 Smooth 탭에서 닫힌 커브를 스무딩할 수 없다. 열린 커브와 똑같이(혹은
  유사하게) 닫힌 커브도 스무딩되게 할 것.
- **막고 있던 것은 툴이 아니라 마야였다.** `cmds.smoothCurve` 는 주기 커브를 거절한다
  (`Cannot smooth CVs on periodic curves`). 그래서 툴은 그 커브를 `capture()` 단계에서
  **통째로 건너뛰고** 사유만 로그에 적고 있었다.
- **★ 대체 스무딩을 새로 짜지 않고 마야 것을 그대로 쓴다.** 라플라시안 같은 자체 구현을
  얹으면 열린 커브와 닫힌 커브의 **감촉이 갈라진다** — "열린 커브와 똑같이" 라는 요청과 어긋난다.
  마야가 못 하는 건 계산이 아니라 **이음매를 넘어가는 이웃 관계**뿐이므로, 닫힌 커브의 CV 목록을
  앞뒤로 **감아 복사해 늘린 열린 임시 커브**를 만들어 거기에 `smoothCurve` 를 돌리고
  **가운데 구간만** 읽어 온다. 마야가 끝을 고정하는 것은 패딩 구간에서만 일어난다.
- **★ 결과가 "순환 스텐실" 과 소수점까지 같다.** 마야의 내부 연산자를 임펄스 응답으로 뽑아 보면
  degree 3 의 내부 스텐실은 `[-1/18, 2/9, 2/3, 2/9, -1/18]`(합 1)이고, 위 방식의 결과는 그것을
  순환으로 건 것과 **오차 `8.9e-16`** 로 일치한다. 패딩은 `2 * degree + 4` 면 충분하다 —
  degree 7 까지 패딩을 40 으로 키운 결과와 비트 단위로 같다(실측).
- **★ 주기 커브는 CV 가 두 가지로 세어진다.** `.cv[i]` 로 고를 수 있는 것은 `spans` 개인데
  `MFnNurbsCurve.cvPositions()` 는 `spans + degree` 개를 준다 — 뒤의 `degree` 개는 앞의 복사본.
  쓸 때 **그 복사본까지 같이 갱신**하지 않으면 이음매가 벌어진다.
- **★ 주기 커브에는 `cmds.curve(replace=True)` 가 그냥은 안 통한다** —
  `Must specify knots with the -per option`. 원본의 `periodic` + `knot` 을 다시 넘겨야 형태가
  열린 커브로 바뀌지 않는다. `setAttr .controlPoints` 로 쓰는 길은 **버렸다** — 히스토리가 붙은
  커브(`makeNurbCircle` 이 살아 있는 원)에서는 그 값이 **절대 위치가 아니라 트윅(델타)** 이라
  같은 값을 다시 써 넣기만 해도 형상이 두 번 섞인다.
- 닫힌 커브에는 **고정되는 CV 가 없다** — `pinned_indices()` 가 빈 목록을 주고,
  `Check Selection` 은 커브마다 `open` / `closed` 를 함께 적는다. 안내 문구도 "열린 커브에서는"
  으로 좁혔다.
- headless(mayapy 2024) 검증 — 닫힌 커브 순환 스텐실 일치 · 이음매 복사본 동기화 ·
  **이음매 CV(`cv[0]` + 마지막)만 고른 경우** · 부분 선택과 Rough 대칭 · degree 5 ·
  히스토리 살아 있는 원 · 3스팬 최소 커브 · 드래그 중 무누적과 임시 커브 정리 ·
  **undo 1스텝** · 열린+닫힌 동시 선택, 그리고 **열린 커브 결과가 이전과 완전히 동일**.

---

## 2026-09-08

> [!summary] `docs` **README · 포트폴리오(EN/KR) 9월 초 작업 반영** — 리그 미러링(3-5) · 공용 미러 토큰 규칙 · Copy Weights Blend
- 포트폴리오 기간을 **`2026-05-06 ~ 2026-09-08`(약 18주)** 로 늘리고, 새 절 **`3-5. 리그 미러링`**
  (계층 · 스킨 웨이트 · 컨스트레인트 · 임의의 노드망을 한 번에)을 EN/KR 양쪽에 추가.
- 툴 표의 `A00145_RigConnect` · `A00275_skinTool_V01` 행에 Mirror 탭 · Pair / Update · Copy Weights(`Blend`) ·
  Expand Bind `Even distribution` 을 반영.
- `README.md` 갱신 이력 표에 **`2026-09 초`** 4행 추가 — `A00145` Mirror / Pair / Update · `A00275` Copy Weights ·
  `A00290` Target Order · `A00400` Edit > Joints · `A00460` FK & IK · `A00090` Pose Wrangler export.
  파일: `README.md` · `docs/portfolio/portfolio_EN.md` · `docs/portfolio/portfolio_KR.md` `#docs` `#portfolio`

> [!summary] `A00275_skinTool_V01` Copy Weights — **`Blend` (0~1)** 로 옮겨지는 웨이트가 얼마나 실릴지 조절 (v01.17 -> 01.18)
- **요청**: Copy Weights 탭에서 `[0,1]` 실수로 블렌딩 정도를 조절할 것. `0.5` 면 옮겨지는
  웨이트가 절반만 대상 버텍스에 영향, `1` 이면 전부 전이.
- 식은 목표의 **원래 웨이트와 소스 웨이트 사이의 자리**다 —
  `새 웨이트 = (1 - Blend) x 원래 + Blend x 소스`. 기본 `1.0` 은 v01.17 과 완전히 같다.
- **Blend 는 정규화를 깨지 않는다.** 합이 1 인 두 행의 **볼록결합**은 다시 합이 1 이라,
  둘 다 정규화돼 있었다면 결과도 정규화돼 있다 — 그래서 `normalize=False` 를 그대로 둔다
  (여기서 마야에게 정규화를 맡기면 그것은 이미 "그대로 복사" 가 아니다).
- **Blend 가 1 이면 목표의 원래 웨이트를 아예 읽지 않는다.** 어차피 전부 덮어쓰므로 읽는 비용
  (버텍스 x 인플루언스)이 그대로 낭비다 — 기본값 경로는 **값도 비용도 v01.17 과 같다.**
- 읽는 컴포넌트를 쓸 때와 **같은 것**으로 두어 행 순서가 어긋날 여지를 없앴다
  (섞으려면 목표의 현재 웨이트를 한 번 더 읽어야 하는데, 여기서 순서가 어긋나면 조용히 틀린다).
- 스핀박스는 `keyboardTracking(False)` — 값을 되쓰는 위젯은 타이핑 중간값이 새면 안 된다.
  범위 밖 값은 `clamp01`, `0.0` 이면 아무것도 안 바뀌었다고 로그에 남긴다.
- headless(mayapy 2024) 검증 — blend `1.0 / 0.5 / 0.25 / 0.0` 의 결과가 식과 **1e-12 이내**로
  일치 · 목표 행 합이 전부 `1.0` · 목표가 아닌 버텍스 무변화 · 범위 밖 입력 클램프 ·
  기본값이 소스 행과 **완전히 동일** · UI 스모크(스핀박스 기본값/범위/tracking + 실제 PASTE).

---

## 2026-09-07

> [!summary] `A00145_RigConnect` **Mirror 탭 신규** — 계층을 통째로 반대쪽으로(스킨 · 컨스트레인트 · 클러스터 · **임의의 노드망**까지) + 컨트롤러용 **Reflect** 모드 + 좌/우 토큰 규칙을 `Framework/rules` 공용으로 (v01.37 -> 01.38)
- **요청**: TSL 에 담은 오브젝트(와 자식들)를 미러하되 **웨이트 · 컨스트레인트 · 클러스터**
  관계가 유지될 것. 평면 3종(YZ 기본) · 조인트/커브의 Behavior·Orientation(기본 Behavior) ·
  토큰 없는 이름은 경고 후 중단(`Disable token check` 로 해제). 토큰 규칙은 `A00110` 것을
  여러 툴이 공유하게 `Framework/rules` 로 옮길 것.
- **토큰 규칙을 `Framework/core/mirror_tokens.py` + `Framework/rules/mirror_tokens.json` 로 이전.**
  `A00110_animTool_V02` 쪽은 기존 import 경로를 살리는 얇은 재노출만 남겼다. 한쪽에서 토큰을
  고치면 양쪽에 적용된다.
- **★ 이름 미러는 단순 substring 치환이면 조용히 틀린다.** `_l` 을 그냥 바꾸면
  `sample_lip_l_ctl` → `sample_rip_l_ctl`, `arm_lower` → `arm_rower`, 우선순위가 위인 `_l` 이
  `jnt_lf_01` 을 삼킨다. 그래서 **토큰 경계에서 끝나는 occurrence 만** 인정한다(뒤가 `_`/끝/
  숫자/대문자). 그러면 `jnt_lf_01` 이 `_lf` 쌍까지 내려가고 `arm_lower` 는 "토큰 없음" 으로
  제대로 걸린다. 미러 툴에서 이름이 어긋나면 엉뚱한 노드에 웨이트를 얹는다.
- **★ Behavior 행렬을 Maya 와 대조해 확정했다.** 평면의 **법선 축**만 알면
  Orientation = 축 그대로 + 위치만 반사, Behavior = **각 축에서 법선 성분만 남기고 나머지 둘을
  뒤집기**(= 반사 후 세 축 전부 뒤집기 — 그래야 행렬식이 양수로 돌아와 오른손계 유지).
  mayapy 2024 에서 `mirrorJoint -mirrorYZ -mirrorBehavior` 와 **행렬 성분 단위로 일치**하는 것을
  확인했고, `-mb off` 는 회전이 원본과 완전히 동일하다는 것도 같이 확인했다.
- **컨스트레인트가 아닌 노드망도 미러한다.** `crv -> pointOnCurveInfo -> fourByFourMatrix
  -> multMatrix -> decomposeMatrix -> jnt` 처럼 **한 종류로 특정할 수 없는** 유틸리티 노드망을
  복제하고 양쪽 끝을 갈아끼워 다시 잇는다. 찾는 법은 스코프 오브젝트의 **구동 플러그**에서
  거슬러 올라가되 **DAG 노드에서 멈추는 것** — DAG 노드는 미러 대상이면 리스트에 있어야 하고,
  아니면 공유 드라이버다. 지오메트리 입력은 일부러 안 본다(따라가면 씬 절반이 딸려온다).
  - **★ 나가는 연결의 도착지가 스코프 밖이면 잇지 않는다.** 이으면 그 노드를 **양쪽에서**
    구동해 버린다.
  - **★ 네트워크는 트랜스폼이 아니라 셰이프에 붙는 일이 흔하다**
    (`crv.worldSpace[0] -> pointOnCurveInfo.inputCurve`) → 셰이프 짝도 지도에 넣어야 한다.
  - **★ `expression` 은 데려가면 안 된다** — 식 안에 원본 이름이 문자열로 박혀 있어
    복제하면 미러본이 **원본을 또 구동**한다. `animCurve*`/`animBlendNode*`/`pairBlend` 도
    뺀다(애니메이션은 미러 대상이 아니고, 블렌드는 컨스트레인트 재생성과 겹친다).
  - 박혀 있는 값(연결이 아닌 `multMatrix.matrixIn` 같은 고정 오프셋)은 그대로 복사되므로
    로그로 알린다. **월드 값을 `parentInverseMatrix` 없이 로컬 채널에 바로 꽂은 네트워크**는
    부모가 원점이 아니게 되는 순간 결과가 달라지는데, 미러하면 반드시 그렇게 된다 —
    미러의 문제가 아니라 원본 리그의 성질이다(`parentInverseMatrix` 를 물린 리그는 그대로 대칭).
- **컨트롤러용 `Reflect` 모드 추가(기본값).** 그룹에 넣고 월드 `scaleX` 를 -1 한 것과
  **같은 상태**다. 로컬 X,Y,Z 가 월드 -X,+Y,-Z 를 향하던 컨트롤러를 YZ 로 Reflect 하면
  미러본의 로컬 축이 +X,+Y,-Z 가 되어, 로컬 +X/+Y/+Z 로 옮기면 월드 +X/+Y/-Z 로 간다(실측).
  행렬은 그냥 `M·S` — 행렬식이 음수라 한 축의 스케일이 -1 로 남는데, 그게 이 미러의 정의다.
  - **★ 계층 전체에 Reflect 를 쓰면 후손의 로컬 트랜스폼이 원본 그대로다**
    (`local = (M_자식·S)(M_부모·S)⁻¹ = M_자식·M_부모⁻¹`) — 뒤집힘은 맨 위 노드 하나만 갖는다.
    "복제 → 그룹에 넣고 scaleX -1 → 루트에 프리즈" 와 정확히 같은 결과다.
  - 조인트 라디오에는 Reflect 를 주지 않는다. 메시는 Reflect 를 골라도 **Orientation 으로
    놓고 지오메트리를 반사**한다 — 그래야 월드가 오른손계로 남아 노멀과 스킨이 성립한다.
- **★ Behavior 는 회전을 미러하지, 이동을 미러하지 않는다.** 양쪽에 같은 `rotateZ +40` 은
  좌우 대칭이지만 같은 `translateY +2` 는 **반대로** 간다(로컬 Y 축이 뒤집혀 있으니 당연하다).
  실측으로 확인해서 클러스터 핸들처럼 이동으로 구동하는 것은 `Curves / Others` 를
  Orientation 으로 두라고 문서·툴팁에 못박았다. mirrorJoint 의 Behavior 도 같은 성질이다.
- **★ 메시는 트랜스폼만으로는 안 뒤집힌다.** Behavior/Orientation 둘 다 강체 회전이라 왼쪽
  신발이 오른쪽에서도 왼쪽 신발이다. 트랜스폼을 규칙대로 놓은 뒤 오브젝트 공간에서
  보정 행렬 `C = (M·S)·M_new⁻¹` 로 정점을 한 번 더 반사하고 노멀을 뒤집는다. 정점 순서가
  보존되므로 스킨·클러스터 웨이트는 인덱스 그대로 옮겨진다.
- **★ 스킨된 메시의 복제본은 트랜스폼이 잠긴 채로 나오고, `xform` 은 잠긴 채널에 조용히
  아무것도 안 한다.** 히스토리를 지워도 잠금이 남는다. 게다가 위의 지오메트리 보정이
  **결과를 가려서** 월드 형상은 맞아 보이고 트랜스폼만 엉뚱한 자리에 있었다 — 처음엔
  메시만 안 움직이는 걸로 보였다. 놓기 직전에만 풀고 되돌리며, **적용 뒤 월드 행렬을 되읽어
  확인**한다(실패하면 로그에 남긴다).
- **★ 마야는 트랜스폼을 리네임하면 셰이프를 알아서 따라 바꾼다.** 그걸 모르고 셰이프 이름까지
  미러하면 이미 맞는 `mesh_r_01Shape1` 을 `mesh_l_01Shape1` 로 **되돌려 버린다**. 마야가 손대지
  않은 셰이프만 바꾸도록 고쳤다.
- **토큰이 없어 멈출 때는 이름을 찍고 세트로 묶는다.** 걸린 오브젝트 이름을 전부 로그에
  (한 줄에 4개씩) 찍고, `mirror_noToken_set` 하나로 묶어 **선택**까지 한다 — 이름만 찍어
  두면 결국 씬에서 다시 찾아야 한다. 세트 이름은 고정이고 **비워서 재사용**한다(같은 이름으로
  `cmds.sets` 를 또 부르면 `..._set1`, `...2` 로 쌓여 어느 것이 방금 것인지 알 수 없어진다).
  - **★ 예외로 던지면 반환값(warnings)이 통째로 사라져 이름이 로그에 안 남는다.**
    `MissingTokenError` 에 이름 목록·세트 이름·로그 줄을 실어 보내고 UI 가 먼저 찍은 뒤
    다시 던지도록 했다.
- **스코프는 리스트가 정한다.** 리스트에 없으면 복사하지 않는다 — 스코프 밖 메시가 미러 대상
  조인트에 바인드되어 있어도 그 메시는 그대로 두고, 스코프 밖 드라이버/인플루언스는
  **그 노드를 그대로 참조**한다(센터 조인트·센터 컨트롤이 자연히 처리된다).
- 컨스트레인트는 **어떤 채널을 실제로 구동하는지 연결로 판정해** skip 을 재현한다
  (키가 있으면 `pairBlend`, 레이어면 `animBlendNode*` 를 한 홉 거쳐 들어오므로 2홉까지 본다).
  미러된 오브젝트가 이미 제자리에 있으므로 `maintainOffset=True` 로 만들면 원본이 오프셋을
  갖고 있든 아니든 그대로 재현된다.
- 클러스터는 `cluster -wn <미러된 핸들> -bindState` 로 만들어 생성 직후 형상이 튀지 않게 했다.
- headless(mayapy 2024) 검증 — 사용자 예시 씬 그대로(그룹·조인트 체인·컨트롤 체인·메시 2개·
  스킨 2개·parentConstraint·클러스터) 미러 후 위치/행렬/스킨 인플루언스/웨이트/컨스트레인트
  타깃/클러스터 웨이트 대조 · Behavior 대칭 동작 · Orientation 회전 동일 · 스킨 변형 대칭
  (8정점 0 비대칭) · XY/XZ 평면 · 토큰 없음 중단과 해제 · **세트 생성/재사용(두 번 돌려도 `_set1` 이 안 생긴다)**
  · UI 스모크(탭 5개, 기본값, 실제 실행, 에러 로그에 이름이 남고 멤버가 선택되는지)
  · **Reflect 는 사용자 예시 그대로**(로컬 축 -X,+Y,-Z → 미러 후 로컬 이동이 월드 +X,+Y,-Z)
  · **노드망**(POCI→ffm→multMatrix→decomposeMatrix) 재구성 후 좌우 대칭·원본 무영향 확인.

> [!summary] `A00290_BSTool` **Target Order 탭 신규** — blendShape 타겟 순서를 리스트에서 바꿔 노드에 적용 (v01.19 -> 01.20)
- **요청**: 임의의 blendShape 노드를 고르면 타겟이 TSL 에 나열되고, 리스트에서 순서를 바꾸면
  **그 노드의 타겟 순서도 실제로 바뀌게** 할 것. 새 탭으로 만들 것.
- **★ 마야에는 이 명령이 없다.** `blendShape` 커맨드에 재정렬 플래그가 없고, Shape Editor 의
  드래그는 **그룹(디렉터리) 안 표시 순서**만 옮긴다. 채널박스 · `aliasAttr` ·
  `blendShape -q -target` 이 보여 주는 **진짜 순서인 weight 인덱스**는 한 번 만들어지면 굳는다.
  Maya 2024 의 MEL 스크립트를 다 뒤져도 재정렬 프로시저가 없다 — 그래서 인덱스를 직접 갈아 끼운다.
- **★ 타겟 하나는 한 군데 있지 않다.** 인덱스 `i` 를 키로 여러 어트리뷰트에 흩어져 있어서,
  하나라도 빠뜨리면 **이름과 모양이 어긋난다**(별칭만 옮기면 `A` 라는 이름이 `B` 의 델타를
  가리키게 된다). 별칭 · weight 값/연결/lock · `inputTargetGroup[i]`(델타 · 인비트윈 ·
  `targetWeights` · `normalizationId` · `postDeformersMode` · 타겟 행렬) · `parentDirectory[i]` ·
  `targetVisibility[i]` · `targetParentVisibility[i]` · `nextTarget[i]` ·
  `inbetweenInfoGroup[i]` · `targetDirectory[d].childIndices` 를 전부 함께 옮긴다.
- **★ `inputTarget` 는 베이스 지오메트리마다 하나다.** 한 blendShape 가 메시 여러 개를 디폼하면
  같은 타겟의 델타가 `inputTarget[0]`, `inputTarget[1]` … 에 따로 있다. `inputTarget[0]` 만
  옮기면 **두 번째 메시부터** 이름과 모양이 어긋난다.
- **★ `removeMultiInstance` 는 `inputTargetGroup[i]` 를 통째로 지우면 undo 로 안 돌아온다.**
  지운 뒤 Ctrl+Z 를 해도 `inputPointsTarget` 이 빈 채로 남는다 = **델타가 영영 사라진다**(실측).
  잎 요소(`inputTargetItem[6000]`, `targetWeights[4]`)는 정상 복원된다. 그래서 그룹을 비우는
  대신 **슬롯 위에 덮어쓰고 남는 잎만** 지우도록 다시 짰다 — 그러고 나서 Ctrl+Z 한 번으로
  순서와 델타가 완전히 돌아온다.
- **★ "값이 없으면 건너뛰기" 가 조용한 버그를 만들었다.** 덮어쓰기 방식이라, 새 주인이 안 쓰는
  배열을 건너뛰면 **전 주인의 델타가 그 슬롯에 그대로 남는다.** 빈 인비트윈 아이템이 있는 씬에서
  실제로 났다(`tgt_A` 가 `tgt_C` 의 인비트윈을 물고 갔다) — 없으면 **빈 배열로 지운다.**
- **★ `setAttr` 은 타입마다 인자 모양이 다르다.** `pointArray` 는 `(x,y,z,w)` **튜플 그대로**
  (풀어서 넘기면 `Error reading data element`), **`Int32Array` 는 개수를 붙이면 안 된다** —
  붙이면 개수를 첫 값으로 읽고 나머지를 버린다. 값이 하나뿐이면 **에러 없이 개수가 값으로
  저장**되는 조용한 오작동이다(`childIndices` 를 쓰다 걸렸다).
- **인덱스 슬롯은 새로 만들지 않는다.** 타겟을 지웠던 노드는 인덱스가 듬성하다(`0,1,4,7`).
  있던 슬롯을 그대로 두고 그 안에서만 자리를 바꾼다 — `0..n-1` 로 다시 매기면 이름 대신
  번호로 `weight[4]` 를 참조하던 바깥 노드/스크립트가 조용히 다른 타겟을 가리키게 된다.
- **Edit(sculpt) 중이면 거절한다.** 확정되지 않은 편집이 떠 있어, 그대로 인덱스를 갈면
  편집분이 **엉뚱한 타겟에** 확정된다. 어느 타겟을 끄면 되는지 이름으로 알린다.
- **Shape Editor 그룹도 따라온다.** `targetDirectory[d].childIndices` 를 새 번호로 옮기고
  오름차순으로 다시 세운다(음수 = 하위 그룹 참조는 자리를 지킨다). 안 그러면 Shape Editor 만
  옛 순서로 남는다.
- 리스트는 공용 TSL 이되 **Select / Add / Del 은 감췄다** — 타겟은 씬 오브젝트가 아니라 별칭이라
  씬 선택으로 담을 것이 없고, 항목을 지운 부분 목록은 어차피 "전체 순열이 아니다" 로 거절된다.
  남는 `Up`/`Down`/`Sort`/`Reverse` 가 편집 수단이다.
- **공용 TSL 에 `attach_uuids` 옵션 추가** — 항목이 씬 노드가 아닌 것이 확실한 리스트는 항목마다
  나가던 `cmds.ls` 조회를 끈다(MetaHuman 처럼 타겟 수백 개면 그대로 비용). 이름이 우연히 씬
  노드와 겹치는 항목을 눌렀을 때 엉뚱한 노드가 선택되는 일도 없어진다.
- headless(mayapy 2024) 검증 — 재정렬 보존 **59 검사**(구운 델타 · 라이브 메시 · 인비트윈 ·
  페인트 웨이트 · lock · 연결 · 그룹 · 베이스 2개) · 듬성 인덱스/undo/sculpt 거절 **11 검사** ·
  웨이트 조합 5종으로 **변형 결과 동일 6 검사**(최대 편차 `1e-6`) · UI 스모크 **16 검사**.

> [!summary] `A00275_skinTool_V01` Expand Bind — **Even distribution** 체크박스 하나로 "간격·폭이 제각각이어도 같은 분배" + "조인트 버텍스 웨이트 1" (v01.15 -> 01.16)
- **요청 1**: xy 평면 격자 플랜 M 에서, +x 로 갈수록 +y 방향 길이가 길어질 때
  (`e_01` 짧고 `e_03` 김) **`vtx_01_a→c` 의 웨이트 분배와 `vtx_03_a→c` 의 분배가 같아야 한다.**
  지금은 `Soft Select` / `Across width` 수치에 따라 서로 다르게 분배된다. 조인트 간격이
  비균일해도, 루프가 열려 있든 닫혀 있든 적용될 것. 분배 값은 **Falloff curve 값 그대로**
  (= 커브 가로축 왼쪽이 `vtx_*_a`, 오른쪽이 `vtx_*_c`).
- **요청 2**: 조인트가 앉은 버텍스 `vtx_01_a` / `vtx_02_a` / `vtx_03_a` 의 웨이트가 각각 **1** 이어야
  한다. 지금은 `jnt_01` 이 `vtx_02_a`, `vtx_03_a` 까지 영향을 준다. **체크박스 하나로 둘 다 되면
  그렇게 할 것.**
- **★ 원인은 반경이 '거리' 라는 것 하나였다.** `Soft Select` 도 `Across width` 도 **씬 단위 절대
  거리**라, 같은 커브를 써도 좁은 자리는 커브의 앞부분만 쓰고 넓은 자리는 커브 전체를 쓴다.
  조인트 간격이 비균일하면 같은 이유로 옆 조인트가 남의 자리까지 밀고 들어온다. 두 요청은
  **다른 증상이 아니라 같은 원인**이었고, 그래서 체크박스 하나로 묶였다.
- **고친 방식은 거리 대신 '자리(파라미터)'** — 루프를 **따라서는** 이웃한 두 조인트 사이 구간
  전체가 커브의 0~1 이고, 루프에서 **멀어질 때는** 그 자리의 밴드 폭이 커브의 0~1 이다.
  두 방향이 독립이라 간격과 폭이 서로를 흔들지 않는다.
- **실측 (조인트 간격 1.0/3.0, 열 폭 1.0/1.5/3.0, Linear 커브)** — `a → b → c`:

  | | `vtx_*_a` | `vtx_*_b` | `vtx_*_c` |
  |---|---|---|---|
  | off — 폭 1.0 열 | 0.600 | 0.500 | 0.400 |
  | off — 폭 3.0 열 | 1.000 | 0.500 | 0.000 |
  | **on** — 폭 1.0 열 | **1.000** | **0.500** | **0.000** |
  | **on** — 폭 3.0 열 | **1.000** | **0.500** | **0.000** |

  끈 상태에서 `jnt_01` 은 `vtx_02_a` 까지 **0.400** 을 가져갔다. 켜면 커브 값 그대로다.
- **★ 웨이트 1 은 커브에 맡기면 안 됐다.** 정규화만으로 1 이 나오려면 커브의 끝값이 0 이어야
  하는데 `Solid` 프리셋은 끝값이 **1** 이다. 그래서 조인트가 앉은 버텍스는 **커브와 무관하게
  못박는다.** 두 조인트가 같은 버텍스로 스냅했으면 누구 것인지 정할 수 없으므로 손대지 않는다.
- **★ 밴드 폭을 재려면 반경으로 자르면 안 된다.** 폭을 모르면 정규화를 못 하므로, 이 모드의
  바깥 방향 탐색만 **반경 없이** 밴드 끝까지 가고 anchor 별 최대 거리로 나눈다.
- **조인트 사이 분배는 합이 1 이 되도록 미리 정규화**했다. 안 그러면 좌우 비대칭 커브
  (`Ease In`/`Ease Out`/`Spike`)에서 `coverage = min(1, 합)` 이 1 밑으로 떨어져 **조인트 사이가
  덜 덮인다.**
- **`Soft Select` · `Across width` · `Fit to Joints` 는 켜는 순간 회색으로 꺼진다.** 계산에서
  실제로 빠지기 때문이다 — 반경 다섯 조합(`0.0001` ~ `1000`)으로 돌려 결과 웨이트가 **완전히
  동일**한 것을 실측하고 나서 껐다. 로그에도 반경을 적지 않는다(적으면 반영된 것처럼 읽힌다).
- 루프 없이 켜면 **조용히 무시하지 않고 거절한다** — '따라/바깥' 두 방향을 가를 기준이 없다.
- headless(mayapy) **43항목** 검증: 요청 1·2, 예전 동작을 고정한 대조군, 닫힌 루프의 감아 도는
  구간, 반경 무영향, 조인트를 표면에서 2.0 띄운 seed 스냅, 행 합 1.0, 방어.

> [!summary] `A00400_CurveTool` **Edit > Joints 탭 신규** — 커브 위에 조인트를 균일하게 놓고, 그 조인트로 커브를 움직인다 (v01.06 -> 01.07)
- 리스트업한 커브마다 ① 조인트를 **균일 배치** → ② 그 조인트로 **커브를 바인드**(skinCluster) →
  ③ 조인트마다 **`_zro` / `_con` / `_ctl` / `_tgt` 컨트롤러 스택**을 세우고 마지막 노드로
  조인트를 컨스트레인트한다. **컨트롤러 → 조인트 → 커브** 로 이어진다. 커브를 리깅에 쓰려면
  누군가 끌어 줘야 하는데 그 셋업이 배치 · 바인드 · 컨트롤러 세 단계로 흩어져 있었다.
- 스택 구성 · 옵션 · 툴팁은 **`A00460_ControllerTool` 의 FK 탭과 같은 모양**으로 맞췄다 —
  두 툴을 오가도 같은 자리에서 같은 이름을 찾게.
- **★ "균일하게" 는 호 길이 균등이 기본이다.** 파라미터 균등(`minValue~maxValue` 등분)과 다르고,
  스팬 길이가 제각각인 커브(엣지에서 뜬 커브가 대표적)에서는 **짧은 스팬에 조인트가 몰린다.**
  CV `(0,0,0)(1,0,0)(11,0,0)` 에 3개면 호 길이는 `0 / 5.5 / 11`, 파라미터는 `0 / 1 / 11`.
  `Spacing: By length / By parameter` 로 고른다.
- **★ 닫힌 커브는 `u=0` 과 `u=1` 이 같은 점**이라 그대로 등분하면 마지막 조인트가 첫 조인트 위에
  겹친다. 주기 커브면 마지막 자리를 빼고 `count` 등분한다(`4` → `0, 0.25, 0.5, 0.75`).
  엣지 루프에서 뜬 커브가 대부분 여기 해당한다.
- **커브에도 skinCluster 가 걸린다** — 메시 전용이 아니고, `polyToCurve` 로 뜬 **히스토리가 살아
  있는 커브**에도 걸려 조인트가 CV 를 끈다(디포머가 히스토리 뒤에 낀다).
- **★ 바인드는 조인트를 그룹에 넣은 뒤에** 해야 한다. `bindPreMatrix` 가 바인드 시점 행렬을
  잡으므로 순서가 뒤집히면 리페어런트만으로 커브가 튄다.
- **★ 리페어런트가 롱네임을 죽인다** — 조인트를 그룹에 넣는 순간 `|spine_1_jnt` 는 없는 경로가
  되어 `cmds.xform` 이 `No object matches name` 을 낸다. 결과에는 **옮긴 뒤 경로**를 담고,
  컨트롤러 스택은 옮기기 전에 **UUID** 를 잡아 뒀다가 다시 해석한다.
- **`cmds.joint` 는 현재 선택의 자식으로 붙는다** — 매번 `select(clear=True)` 하지 않으면
  조인트끼리 체인이 되어 버린다. 커브 구동 조인트는 각자 독립이어야 한다.
- 조인트 방향은 `rotate` 말고 **`jointOrient`** 에 쓴다(로컬 = `R * JO`, 갓 만든 조인트는 `R=0`
  이라 JO 가 곧 월드 방향). `rotate` 에 넣으면 애니메이터가 채널을 0 으로 돌릴 때 풀린다.
  `Aim joints along the curve`(기본 켬)는 X 축을 접선으로, up 힌트는 월드 Y — 접선이 Y 와
  나란하면 월드 Z 로 갈아탄다.
- **다른 툴의 core 를 import 하지 않았다** — `dev/build_release.py` 가 **툴 하나 + Framework** 만
  복사하므로 `A00460` 의 `fk_manager` 를 참조했다면 릴리스에서 곧바로 깨진다. 툴 사이 공유가
  필요해지면 그때 `Framework` 로 올릴 자리다.
- 커브가 아닌 항목 · 씬에 없는 이름 · **이미 skinCluster 가 걸린 커브**는 사유와 함께 건너뛰고
  로그에 남긴다(중단하지 않는다). 전체가 **undo 한 스텝**.
- 검증(mayapy 2024) — `uniform_us` 경계(1/2/3/닫힘) · 호 길이 균등 실측 · 열린·닫힌 커브 배치 ·
  `skinCluster` 웨이트 분포와 컨트롤 → 조인트 → CV 전달 · 재바인드 차단 · 커브 아님·없는 노드
  방어 · 옵션 전부 끈 조합 · UI 빌드 후 탭에서 실행 + **undo 1스텝** 복원.

> [!summary] `A00275_skinTool_V01` **Copy Weights 탭 신규** — 같은 메시 안에서 버텍스 → 버텍스로 웨이트를 그대로 복사 (v01.16 -> 01.17)
- **요청**: 같은 메시 M 에서 임의의 버텍스 집합을 저장하되 **TSL 에 담지 말고 개수만** 보이면
  된다. 저장 후 M 의 다른 버텍스를 고른 상태에서 copy & paste 를 누르면 저장한 버텍스로부터
  선택한 버텍스로 **웨이트를 그대로** 복사. 복사 방법은 Expand Bind 의 Falloff mode 처럼
  **Surface / Topology / Volume** 중에서 고를 수 있을 것.
- `Weights` 카테고리에 **Copy Weights** 하위 탭을 새로 붙였다. `Copy` 는 아무것도 쓰지 않고
  버텍스만 기억하고(`Copied: 1234 vertices (head_geo)` 라벨 + Select / Clear), `PASTE` 가
  현재 선택한 버텍스에 적용한다.
- **"그대로" 의 정의를 먼저 못박았다.** 목표 버텍스마다 가장 가까운 소스 버텍스 **하나**를 골라
  그 버텍스의 **웨이트 행 전체**를 통째로 베낀다. 섞거나 보간하지 않고 `normalize=False` 로
  쓴다 — 여기서 다시 정규화하면 그것은 이미 "그대로" 가 아니다. 인플루언스가 몇 개든, 행의
  합이 1 이 아니든 소스와 완전히 같은 값이 나온다.
- **인플루언스를 새로 넣지 않는다.** 소스와 목표가 같은 skinCluster 라 열 구성이 이미 같기
  때문이고, 그래서 이 기능은 한 메시 안에서만 동작한다. 다른 메시를 고르면 어디서 복사했는지
  적어서 거절한다(메시 사이 전이는 `Transfer` / `Migrate` 쪽이다).
- **세 모드가 실제로 다른 답을 낸다** — 열 간격이 넓고 세로 간격이 좁은 격자에서 같은 목표를
  두고 Surface·Volume 은 가까운 쪽을, **Topology 는 홉 수가 적은 먼 쪽**을 고르는 것을 실측으로
  확인했다. 셋 다 "가깝다" 이지만 재는 자가 다르다.
- **★ 탐색 범위를 Expand Bind 에서 그대로 베끼면 아무 데도 못 간다.** 그쪽은 falloff 가 영역
  밖으로 새면 안 되니까 인접을 **저장한 집합 안으로** 가둔다. 여기서는 소스와 목표가 **떨어져
  있는 것이 정상**이라 같은 걸 하면 이웃이 끊긴다. 그래서 인접은 메시 전체로 만든다.
- **Surface / Topology 는 메시를 걸어가므로 떨어진 조각에는 못 닿는다.** 그런 버텍스는 손대지
  않고 개수를 로그에 남기고, 하나도 못 닿으면 **아무것도 쓰지 않은 채** `Volume` 을 쓰라고
  알린다 — 조용히 다른 모드로 넘어가면 사용자는 자기가 고른 모드의 결과라고 읽는다.
- **★ volume 은 전수 비교를 하면 안 된다.** 목표마다 소스를 전부 재면 `목표 × 소스` 라,
  22,500 정점 메시에서 소스 5,000 / 목표 15,000 이면 순수 파이썬으로 **약 20초**다. 소스를
  균일 격자에 담고 목표 주변 셀을 **한 겹씩** 넓혀 보되, "다음 겹의 가장 가까운 지점보다 이미
  찾은 것이 더 가깝다" 가 되면 멈춘다. **근사가 아니라 전수 비교와 같은 답**이고(소스
  3/70/400/1599 네 경우 · 목표 200개에서 거리 차 `0.0e+00`, 목표가 소스 bbox 바깥인 경우 포함)
  **1.00초** 로 20배 빠르다. 소스가 64개 미만이면 격자 만드는 비용이 더 커서 그냥 전수 비교한다.
- Expand Bind 의 `_dijkstra_multi` 를 **공개(`dijkstra_multi`)** 로 올려 재사용했다 — "여러
  시작점에서 퍼뜨려 버텍스마다 anchor 를 얻는다" 는 같은 계산이라 두 번 구현할 이유가 없다.
  Expand Bind 쪽 동작이 바뀌지 않은 것을 43항목 회귀로 확인했다.
- headless(mayapy 2024) **30항목** 검증 — 값이 소스와 완전히 같음(정규화 안 된 행·6 인플루언스
  포함), 소스 자신에게 붙여넣으면 no-op, 세 모드 분기, 떨어진 조각의 거절과 Volume 성공,
  격자 vs 전수 동일, 성능(surface end-to-end 22,500 정점 **0.14초**), 방어 5종.

> [!summary] `A00460_ControllerTool` **FK 탭 → FK & IK** — 자식 스택을 `_ctl` 밑으로(`_tgt` 는 잎) + 모든 `_zro` 를 씬 최상위에 두는 IK 계층 (v01.03 -> 01.04)
- **요청 1**: FK 계층을 만들 때 `_tgt` 하위로 자식 `_zro` 가 생긴다. 그러지 말고 **`_ctl` 하위에**
  자식 `_zro` 가 생기게 하고, **`_tgt` 에는 어떤 자식도 없게** 할 것.
- **요청 2**: 지금은 Bone Root 든 Bone Chain 이든 FK 로만 계층이 만들어진다. **IK 모드**를 만들어
  리스트업한 오브젝트에 자식 계층이 있더라도 **`_zro` 가 모두 씬 최상위에 생성**되게 할 것.
- **요청 1 은 역할을 나누는 것이 전부였다.** `_tgt` 가 "조인트를 끄는 드라이버" 와 "다음 뼈의
  부모" 두 역할을 겸하고 있었다. 이제 `_build_one` 이 컨스트레인트는 `last`(=`_tgt`)로 걸고
  **`ctl` 을 돌려준다.** `_ctl` 밑에 `_tgt`(잎)와 자식 `_zro` 가 나란히 선다. 월드 결과는
  예전과 같다 — `_tgt` 도 `_ctl` 에 로컬 0 으로 붙어 있었기 때문이다. 달라진 것은 **`_tgt` 를
  이제 따로 옮기거나 지울 수 있다**는 것이고, `tgt` 옵션을 꺼도 자식이 붙는 자리는 `_ctl` 로 같다.
- **★ 요청 2 는 Mode 와 다른 축이라 옵션을 따로 두었다.** `Mode`(Bone Root / Bone Chain)는
  **누구에게** 만들까이고, 새로 넣은 `Hierarchy`(FK / IK)는 **만든 것끼리 어떻게 이을까**다.
  한 콤보에 IK 를 세 번째 항목으로 넣으면 "IK + Bone Chain" 같은 조합을 표현할 수 없다.
  그룹박스를 나누고 제목에 차이를 적었다(`Mode - which nodes get a control` /
  `Hierarchy - how the stacks are linked`). **네 조합이 모두 성립한다.**
- **★ 자손을 "따라가는 것" 과 스택을 "잇는 것" 은 별개다.** Bone Root + IK 는 자손까지 그대로
  돌며 컨트롤러를 만들되 부모를 넘기지 않는다. 재귀에서 이 둘을 한 덩이로 보면 "IK 면 자손을
  안 판다" 로 잘못 만들게 된다 — `_build_root_recursive` 는 재귀는 그대로 하고 자식에게 넘길
  부모만 `None` 으로 바꾼다. 분기(자식 여럿)도 갈래마다 스택이 생기고 전부 최상위에 선다.
- IK 도 **스택 최상단은 조인트 자리에 `matchTransform`** 한다 — 부모가 없을 뿐이다. 조인트는
  여전히 자기 `_tgt` 를 따라가므로 **컨트롤러 하나를 옮기면 그 조인트만** 움직인다.
  FK 로 같은 씬을 돌려 자식 조인트가 따라오는 것과 대조해 실측했다.
- **★ 테스트를 쓰다 기존 버그를 하나 물었다** — Bone Root 에서 **루트와 그 자손을 리스트에
  함께 담으면 자손 스택이 두 번** 만들어졌다. 중복 판정 `seen` 이 **입력 문자열 그대로**를
  담고 있어서, 재귀가 준 풀패스(`|a|b`)와 사용자가 넣은 짧은 이름(`b`)을 다른 노드로 봤다.
  **에러 없이** `b_zro1` 이 조용히 하나 더 생긴다. `cmds.ls(node, long=True)` 로 정규화해
  비교하도록 고쳤고 회귀로 고정했다.
- 로그도 계층 방식을 말한다(`IK built (Bone Root mode): ... 4 stack(s) at the scene top`).
  IK 는 스택마다 최상단이 하나씩이라 "root hierarchy" 라고 부르면 오해를 준다.
- headless(mayapy 2024) **45항목** 검증 — `_tgt` 가 잎인지 · 자식 부모가 `_ctl` 인지 ·
  `tgt` 를 껐을 때 · IK 가 분기 포함 전부 최상위인지 · IK/FK 의 전파 차이 · 네 조합 ·
  기본값과 알 수 없는 값 폴백 · 중복 생성 회귀 · 스택이 조인트 자리에 정확히 서는지.

---

## 2026-09-04

> [!summary] `docs` **지원서 문항 답변 문서 신규** — "직무를 수행하며 AI 를 활용해 성과를 낸 경험" (3D 애니메이터)
- `docs/portfolio/application_AI_experience_KR.md`(신규, 499줄). 근거는 `portfolio_KR.md` · 툴별 가이드 ·
  커밋 기록(2026-05-06 ~ 2026-09-04).
- 구성: **제출용 짧은 답변(약 1,000자)** → 애니메이션(`A00410` 2차 모션 굽기 · Stagger Offset · 구간 오일러 필터 등) →
  리깅(Update Bind Pose · IK Edit · 스킨 웨이트 역산 · 페이셜 결선 자동화) → 언리얼 세팅(노드 텍스트 변환기 ·
  splineIK 런타임 물리 · 플러그인 패치) → 전공과의 접점 · AI 활용 방식 · 수치 요약.
    #docs #portfolio

> [!summary] `A00100_jsonEditor_MH` **작업용 소스 `wrk_0010.json` 추가** (데이터만, 코드 변경 없음)
- `app/core/0010_src_wrk/wrk_0010.json` — Pose Wrangler 솔버 번들(`solvers` 최상위 키, `WRK_calf_l_UERBFSolver` …)
  형식의 작업용 입력. 같은 날 `A00090` 이 읽게 된 번들 export 와 같은 포맷이다.
    #A00100 #data

> [!summary] `A00090_ConnectionBuilder` **Pose Wrangler export 를 규칙으로 그대로** + 모든 버튼 undo 1스텝 (v01.06 -> 01.07)
- **요청 1**: `app/rules/v003/rules_v003.json` 은 마야 **Pose Wrangler 에서 솔버 세팅을 그대로
  export 한 파일**이다. 지금은 포즈를 고칠 때마다 `WRK_calf_l.json`, `WRK_calf_r.json` … 을
  **솔버 수만큼 손으로 다시 써야** 한다. 이 export 파일을 규칙으로 바로 읽어 v002 와 똑같이
  동작하게 할 것. 그리고 앞으로 v004, v005 에도 파일을 하나씩 둘 계획이니 **파일 이름 규칙을
  정해 달라**.
- **파일 이름은 `rules_<폴더이름>.json` 으로 정했다**(`v004/rules_v004.json`). 파일만 떼어 놔도
  어느 버전에서 나온 것인지 읽힌다. **다만 코드는 이 이름에 기대지 않는다** — 최상위에 `solvers`
  키가 있으면 번들로 읽으므로 Pose Wrangler 가 지어 준 이름 그대로 떨어뜨려도 되고, 한 폴더에
  두 방식(솔버당 파일 / 번들)을 **섞어 둬도 된다.** 이름 규칙은 나중에 폴더를 열어 본 사람을 위한
  것이지 동작 조건이 아니다.
- **★ 그대로 쓸 수 없는 이름이 딱 하나 있었다.** Pose Wrangler 는 중립 포즈를 **언제나 그냥
  `default`** 로 부른다. 그대로 mapping 에 넣으면 솔버 8개가 전부 `WRK_intermediate.default`
  라는 **같은 어트리뷰트 하나로 몰려 서로를 덮어쓴다.** 손글씨 규칙은 이 자리를
  `calf_l_default` 로 적고 있었고, 번들의 `drivers[0]` 이 정확히 `calf_l` 이라
  **`<driver>_default`** 로 되살렸다. 나머지 포즈는 사용자가 이미 드라이버 이름을 붙여 짓기
  때문에 손대지 않는다.
- **동치를 눈으로 확인하고 나서 붙였다** — v003 번들의 솔버 8개를 v002 손글씨 mapping 과 한 줄씩
  대조해 **mapping · solver_node 전부 일치**. 포즈 순서(=`outputs[i]` 순서)도 json 이 순서를
  보존하므로 그대로 맞는다.
- **규칙 이름은 솔버 이름에서 `_UERBFSolver` 를 뗀 것**으로 했다(`WRK_calf_l`). v002 의 파일
  이름과 같아서 **버전을 바꿔도 `Rule` 콤보 목록이 그대로다.**
- **파일을 고치면 `Refresh` 없이 반영된다** — 색인이 폴더 안 json 의 (이름 · 수정 시각 · 크기)를
  기억해 두고 달라지면 다시 읽는다. Pose Wrangler 에서 다시 export 해 덮어써도 그만이다.
- **요청 2**: `Connect Intermediate` 로 노드를 만든 뒤 `Ctrl+Z` 를 누르면 노드가 생기기 전으로
  돌아가지 않고 **어트리뷰트가 하나씩 끊어지다가 마지막에야 노드가 사라진다.** `undo_chunk()` 로
  안 묶인 곳을 묶을 것.
- **씬을 바꾸는 버튼 6개를 묶었다** — `Connect` / `Connect All` / `Disconnect` / `Set Attr` /
  `Del Attr` / `Connect Intermediate`. `Create` 계열은 v01.04 때 이미 묶여 있었고, `Validate` 는
  읽기만 해서 뺐다.
- **검증**(mayapy 2024 headless, Qt 창 실제 빌드): 49항목 통과 — 로더 30(두 포맷 동치 · 규칙 이름 ·
  `default` 이름 충돌 · 섞인 폴더 · 깨진 json 무시 · mtime 재읽기) + UI 19(`Connect Intermediate`
  뒤 **undo 한 번**으로 `WRK_All`/`WRK_intermediate` 까지 사라지는 것, Set/Del Attr · Connect/
  Disconnect 각각 한 번, 46개 attr 이름이 겹치지 않는 것).
- 파일: `app/core/rule_loader.py`, `app/ui/main_window.py`, `app/config/version.py`,
  [`docs/A00090_ConnectionBuilder.md`](A00090_ConnectionBuilder.md)(§1-2 · §4-2)
    #A00090 #ConnectionBuilder #poseWrangler #undo

---

## 2026-09-03

> [!summary] `A00145_RigConnect` **Connect > Pair — 오브젝트를 이름으로 짝짓기** (v01.36 -> 01.37)
- **요청**: Connect > Connect 하위 탭의 어트리뷰트 이름 매칭을 **오브젝트에도** 달라. Driver /
  Driven TSL 이 주어졌을 때 이름이 비슷하거나 같은 것끼리 짝짓고, 안 되면 `(Null)`.
  덧붙여 — 그 탭을 통째로 `A00310_SearchTool` 로 옮기는 게 낫지 않겠나(옮긴다면 constraint 는
  빼도 된다), 더 나은 방법이 있으면 제안하고 구현할 것.
- **옮기지 않기로 하고 A00145 에 두었다**(사용자 확인). 근거는 **정렬된 짝은 순서가 곧 의미**인데,
  툴 사이로 짝을 넘길 수단이 씬 선택뿐이라 **넘기는 순간 그 순서가 사라진다**는 것이다.
  `(Null)` 로 자리를 지켜 놓아도 다른 툴에서는 되살릴 방법이 없다. 짝을 세우는 자리는 그 짝을
  **소비하는 자리**(= 연결) 옆이어야 한다.
- **점수 계산을 새로 만들지 않았다** — `attr_match` 의 토큰 역색인 + IDF 엔진을 그대로 쓴다.
  이 모듈은 애초에 **이름 리스트만 받는 순수 파이썬**이라 어트리뷰트든 오브젝트든 상관이 없었다.
  새로 필요한 것은 **오브젝트 이름을 비교 가능하게 만드는 일**뿐이었다(`object_match.py`).
- **★ 경로/네임스페이스가 진짜 문제였다.** `|grp|rig:jnt_L_arm` 을 통째로 토큰화하면 `grp` ·
  `rig` 가 토큰으로 섞여, **한쪽 리스트에만 경로가 붙어 있으면 같은 오브젝트인데 문턱을 못 넘는다.**
  그래서 비교는 **말단 이름**으로 하고 네임스페이스는 옵션(`Ignore Namespace`, 기본 ON)으로 두되,
  **돌려주는 것은 언제나 원래(전체) 이름**이다 — 말단 이름을 돌려주면 동명 노드가 있는 씬에서
  엉뚱한 노드를 잡는다. 비교용 이름과 실제 이름을 갈라 두고 인덱스로 되짚는다.
- **★ 짝을 세워 놔도 Connect 가 거리로 다시 계산하고 있었다.** 기존 `connect_closest` 는 리스트
  순서를 아예 보지 않는다(Get Closest 로 채워 넣어도 연결 때 다시 최근접 매칭). 그대로 두면
  이름으로 세운 짝이 **연결 순간 조용히 뒤집힌다.** 그래서 짝짓는 방법을 `Pairing` 라디오
  (`Closest distance` / `List order`)로 꺼내고, Match by Name 이 자동으로 `List order` 로 돌린다.
  - `List order` 는 **거르기 전에 짝을 만든다** — 씬에 없는 항목을 먼저 빼면 그 자리가 사라져
    뒤의 짝이 한 칸씩 밀린다.
- 하위 탭 이름을 **`Connect Closest` -> `Pair`** 로 바꿨다(이제 거리만이 아니라 이름으로도 짝을
  세운다). Get Closest 와 Match by Name 이 **후보 풀 규칙을 공유**하도록 정리했다.
- **검증**(mayapy 2024 headless, Qt 창 실제 빌드): 25항목 전부 통과 —
  driver 순서 유지 · `(Null)` · 전체 경로 반환 · **동명 말단 이름 두 개가 서로 다른 경로로** ·
  exact / unique / namespace 옵션 · 빈 리스트 · 컴포넌트 이름 보존 · `(Null)` 과 없는 노드가 낀
  자리 건너뛰기 · **같은 리스트를 두 Pairing 으로 연결하면 서로 다른 짝**(거리는 엇갈리고
  자리는 그대로) · UI 에서 Match by Name -> Connect 까지.
- 파일: `app/core/object_match.py`(신규), `app/core/closest_connector.py`(짝짓기 모드),
  `app/ui/main_window.py`, `app/config/version.py`,
  [`docs/A00145_RigConnect.md`](A00145_RigConnect.md)(§Pair)
    #A00145 #RigConnect #nameMatching

> [!summary] `A00145_RigConnect` **Constrain > Update — AE 의 Update 버튼을 리스트 전체에** (v01.35 -> 01.36)
- **요청**: Attribute Editor 에서 parentConstraint 를 열면 **Update** 버튼이 있다. constraint 가
  걸린 오브젝트를 옮긴 뒤 그 버튼을 누르면 offset 이 다시 계산되어 옮긴 자리 그대로
  물린다(`parentConstraint -e -maintainOffset curve2  curve1_parentConstraint1;`).
  그걸 **TSL 에 담은 constraint 여러 개에 한번에** 돌리고 싶다. parent 뿐 아니라
  point · scale 도 같이.
- **계산을 다시 구현하지 않고 Maya 명령을 그대로 불렀다** —
  `cmds.<type>Constraint(*targets, cn, e=True, mo=True)`. AE 버튼과 결과가 어긋날 이유가
  없어야 하기 때문이다. 대신 **명령에 넘길 타깃 목록**이 까다로워서 mayapy(2024) 로
  세 가지를 먼저 확인했다.
  - **타깃을 전부 넘겨야 한다.** 2개 중 하나만 넘기면 **넘긴 슬롯의 offset 만** 다시
    구워지고 나머지는 옛 값 그대로 남는다 → weight 가 섞이는 순간 driven 이 튀다.
  - **타깃이 아닌 오브젝트를 넘기면 `-e` 인데도 타깃으로 추가된다.** 그래서 이름을 새로
    만들지 않고 **지금 연결된 target 슬롯에서 그대로 읽어** 넘긴다.
  - `-q -targetList` 는 **짧은 이름**이라 동명 노드에서 어긋난다 → Target Edit 과 같은
    `_target_entries()`(입력 연결 역추적, 롱네임)를 쓴다.
- **타입별로 되는 것과 안 되는 것이 갈린다** — parent / point / orient / scale / aim /
  pointOnPoly 는 `-e -mo` 를 받고, `geometry` / `normal` / `tangent` / `poleVector` 는 애초에
  플래그가 없어 **`Invalid flag 'mo'`** 로 거절한다 → 건너뛰고 경고.
- **로그가 `updated` 와 `no change` 를 가른다.** 아무도 안 움직인 constraint 에 돌리면
  offset 값이 그대로인 무해한 no-op 이므로, "일단 다 담고 돌리기" 가 안전하다.
- 리스트에는 **constraint 노드도, constraint 가 걸린 오브젝트도** 담을 수 있다(오브젝트는
  그 아래 constraint 로 확장). 고른 항목만 대상으로 하는 규칙도 Target Edit 과 같다.
- **검증**(mayapy 2024 headless): parent(타깃 2개 + weight 0.3 혼합) · point · orient ·
  scale · aim(aim/up 설정 보존 확인) · pointOnPoly 전부 **driven 월드 행렬 오차 1e-16** ·
  네임스페이스 · **동명 타깃(긴 이름)** · 조인트 driven · 지원 안 하는 타입 경고 ·
  같은 constraint 를 두 번 담았을 때 1회만 처리 · 빈 리스트 방어. **Qt 창을 실제로 빌드해**
  하위 탭 6개와 로그 출력까지 확인했다.
- 파일: `app/core/constraint_update_manager.py`(신규), `app/ui/main_window.py`(Constrain 하위 탭
  `Update` + 핸들러), `app/config/version.py`, [`docs/A00145_RigConnect.md`](A00145_RigConnect.md)(§Update)
    #A00145 #RigConnect #constraint

> [!summary] `docs` **WORKLOG 8월 롤링** — 루트는 9월부터
- 월이 바뀌었으므로 8월 항목 **18일치 3,108줄**을 [`worklog/2026-08.md`](worklog/2026-08.md) 로
  내렸다. **본문은 순수 이동**이고, 한 단계 깊어졌으므로 **상대 링크 24건에 `../` 를
  붙였다**(이미 `../tools/...` 였던 것은 `../../tools/...`). 규칙과 절차는
  [`worklog/README.md`](worklog/README.md).
    #docs #worklog

---
