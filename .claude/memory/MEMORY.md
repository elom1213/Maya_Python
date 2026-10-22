# Memory Index

한 줄 = 한 메모(같은 툴은 한 줄에 묶음). 상세 · 버전 이력은 각 파일에 — 여기엔 훅만.

> 저장소 규칙은 루트 `CLAUDE.md`, 세션 공통 규칙(한국어 · 푸시 · 커밋 · 라우팅)은 전역 `JUN_Claude/CLAUDE.md`.
> 학습 노트 메모는 `JUN_Study/.claude/memory/`, UE 메모는 `JUN_UE/.claude/memory/` (2026-08-24 이동).

## 작업 방식 · 사용자 선호

- [Push target Dnable/dev](push-target-dnable-dev.md) — push 대상은 Dnable_repo 의 dev
- [No history rewrite / master on request](no-history-rewrite-master-on-request.md) — 재작성 금지, master 최신화는 그 턴 요청 시만
- [Push includes tool guide docs](push-includes-tool-guide-docs.md) — 툴 push 에 docs 가이드 · version · WORKLOG 함께
- [Push refreshes README date](push-refresh-readme-date.md) — 푸시 때 루트 README 의 `최근 갱신` 날짜 진단 · 최신화해 함께 담기
- [WORKLOG maintenance](worklog-maintenance.md) — 최신이 위, 날짜 헤딩 중복 금지, 월 롤링
- [Docs go in JUN_All/docs](docs-go-in-jun-all-docs.md) — 툴 안내 = docs/, 계획 = docs/plans/, 학습 = JUN_Study
- [A00500_reloader](wip-a00500-reloader.md) — dev 리로더는 `dev/A00500_reloader` 셸프 툴, `dev/reloader_v02` 는 재노출(launch.py 들이 쓴다) · 전부 리로드는 다른 툴 창을 닫을 수 있다
- [A00520 icon_builder · A00530 dependency_check](wip-a00500-reloader.md) — dev 툴 4개 전부 같은 모양(launch.run · __dragDrop · icon · docs), 옛 `dev/build_icons.py` · `check_dependencies.py`(재노출 유지) 자리, 새 tools 는 A00540 부터
- [A00510_release_builder](wip-release-builder-qt.md) — 릴리즈 복사 개발툴(dev/, 옛 release_builder_QT, v01.03 부터 A 번호 + __dragDrop_A00510)
- [Release layout & launch.py](release-layout-launch-py.md) — 릴리즈본은 Framework 동봉 · config/dev 없음, launch.py 가 두 배치 구분. **툴 간 import 금지**
- [Release install scripts](release-install-scripts.md) — userSetup 이름 고정, git 출력 UTF-8 vs 콘솔 cp949
- [Update portfolio on tool work](update-portfolio-on-tool-work.md) — portfolio EN/KR 동기, 커밋 통계 건드리지 않기
- [Launcher buttons follow current version](launcher-buttons-follow-current-version.md) — 새 버전 폴더면 A00370 버튼도 옮길 것
- [Prefer PySide for new tools](prefer-pyside-for-new-tools.md) — 신규 툴은 PySide(arch B)
- [JUN_JALI repo](jun-jali-repo.md) — VisemeNet 포크, 푸시는 origin main, `.venv` 추론 · angela_JALI 리그 적용
- [kangaroo plugin read-only](kangaroo-plugin-external-readonly.md) · [PoseWrangler fork patch](posewrangler-plugin-fork-patch.md)

## 검증 · 창 크기

- [mayapy headless verify](mayapy-headless-verify.md) — maya.cmds 동작은 mayapy + standalone 으로 실측
- [offscreen size needs theme](offscreen-size-needs-theme.md) — 테마 입히고 재라, 오프스크린 px > 마야 px (잰 값을 박지 말 것)
- [QTabWidget min size = all pages](qtabwidget-min-size-hidden-pages.md) — 숨은 페이지까지 최소의 최댓값 → 창이 못 줄어듦, 탭을 QScrollArea 에 + fit_to_content
- [window taller than screen](window-taller-than-screen-ghost.md) — 화면 밖 잘림 = "로그창 2개", 탭 스크롤 + 작업 영역 높이
- [QApplication before standalone](qapplication-before-maya-standalone.md) · [standalone app package collision](standalone-app-package-collision.md)(`tools.<tool>.app.*`)
- icons — [New tool needs icon](new-tool-needs-icon.md) · [Standalone taskbar icon](standalone-taskbar-icon-method.md) · [Pin for maya.cmds tools](pin-for-maya-cmds-tools.md)
- [shelf childArray has separators](shelf-childarray-has-separators.md) — 구분선에 `shelfButton` 질의는 RuntimeError

## 마야 공통 함정

- [maya reference import traps](maya-reference-import-traps.md) — `loadReferenceDepth none` 저장은 언로드로 굳음 · 언로드는 import 불가 · 부모 import 시 중첩이 최상위로 · `.ma` 머리글 file 문장 여러 줄 · mayapy 워커는 uninitialize 필수
- [FBX export selected scope](fbx-export-selected-scope.md) · [Maya 2023 compat](maya-2023-compat.md)(sin/cos 노드 없음) · [Maya loadPlugin no __file__](maya-loadplugin-no-file.md)
- [undo_chunk by default](undo-chunk-by-default.md) · [cmds.toggle not undoable](maya-toggle-cmd-not-undoable.md) · [attr reorder = deleteAttr + undo](maya-attr-reorder-deleteattr-undo.md)
- attrs — [channel box & references](attr-channelbox-and-references.md)(레퍼런스 어트리뷰트 표시 상태 못 바꿈) · [lock: parent compound overrides child unlock](maya-attr-lock-parent-compound.md) · [addAttr min/max raises](addattr-min-max-raises-not-clamps.md) · [xform silent on locked](xform-silent-on-locked-channels.md) · [getAttr settable lies](getattr-settable-lies-for-constrained.md) · [list_attrs multi detection](list-attrs-multi-detection.md) · [setAttr Int32Array no count](setattr-int32array-no-count.md)
- connections — [compound connect leaves child connections](compound-connect-leaves-child-connections.md) · [constraint target plugs & offset spaces](constraint-target-plugs-and-offset-spaces.md) · [parentMatrix includes own OPM](parentmatrix-includes-offsetparentmatrix.md)
- animLayer — [copy/cut traps](animlayer-copy-cut-traps.md) · [no global selected query](animlayer-no-global-selected-query.md)
- keys — [keyframe over squeezes on collision](keyframe-over-squeezes-on-collision.md) · [setKeyframe insert needs a curve](setkeyframe-insert-needs-existing-curve.md) · [pasteKey attribute = order match](pastekey-attribute-matches-by-order.md) · [animated attr: key + setAttr](animated-attr-setkeyframe-plus-setattr.md)
- shading — [per-face assignment](shading-per-face-assignment.md)(`getConnectedShaders`, `sets -q` 는 트랜스폼 기준, 큰 선택은 API) · [utility nodes inherit shadingDependNode](utility-nodes-inherit-shadingdependnode.md) · [node purity signals](node-purity-signals.md)
- names — [Referenced node name compares](referenced-node-name-comparisons.md) · [Set rename traps](maya-set-rename-traps.md) · [UUID-safe rename](uuid-safe-rename-duplicate-names.md) · [name matching: token index](attr-name-matching-token-index.md)
- rig — [ikHandle creation traps](ikhandle-creation-traps.md) · [hold mesh while moving joints](skincluster-hold-mesh-while-moving-joints.md) · [surface normal handedness](surface-normal-handedness.md)
- skin — [weights: physical index](skincluster-weight-index-physical.md) · [deforms user normals](skincluster-deforms-user-normals.md)(노멀 쓰기는 MFnMesh + dgdirty)
- blendShape — [delta space = origin](blendshape-delta-space-origin.md) · [target name vs alias](blendshape-target-name-vs-alias.md) · [live target deltas](blendshape-live-target-inputpointstarget.md) · [sculpt target: pnts redirect](sculpt-target-pnts-redirect.md) · [shape.pnts is post-deformation](shape-pnts-is-post-deformation.md)
- shapes/curves — [parent -s -add = instance](parent-shape-add-is-instance.md) · [extendToShape picks wrong shape](extendtoshape-picks-wrong-shape.md)(공용 `maya_shape`) · [pointPosition: points only](pointposition-points-only.md) · [cmds -pivot is world](cmds-scale-rotate-pivot-is-world.md) · [referenced curve CV write](referenced-curve-cv-write.md)(xform 으로만)
- [viewport Tab is MTK](maya-viewport-tab-is-mtk.md) — 뷰포트 Tab 은 hotkey 무시, `nexOpt mayaTabPressCmd` 를 바꿔 끼울 것 (GUI 전용)
- [Euler closestSolution not equivalent](euler-closest-solution-not-equivalent.md) — 짐벌 근처 다른 회전, closestCut + alternate 로 · 오일러는 축별로 안 더해진다
- API lifetime — [MPlug.asMObject](mplug-asmobject-lifetime.md) · [MFn cvPositions](mfn-cvpositions-lifetime.md)(읽는 즉시 tuple 로)

## 공용 위젯 · 프레임워크

- [zero-arg super after reload](reload-stale-instance-super.md) — Framework 클래스는 `super()` 만
- [token name widget](framework-token-name-widget.md) — Profile + 칸, A00330 · A00480 공유, 칸 편집은 `Save` 버튼으로만 저장
- [control shapes](framework-control-shapes.md) · [mirror tokens](framework-mirror-tokens.md)(공용 json, 경계 매칭)
- TSL — [(Null) is red](framework-tsl-null-placeholder-red.md) · [UUID selection](wip-tsl-uuid-selection.md) · [attach_uuids](framework-tsl-attach-uuids.md)(씬 노드 아니면 False) · [list_limit summary](framework-tsl-list-limit.md) · [max-height squeezes buttons](tsl-widget-max-height-squeezes-buttons.md) · [selection order](tsl-selection-order.md) · [select_no_expand](wip-a00440-find-tab.md)(세트 리스트는 켤 것)
- [Menu bar + common items](framework-menubar-widget.md)(`tool_menu.COMMON_MENUS` 한 줄) · [Dev Mode menu widget](framework-devmode-widget.md) · [Sub-tabs over collapsibles](prefer-subtabs-over-stacked-collapsibles.md)
- [checkList behavior](framework-checklist-behavior.md) — QListWidget 다중 체크는 `JUN_mod_checkList_qt_v01(lw)` 한 줄. 트리 판은 `MOD_checkTree_qt_v01`, 폴더 트리는 `MOD_fileTree_qt_v01`(A00240 Tree 승격) — [[wip-a00210-maya-reference-tab]]
- widgets — [log level colors](framework-log-level-colors.md) · [log](framework-log-widget.md)(47툴 교체 완료) · [expand](framework-expand-widget.md)(이동) · [filter](framework-filter-widget.md)(트리 모드) · [falloff curve](framework-falloff-curve-widget.md) · [progress popup](framework-progress-widget.md)(마지막 값 스로틀 금지) · [timeRange](framework-timerange-widget.md)
- Qt 함정 — [exclusive radio uncheck ignored](qt-exclusive-radio-uncheck-ignored.md) · [QTreeWidgetItem checkable default](qtreewidgetitem-checkable-default-flag.md) · [clicked passes checked bool](qt-clicked-passes-checked-bool.md) · [QDoubleSpinBox keyboardTracking](qdoublespinbox-keyboard-tracking.md)

## 툴 작업

- A00010 — [HIK Mirror](wip-a00010-hik-mirror.md)(이름 1순위 · 위치 폴백, 같은 타입 후보, 공용 미러 토큰)
- A00040 — [Joints only export](wip-a00040-joints-only-export.md) · 새 파일 기능은 A00480 으로
- A00050 — [uvTool V02](wip-a00050-uvtool-v02.md)(UV Sets 탭은 A00380 으로 이식 완료, 코어 공유)
- A00060 — [From Object Match Rotation](wip-a00060-from-object-match-rotation.md) · [Curve By Count](wip-a00060-curve-by-count.md)(길이 등분 아님) · [Aim Root mode](wip-a00060-aim-root-mode.md) · [V03 tab reorg](wip-a00060-v03-tab-reorg.md) · [IK Edit](wip-a00060-ik-edit.md) · [Pole Target](wip-a00060-pole-target.md) · [world-space joint pos](wip-a00060-world-space-joint-pos.md)
- A00060 · A00130 — [IK Edit keep PV offset](wip-ik-edit-keep-pv-offset.md)(2조인트 체인은 솔버가 축을 정함, 길이는 IK 전에)
- A00090 — [PoseWrangler bundle](wip-a00090-posewrangler-bundle.md) · [rule versions](wip-a00090-rule-versions.md)
- A00110 — [Mirror Key: Scale](wip-a00110-mirror-scale.md) · [Follow: component target](wip-a00110-follow-component-target.md) · [Layer key copy](wip-a00110-layer-key-copy.md) · [Copy Key custom attrs](wip-a00110-copykey-custom-attrs.md) · [Copy Key 1->n](wip-a00110-copykey-one-to-many.md) · [V02 tab taxonomy](wip-a00110-tab-taxonomy.md) · [Fill Keys](wip-a00110-fill-keys.md) · [Stagger Offset](wip-a00110-stagger-offset.md) · [Graph Focus](wip-a00110-graph-focus.md) · [Get Sel Range](wip-a00110-get-sel-range.md) · [Euler Filter range](wip-a00110-euler-filter-range.md)
- A00120 — [FKIK Auto + Dev Mode](wip-a00120-fkik-auto-devmode.md)(Auto = NS 단위, Release 화면 축소 · GUI 확인 아직) · [constraint-free bake](wip-a00120-fkik-bake-constraintfree.md)
- A00130 V02 — [Match](wip-a00130-v02-match.md) · [Length](wip-a00130-length-values.md) · [IK session](wip-a00130-ik-session.md)(snapEnable 이 undo 를 깬다) · [Orient & Place](wip-a00130-orient.md)(오른팔은 Behavior 미러 하나) · [Pair & Constrain](wip-a00130-pair-constrain.md) · [IK axis](wip-a00130-ik-axis.md)
- A00145 — [Mirror network offsets](wip-a00145-mirror-network-offsets.md) · [Mirror tab](wip-a00145-mirror-tab.md) · [object name match](wip-a00145-object-name-match.md) · [Update offset](wip-a00145-update-offset.md) · [component followers](wip-a00145-component-followers.md) · [Match 1<-n](wip-a00145-match-one-to-many.md) · [(Null) match rows](wip-a00145-match-null-placeholder.md) · [Match Cache](wip-a00145-match-cache.md) · [Match Keep Children](wip-a00145-match-keep-children.md) · [Match DOOTOOL options](wip-a00145-match-dootool-options.md)
- A00145 (계속) — [Connect both directions](wip-a00145-connect-both-directions.md) · [Match from Source](wip-a00145-attr-name-matching.md) · [Target Edit](wip-a00145-target-edit.md) · [Target Replace](wip-a00145-target-replace.md) · [Attribute Edit tab](a00145-attribute-tab-blendshape-alias.md) · [skin constraint types](wip-a00145-skin-constraint-types.md) · [multi constraint types](wip-a00145-multi-constraint-types.md) · [All Targets -> Each Follower](wip-a00145-all-targets.md) · [Constraint Transfer](wip-a00145-constraint-transfer.md) · [Constraint Copy + 모드](wip-a00145-constraint-copy.md) · [Group Create](wip-a00145-group-create.md) · [Set Value](wip-a00145-set-value.md) · [채널박스 표시](attr-channelbox-and-references.md) · [Transfer Connection](wip-a00145-transfer-connection.md)(`listConnections -shapes` 필수) · [Connect by Rule](wip-a00145-connect-rules.md)(json 하나 = 규칙 하나)
- A00170 — [AttachCrv tab](wip-a00170-attachcrv-tab.md)(Maintain offset, 조인트는 JO 벗긴 rotate, Mode 콤보 · Follower 모드) · [Edge Loop drivers](wip-a00170-edge-loop-drivers.md) · [Lip Seal](wip-a00170-lip-seal.md)(Free 모드, sealBase/sealBaseRotate) · [Stretch tab](wip-a00170-stretch-tab.md) · [Remap List Attributes](wip-a00170-remap-listattrs.md)
- A00210 — [Maya > Reference](wip-a00210-maya-reference-tab.md)(레퍼런스 트리 → 체크한 것을 각 파일에 임포트해 저장, **standalone 이라 mayapy 워커**, 처음 A00480 에 만들었다가 옮김, GUI 실제 mayapy 확인 아직) · [PathStructure tree](wip-a00210-pathstructure-tree-depth.md) · [Recreate To + Rename](wip-a00210-recreate-to-rename.md) · [PathStructure files](wip-a00210-pathstructure-files.md)
- A00220 — [Pin toggle](wip-a00220-pin.md) · [dino save pulse](wip-a00220-dino-save-pulse.md) · [Shrink](wip-a00220-shrink.md)
- A00240 — [Junction tab](wip-a00240-junction-tab.md)(lstat 리파스 태그, rmdir 주의 · Tree 우클릭 Reveal (Junction)/(Origin) = 공용 `path_context.origin_of`, v01.21) · [Tree Omit](wip-a00240-tree-omit.md) · [Shrink + tree anim](wip-a00240-shrink-anim.md) · [Button colors](wip-a00240-button-colors.md) · Tree 탭 본체는 Framework `MOD_fileTree_qt` (v01.20)
- A00270 — [Classic tab](wip-a00270-classic-tab.md) · A00280 — [cloth-corrective](metahuman-cloth-corrective-A00280.md)
- A00275 — [Transfer 1:1 pairs](wip-a00275-transfer-pairs.md) · [Smooth tab](wip-a00275-smooth-tab.md) · [Select By Weight](wip-a00275-select-by-weight.md) · [Layer tab](wip-a00275-layer-tab.md)(setWeights 는 undo 안 됨) · [tab reorg](wip-a00275-tab-reorg.md) · [Copy Weights](wip-a00275-copy-weights.md) · [Edit Mesh](wip-a00275-edit-mesh.md) · [Expand Bind](wip-a00275-expand-bind.md) · [Move Joints](wip-a00275-move-joints.md) · [Bind Pose](wip-a00275-skintool-bindpose.md) · [Transfer tab](wip-a00275-transfer-tab.md) · [Classic Native 선택 버텍스만](wip-a00275-classic-partial.md)(To 기준, 미선택 To 는 Skipped)
- A00290 — V02 [tab reorg](wip-a00290-v02-tab-reorg.md)(아래 V01 메모의 탭 경로는 V01 기준) · [Naming tab](wip-a00290-naming-tab.md) · [Target Order](wip-a00290-target-order-tab.md) · [Bake Delete](wip-a00290-bake-delete-tab.md) · [Mix Targets](wip-a00290-mix-targets-tab.md) · [Shape Editor](wip-a00290-shape-editor-tab.md)(`sculptTarget` 필수)
- A00300 — A00380 MeshDoctor 탭으로 이식됨(원본 보존) · [batch summary](wip-a00300-batch-summary-table.md) · [zero-area rework](wip-a00300-zero-area-quality-rework.md)
- A00310 — [Type/Token/Rules](wip-a00310-searchtool-rules.md) · A00330 — [Set Rename](wip-a00330-set-rename.md) · [Token tab](wip-a00330-token-tab.md) · [Quick Rename > Insert](wip-a00330-insert-tab.md)
- A00340 — [SelectionTool](wip-a00340-selectiontool.md) · [button colors](wip-a00340-button-colors.md) · [split layout](wip-a00340-split-layout.md)
- A00350 — [ArrayCreator](wip-a00350-arraycreator.md) · A00360 — [SortTool](wip-a00360-sorttool.md) · A00370 — [ToolLauncher](wip-a00370-toollauncher.md)
- A00380 — [MeshTool Peak](wip-a00380-meshtool-peak.md) · [Match tab](wip-a00380-match-tab.md) · [Match > By Weight](wip-a00380-match-by-weight.md) · [MeshDoctor tab](wip-a00380-meshdoctor-tab.md) · UV Sets 탭([[wip-a00050-uvtool-v02]])
- A00390 — [WindTool](wip-a00390-windtool.md) · [Chain Wave](wip-a00390-chain-wave.md) · [V02 axis & driver](wip-a00390-v02-axis-driver.md) · [V02 Envelope](wip-a00390-v02-envelope.md) · [Lite debug curve](wip-a00390-lite-debug-curve.md)
- A00400 — [CurveTool](wip-a00400-curvetool.md) · [Smooth](wip-a00400-smooth-tab.md) · [Points to Curve](wip-a00400-points-to-curve.md) · [Wrap](wip-a00400-curve-wrap.md) · [Joints](wip-a00400-curve-joints.md) · [Controls](wip-a00400-controls-tab.md) · Combine([instance trap](parent-shape-add-is-instance.md)) · [Shape Edit](wip-a00400-shape-transform.md)(레퍼런스 커브는 xform, Line Width 흡수, Replace > Resolve Pair)
- A00410 — [SecondaryMotion](wip-a00410-secondarymotion.md)(Virtual Child) · A00420 — [Wrapper](wip-a00420-wrapper.md) · A00430 — [DemBone](wip-a00430-dembone.md)
- A00440 — [SetTool](wip-a00440-settool.md) · [Sets x Objects](wip-a00440-sets-x-objects.md) · [Find tab](wip-a00440-find-tab.md) · A00450 — [ManipulatorTool](wip-a00450-manipulatortool.md) · A00460 — [FK & IK](wip-a00460-fk-ik.md)
- A00470 — [MaterialTool](wip-a00470-materialtool.md)(이름 규칙 진단 · Copy Material · Rename to Suggested · Select Materials/Faces 는 API 선택 · 세로 줄이는 방향 유지)
- A00480 — [FileTool](wip-a00480-filetool.md)(Export/Import/Path, Export 규칙, Naming = 공용 토큰 위젯. Maya 탭은 A00210 으로 감)
- A00490 — [KeyboardTool](wip-a00490-keyboardtool.md)(크롬 계열은 활성 창만 키를 받는다 → Auto)
- A00540 — [JaliLipSync](wip-a00540-jalilipsync.md)(VisemeNet txt → JALI 리그 키, 짝 = JUN_JALI 변환기 · 원본 모델은 추론도 무작위 · 끝 0.32초 짧음)
- A00550 — [PoseMapper](wip-a00550-posemapper.md)(음소 → BS 포즈 json · Connect, blendWeighted 의 weight 원소 없는 input = 안 보이고 1.0 · getAttr 가 원소를 만든다)
- JALI 슬라이더 리그 — [A0020_jali_slider_ctl](wip-jali-slider-ctl.md)(angela 1:1 슬라이더 22 + JaLi 박스, remapValue 리맵, DUMMY_IN/OUT 3쌍, global_scale · 생성/검증은 JUN_JALI examples · GUI 확인 아직)
