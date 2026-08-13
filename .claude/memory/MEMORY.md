# Memory Index

한 줄 = 한 메모. 자세한 내용은 각 파일에 있으니 필요할 때 열어본다.

## 작업 방식 · 사용자 선호

- [Explain in Korean](explain-in-korean.md) — 설명/대화는 한국어로 (코드·UI 문자열은 영어)
- [UI text English-only](ui-text-english-only.md) — UI 문자열·로그는 전부 영어, 한국어는 주석/독스트링만
- [Push only when asked](push-only-when-asked.md) — 그 턴에 명시 요청 없으면 절대 push 금지 (로컬 커밋은 OK)
- [Push target Dnable/dev](push-target-dnable-dev.md) — 기본 push 대상은 Dnable_repo 의 dev (origin 아님)
- [Push includes tool guide docs](push-includes-tool-guide-docs.md) — 툴 push 시 docs/<툴>.md 가이드 + CHANGELOG/version/WORKLOG 함께
- [Clean commit message](clean-commit-message-no-stray-chars.md) — 커밋 메시지에 이상문자 새지 않게(과거 `@` 유출), 커밋 후 `git log -1` 확인
- [WORKLOG maintenance](worklog-maintenance.md) — docs/WORKLOG.md 갱신 규칙(최신이 위, 날짜 헤딩 중복 금지)
- [Docs go in JUN_All/docs](docs-go-in-jun-all-docs.md) — 분석/설명 문서는 JUN_All/docs 아래
- [Update portfolio on tool work](update-portfolio-on-tool-work.md) — portfolio_EN/KR 둘 다 동기 갱신, 커밋수 통계는 건드리지 않기
- [Memory synced via repo](memory-synced-via-repo.md) — 메모리는 repo `.claude/memory`(정션), 커밋+푸시로 PC 간 공유
- [Prefer PySide for new tools](prefer-pyside-for-new-tools.md) — 신규/병합 툴은 maya.cmds UI 말고 PySide(arch B)
- [JUN_mgear vault](jun-mgear-vault.md) — mgear 학습 노트는 JUN_mgear Obsidian vault → elom1213/JUN_mgear
- [kangaroo plugin read-only](kangaroo-plugin-external-readonly.md) — kangaroo 플러그인은 외부 3rd-party, 수정 금지
- [PoseWrangler fork patch](posewrangler-plugin-fork-patch.md) — Epic PoseDriverConnect 포크 위치 + serializer objExists 패치 3단계

## 검증 · 마야 공통 함정

- [mayapy headless verify](mayapy-headless-verify.md) — maya.cmds 동작은 추측 말고 Maya2024/bin/mayapy.exe + maya.standalone 으로 확인
- [QApplication before standalone](qapplication-before-maya-standalone.md) — mayapy Qt 테스트는 `QApplication` 을 `standalone.initialize()` **앞에** (뒤면 QWidget 에서 무단 종료)
- [undo_chunk by default](undo-chunk-by-default.md) — 반복 씬 변경은 요청 없어도 `Framework.core.maya_undo.undo_chunk()` 로 묶기
- [Maya 2023 compat](maya-2023-compat.md) — 2023 지원 필요할 수 있음, sin/cos 노드 없음(eulerToQuat 우회)
- [Maya loadPlugin no __file__](maya-loadplugin-no-file.md) — loadPlugin 으로 뜬 .py 플러그인은 `__file__` 없음
- [animLayer no global selected query](animlayer-no-global-selected-query.md) — `animLayer(q,selected)` 는 레이어 인자 필요, `ls(type=animLayer)` 순회
- [name matching: token index](attr-name-matching-token-index.md) — 이름 대량 유사도 매칭은 편집 거리 말고 토큰 역색인+IDF. **difflib 비율은 coverage 와 척도가 다르다**
- [hold mesh while moving joints](skincluster-hold-mesh-while-moving-joints.md) — 스킨 행렬 `bindPreMatrix*matrix` 를 multMatrix 로 상수 유지. `worldInverseMatrix` **직결은 포즈된 리그에서 메시가 튄다**
- [constraint target plugs & offset spaces](constraint-target-plugs-and-offset-spaces.md) — `listConnections("con.target[0]")` 는 None(노드 단위로 열거), parentConstraint 의 offsetT/offsetR 은 **다른 공간**, 오일러 순서는 driven `rotateOrder`
- [blendShape delta space = origin](blendshape-delta-space-origin.md) — 델타 공간은 `origin` 이 정함(0=world→베이스 공간). 미러/회전 타겟에서 일부 축만 반대로 가는 원인
- [blendShape live target deltas](blendshape-live-target-inputpointstarget.md) — inputGeomTarget 연결 시 inputPointsTarget setAttr 은 조용히 무시, 타겟 메시를 옮겨야 함
- [setKeyframe insert needs a curve](setkeyframe-insert-needs-existing-curve.md) — `insert=True` 는 커브가 없으면 **조용히 no-op**(레이어에 채널 커브 없을 때 특히). 값 경로는 쓰기 전에 전부 미리 계산
- [animated attr: key + setAttr](animated-attr-setkeyframe-plus-setattr.md) — 키/레이어 걸린 attr 은 `setKeyframe` 만으론 값이 안 바뀜(뒤에 `setAttr` 까지), 레이어면 소스가 `animBlendNode*`
- [cmds.toggle not undoable](maya-toggle-cmd-not-undoable.md) — `toggle -localAxis` 는 undo 를 안 남겨 Ctrl+Z 가 이전 작업을 지움 → `setAttr` 사용
- [extendToShape picks wrong shape](extendtoshape-picks-wrong-shape.md) — `kInvalidParameter: Object is incompatible` 1순위 원인. 새 코드는 `extendToShape` 금지, **공용 `Framework.core.maya_shape`** 사용. `polyEvaluate`/`copySkinWeights` 도 셰이프에 걸 것
- [list_attrs multi detection](list-attrs-multi-detection.md) — multi 판정은 `attributeQuery(multi=True)`, getNextFreeMultiIndex 남용 금지
- [UUID-safe rename](uuid-safe-rename-duplicate-names.md) — 동명 노드 대비 UUID 로 노드 보관("UUID 기반 리네임 패턴 적용해줘")
- [standalone app package collision](standalone-app-package-collision.md) — standalone Qt 툴은 `tools.<tool>.app.*` 로 import, 맨 `app` 금지
- [Standalone taskbar icon](standalone-taskbar-icon-method.md) — SVG→다중크기 .ico + QApplication 전에 AppUserModelID
- [Pin for maya.cmds tools](pin-for-maya-cmds-tools.md) — cmds.window 최상단 고정은 maya_ui_widget() 로 감싸 WindowStaysOnTopHint

## 공용 위젯 · 프레임워크

- [TSL UUID selection](wip-tsl-uuid-selection.md) — MOD_tsl_qt_v01 이 (uuid, component) 보관 → 리네임/동명/다중 레퍼런스 안전
- [TSL selection order](tsl-selection-order.md) — `Order` 체크박스. `ls(sl)` 는 컴포넌트를 인덱스 순으로 줌 → `selectPref(trackSelectionOrder)`+`ls(orderedSelection)`. **함정: pref off 면 `ls(os)` 도 에러 없이 인덱스 순서**
- [Sub-tabs over collapsibles](prefer-subtabs-over-stacked-collapsibles.md) — 기능 섹션이 3~4개 넘으면 접이식 대신 **중첩 탭**. 하위 탭마다 개별 스크롤(이중 스크롤 주의), 단 **창 자동 리사이즈 툴은 스크롤 대신 fit page**
- [Framework filter widget](framework-filter-widget.md) — MOD_filter_qt_v01: 검색 있는 툴은 전부 이 공용 Filter 로 통일 중
- [Framework timeRange widget](framework-timerange-widget.md) — MOD_timeRange_qt_v01: Start/End 입력 + Get Current / Get Sel Range 공용 위젯
- [QTreeWidgetItem checkable default](qtreewidgetitem-checkable-default-flag.md) — ItemIsUserCheckable 은 기본 ON, 플래그로 체크 가능 판정 금지
- [clicked passes checked bool](qt-clicked-passes-checked-bool.md) — `clicked` 는 `checked`(bool)를 넘긴다. 기본 인자 있는 슬롯에 직접 연결하면 그 값이 옵션으로 샌다
- [QDoubleSpinBox keyboardTracking](qdoublespinbox-keyboard-tracking.md) — 값을 되쓰는 스핀박스는 `setKeyboardTracking(False)`, 안 그러면 타이핑 중 `0.1` → `0.100` 으로 잘림

## 툴 작업 (신규 · 큰 기능)

- [A00090 rule versions](wip-a00090-rule-versions.md) — 규칙 json 을 `app/rules/<version>` 폴더로 분리 + UI Version 콤보 (v01.05)
- [A00420 Wrapper](wip-a00420-wrapper.md) — **신규**: 커브 가이드로 다른 토폴로지 메시 래핑(Wrap3D 대응). TPS 워프 + 표면 투영 2단계, MMeshIntersector 는 월드 행렬을 줘도 결과가 오브젝트 공간 (v01.00)
- [A00410 SecondaryMotion](wip-a00410-secondarymotion.md) — **신규**: FK 체인 관성(KawaiiPhysics식)을 키로 굽기. nucleus 안 쓰는 이유, 전 구간 30ms 재계산→override 레이어, addKeys 74배, **joint `local=R*JO` / transform `local=RA*R`**, 부모를 앞 체인 노드로 가정하면 오프셋 그룹에서 깨짐. v01.02 Bone Chain/Root + 출력 레지스트리(`outputs.py`) 확장 지점
- [A00400 CurveTool](wip-a00400-curvetool.md) — 선택 엣지를 연결 성분별로 그룹지어 커브 1개 + Reverse Direction, **Line Width 탭**(lineWidth 슬라이더, 드래그=undo 1스텝) (v01.01)
- [A00390 WindTool](wip-a00390-windtool.md) — **신규**: 본 체인에 싸인 파형 바람. Curve/Node 출력, windSpeed 적분 표현식, windPhaseOffset (v01.08)
- [A00380 MeshTool Peak](wip-a00380-meshtool-peak.md) — **신규**: 노멀 방향 인플레이트. `shape.pnts` ranged setAttr(~70배), 슬라이더 settle 자동 커밋 (v01.05)
- [A00380 Match tab](wip-a00380-match-tab.md) — Kangaroo Geometry>Match 재현 + Peak auto-load 가 수동 편집을 되돌리던 버그 수정 (v01.03)
- [A00370 ToolLauncher](wip-a00370-toollauncher.md) — **신규**: 툴 바로가기 런처. 경로를 JUN_All 상대로 저장해 PC 간 git churn 제거 (v01.04)
- [A00360 SortTool](wip-a00360-sorttool.md) — **신규**: 월드 XYZ/이름/타입 정렬 + 아웃라이너 재정렬 (v01.00)
- [A00350 ArrayCreator](wip-a00350-arraycreator.md) — **신규**: TSL → UE Control Rig Item Array 텍스트. 공용 TSL 에 Reverse 버튼 옵션 추가
- [A00340 SelectionTool](wip-a00340-selectiontool.md) — **신규**: 저장한 오브젝트 세트 빠른 재선택 + 프로파일 (v01.00)
- [A00310 SearchTool](wip-a00310-searchtool-merge.md) — 레거시 Selection/Search 툴 2개를 탭 하나로 병합 (Maya 테스트 대기)
- [A00300 batch summary](wip-a00300-batch-summary-table.md) — Target Meshes TSL + 색상 요약 테이블 (v01.02)
- [A00300 zero-area rework](wip-a00300-zero-area-quality-rework.md) — **진행 중**: zero_area_faces 를 shape-quality 로 재작업 + Clear Log
- [A00290 Mix Targets tab](wip-a00290-mix-targets-tab.md) — **신규**: 소스 가중합을 다른 타겟 + 최종(리깅) 메시에 일괄 반영. Base mesh 3모드, 공용 `delta_utils` (v01.17)
- [A00290 Shape Editor tab](wip-a00290-shape-editor-tab.md) — 마야 Shape Editor 대체. `cmds.sculptTarget` 필수, 행 클릭 다중 편집, 제스처당 undo 1회 (v01.10)
- [A00280 cloth-corrective](metahuman-cloth-corrective-A00280.md) — Houdini 알렘빅 캐시 → MetaHuman RBF 코렉티브 일괄 추출(invertShape)
- [A00275 Expand Bind](wip-a00275-expand-bind.md) — 루프 위 조인트에 측지 거리 기반 균등 바인드(Kangaroo ClosestExpand 대체). **엣지 루프를 주면** 밴드 전 줄이 루프 비율 유지, coverage 없이 정규화만 하면 커브가 무의미, falloff 커브 위젯 자작 (v01.10)
- [A00275 Move Joints](wip-a00275-move-joints.md) — Edit 토글로 메시 변형 없이 조인트 이동 → 재바인드, 웨이트 불변 (v01.08)
- [A00275 SkinTool Bind Pose](wip-a00275-skintool-bindpose.md) — Update Bind Pose 탭. bindPreMatrix 인덱스는 `matrix[]` 연결에서 얻어야 함 (v01.03)
- [A00275 Transfer tab](wip-a00275-transfer-tab.md) — N 소스 → 선택 메시/버텍스 전부. copySkinWeights 는 컴포넌트 선택 무시 (v01.07)
- [A00270 Classic tab](wip-a00270-classic-tab.md) — 레거시 move_skinWeightTool 2버튼 UI 를 Classic 탭으로 이식

## 툴 작업 (탭 · 기능 추가)

- [A00220 Pin toggle](wip-a00220-pin.md) — Always on Top 토글 (v01.13)
- [A00220 dino save pulse](wip-a00220-dino-save-pulse.md) — 저장 순간 상태 공룡이 accent 색으로 점프 (v01.09)
- [A00210 PathStructure tree](wip-a00210-pathstructure-tree-depth.md) — Preview 를 QTreeWidget + Capture/View Depth 로 (v01.24)
- [A00210 Recreate To + Rename](wip-a00210-recreate-to-rename.md) — 명시적 대상 경로 필드 + Rename 버튼 (v01.28)
- [A00210 PathStructure files](wip-a00210-pathstructure-files.md) — 파일도 캡처/재생성, 0바이트 + `__` 표식 (v01.29)
- [A00170 Edge Loop drivers](wip-a00170-edge-loop-drivers.md) — AttachCrv 하위 탭. 루프→커브→널→(con/ctl/tgt 컨트롤러)→조인트. joint `.radius` 는 맞고 화면 크기만 Joint Size 배율 (v01.15)
- [A00170 Stretch tab](wip-a00170-stretch-tab.md) — Default Distance 가 Stretch 구동, linear + Sigmoid 노드망 (v01.11)
- [A00170 AttachCrv tab](wip-a00170-attachcrv-tab.md) — TSL 오브젝트를 커브 최근접점에 부착
- [A00170 Remap List Attributes](wip-a00170-remap-listattrs.md) — Remap Value 탭에 전체 어트리뷰트 목록 + 검색
- [A00145 Connect both directions](wip-a00145-connect-both-directions.md) — 역방향 연결(인자 순서만 뒤집기) + 개수 달라도 적은 쪽만큼 부분 연결·실패해도 계속 (v01.24~01.25)
- [A00145 Match from Source](wip-a00145-attr-name-matching.md) — 이름 유사 어트리뷰트를 소스 순서대로 찾아 Connect 로 연결. 1000x1000 = 0.15s (v01.21)
- [A00145 Target Edit](wip-a00145-target-edit.md) — 타깃 추가/삭제. Maya 명령의 add/remove, 마지막 타깃 삭제 = 노드 삭제, remove 후 offset 재베이크 (v01.26)
- [A00145 Target Replace](wip-a00145-target-replace.md) — 컨스트레인트의 타깃(드라이버)을 다른 오브젝트로 일괄 교체. 재생성 대신 `target[i]` 연결만 rewire → weight/이름 보존 (v01.20)
- [A00145 Attribute tab](a00145-attribute-tab-blendshape-alias.md) — 어트리뷰트 복사 + blendShape 타깃은 `weight[]` 별칭(aliasAttr) (v01.17)
- [A00145 skin constraint types](wip-a00145-skin-constraint-types.md) — Parent/Scale/Point/Orient 라디오, interpType 은 attributeQuery 가드 (v01.16)
- [A00145 Constraint Transfer](wip-a00145-constraint-transfer.md) — 기존 컨스트레인트를 다른 오브젝트로 이전(재생성) (v01.14)
- [A00145 Group Create](wip-a00145-group-create.md) — 동일 위치/회전 zero-out 노드 삽입, 타입 매칭 (v01.13)
- [A00145 Match DOOTOOL options](wip-a00145-match-dootool-options.md) — Match 탭에 T/R/S/Parent 체크박스 이식 (v01.10)
- [A00120 FKIK constraint-free bake](wip-a00120-fkik-bake-constraintfree.md) — parentConstraint 대신 프레임별 matchTransform (애님 레이어 포즈 깨짐 수정)
- [A00110 Fill Keys](wip-a00110-fill-keys.md) — 구간 전 프레임 키 채우기(기존 키 방치) + 애니 레이어 지정, Key Edit 하위 8탭 재편 (v01.40)
- [A00110 Stagger Offset](wip-a00110-stagger-offset.md) — TSL 순서 × Offset 계단식 키 이동, settle 커밋 모델 (v01.34)
- [A00110 Graph Focus tab](wip-a00110-graph-focus.md) — 선택 변경 시 그래프 에디터 자동 프레이밍 (v01.30)
- [A00110 Get Sel Range](wip-a00110-get-sel-range.md) — 선택 키의 최소/최대로 Start/End 동시 채우기 (v01.35)
- [A00110 Euler Filter range](wip-a00110-euler-filter-range.md) — 구간 한정 오일러 필터. filterCurve 는 start/endTime 을 존중, 앵커 = 구간 안 첫 키 (v01.37) + 씬/키 선택 감지 원버튼 (v01.38)
- [A00340 button colors](wip-a00340-button-colors.md) — 버튼별 커스텀 색 + Color Select 모드 (v01.03)
- [A00340 split layout](wip-a00340-split-layout.md) — QSplitter 로 Controls 박스 접기 (v01.04)
- [A00060 world-space joint pos](wip-a00060-world-space-joint-pos.md) — Curve/Divide 조인트 생성을 월드 절대좌표로 (v01.03)
