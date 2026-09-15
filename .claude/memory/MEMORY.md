# Memory Index

한 줄 = 한 메모(같은 툴의 기능 메모는 한 줄에 묶음). 자세한 내용은 각 파일에 있다.

> 저장소 규칙은 루트 `CLAUDE.md`, 세션 공통 규칙(한국어 · 푸시 · 커밋 · 라우팅)은 전역 `JUN_Claude/CLAUDE.md`.
> 2026-08-24 에 학습 노트 메모는 `JUN_Study/.claude/memory/`, UE 메모는 `JUN_UE/.claude/memory/` 로 옮겼다.
> 본문의 `[[push-only-when-asked]]` 같은 링크는 전역 규칙으로 옮겨진 것들이다.

## 작업 방식 · 사용자 선호

- [Push target Dnable/dev](push-target-dnable-dev.md) — push 대상은 Dnable_repo 의 dev
- [No history rewrite / master on request](no-history-rewrite-master-on-request.md) — 재작성 금지, master 최신화는 그 턴 요청 시만
- [Push includes tool guide docs](push-includes-tool-guide-docs.md) — 툴 push 에 docs 가이드·version·WORKLOG 함께
- [WORKLOG maintenance](worklog-maintenance.md) — 최신이 위, 날짜 헤딩 중복 금지, 월 롤링
- [Docs go in JUN_All/docs](docs-go-in-jun-all-docs.md) — 분석/설명 문서 위치
- [Update portfolio on tool work](update-portfolio-on-tool-work.md) — portfolio EN/KR 동기, 커밋 통계 건드리지 않기
- [Prefer PySide for new tools](prefer-pyside-for-new-tools.md) — 신규 툴은 PySide(arch B)
- [kangaroo plugin read-only](kangaroo-plugin-external-readonly.md) — 외부 플러그인, 수정 금지
- [PoseWrangler fork patch](posewrangler-plugin-fork-patch.md) — 포크 위치 + serializer objExists 패치

## 검증 · 마야 공통 함정

- [FBX export selected scope](fbx-export-selected-scope.md) — 내용은 `FBXExportIncludeChildren`/`InputConnections` 로 통제
- [mayapy headless verify](mayapy-headless-verify.md) — maya.cmds 동작은 mayapy + standalone 으로 확인
- [QApplication before standalone](qapplication-before-maya-standalone.md) — `QApplication` 을 `initialize()` 앞에
- [undo_chunk by default](undo-chunk-by-default.md) — 반복 씬 변경은 `undo_chunk()` 로
- [Maya 2023 compat](maya-2023-compat.md) — sin/cos 노드 없음(eulerToQuat 우회)
- [addAttr min/max raises](addattr-min-max-raises-not-clamps.md) — 범위 밖 setAttr 은 클램프 아닌 에러
- [xform silent on locked](xform-silent-on-locked-channels.md) — 잠긴 채널은 조용히 건너뛴다 → 되읽어 확인
- [getAttr settable lies](getattr-settable-lies-for-constrained.md) — 컨스트레인트 구동도 True, 연결+lock 으로 판정
- [Maya loadPlugin no __file__](maya-loadplugin-no-file.md) — loadPlugin .py 에 `__file__` 없음
- animLayer — [copy/cut traps](animlayer-copy-cut-traps.md)(`cutKey` 는 `animLayer` 를 안 받는다) · [no global selected query](animlayer-no-global-selected-query.md)(`ls(type=animLayer)` 순회)
- [Referenced node name compares](referenced-node-name-comparisons.md) — 솔버까지 네임스페이스, 타입으로 판정
- [Set rename traps](maya-set-rename-traps.md) — `select(set)` 은 멤버를 펼침, 짧은 이름 rename 은 NS 를 벗김
- [ikHandle creation traps](ikhandle-creation-traps.md) — SC 에도 poleVector, ikSpringSolver 는 MEL 로
- [name matching: token index](attr-name-matching-token-index.md) — 편집 거리 말고 토큰 역색인+IDF
- [hold mesh while moving joints](skincluster-hold-mesh-while-moving-joints.md) — `bindPreMatrix*matrix` 상수 유지
- [parentMatrix includes own OPM](parentmatrix-includes-offsetparentmatrix.md) — OPM 을 구동할 땐 `obj.parentInverseMatrix` 금지(자기 OPM 을 되먹음), 부모 `worldInverseMatrix` 직결
- [surface normal handedness](surface-normal-handedness.md) — normal = tanU×tanV, matrix pinning 의 [tanU, N, tanV] 는 왼손계 → Z = tanU×N 로 직교화
- [constraint target plugs & offset spaces](constraint-target-plugs-and-offset-spaces.md) — 노드 단위 열거, offsetT/R 공간이 다름
- [shape.pnts is post-deformation](shape-pnts-is-post-deformation.md) — pnts 는 디포머 뒤에 더해진다
- blendShape — [delta space = origin](blendshape-delta-space-origin.md) · [target name vs alias](blendshape-target-name-vs-alias.md)(노드 이름 ≠ 웨이트 alias, 인덱스는 max+1) · [live target deltas](blendshape-live-target-inputpointstarget.md)(라이브 타겟은 메시를 옮겨야 함)
- keys — [setKeyframe insert needs a curve](setkeyframe-insert-needs-existing-curve.md)(없으면 조용히 no-op) · [pasteKey attribute = order match](pastekey-attribute-matches-by-order.md)(plug 단위로) · [animated attr: key + setAttr](animated-attr-setkeyframe-plus-setattr.md)
- [cmds.toggle not undoable](maya-toggle-cmd-not-undoable.md) — `toggle -localAxis` 대신 setAttr
- [extendToShape picks wrong shape](extendtoshape-picks-wrong-shape.md) — 금지, 공용 `maya_shape` 사용
- [pointPosition: points only](pointposition-points-only.md) — 엣지/페이스는 xform 평균
- [skin weights: physical index](skincluster-weight-index-physical.md) — get/setWeights 는 물리 인덱스
- [setAttr Int32Array no count](setattr-int32array-no-count.md) — Int32Array 는 개수를 붙이지 않는다
- [list_attrs multi detection](list-attrs-multi-detection.md) — `attributeQuery(multi=True)`
- [UUID-safe rename](uuid-safe-rename-duplicate-names.md) — 동명 노드 대비 UUID 보관
- [standalone app package collision](standalone-app-package-collision.md) — `tools.<tool>.app.*` 로 import
- icons — [New tool needs icon](new-tool-needs-icon.md)(svg+png 32px) · [Standalone taskbar icon](standalone-taskbar-icon-method.md)(다중크기 .ico + AppUserModelID)
- [Pin for maya.cmds tools](pin-for-maya-cmds-tools.md) — maya_ui_widget() + WindowStaysOnTopHint

## 공용 위젯 · 프레임워크

- TSL — [UUID selection](wip-tsl-uuid-selection.md)((uuid, component) 보관) · [attach_uuids](framework-tsl-attach-uuids.md)(씬 노드 아닌 리스트는 False) · [list_limit summary](framework-tsl-list-limit.md)(500+ 요약) · [max-height squeezes buttons](tsl-widget-max-height-squeezes-buttons.md)(`list_widget` 에만) · [selection order](tsl-selection-order.md)(`trackSelectionOrder` 꺼지면 `ls(os)` 도 인덱스 순)
- [Sub-tabs over collapsibles](prefer-subtabs-over-stacked-collapsibles.md) — 섹션 3~4개 넘으면 중첩 탭
- Framework 위젯 — [expand](framework-expand-widget.md)(복제 말고 이동) · [filter](framework-filter-widget.md)(v2 트리 모드) · [mirror tokens](framework-mirror-tokens.md)(공용 json, 경계 매칭) · [falloff curve](framework-falloff-curve-widget.md) · [progress popup](framework-progress-widget.md)(마지막 값 스로틀 금지) · [timeRange](framework-timerange-widget.md)
- Qt 함정 — [QTreeWidgetItem checkable default](qtreewidgetitem-checkable-default-flag.md) · [clicked passes checked bool](qt-clicked-passes-checked-bool.md) · [QDoubleSpinBox keyboardTracking](qdoublespinbox-keyboard-tracking.md)

## 툴 작업

- A00010 — [HIK Mirror](wip-a00010-hik-mirror.md)(이름 1순위·위치 폴백, v02.01)
- A00040 — [Joints only export](wip-a00040-joints-only-export.md)(FBX 옵션으로 non-joint 제외, v02.06)
- A00060 — [V03 tab reorg](wip-a00060-v03-tab-reorg.md) · [IK Edit](wip-a00060-ik-edit.md)(폴 벡터 역산) · [Pole Target](wip-a00060-pole-target.md)(pointConstraint 하나, Slide, v03.08) · [world-space joint pos](wip-a00060-world-space-joint-pos.md)
- A00090 — [PoseWrangler bundle](wip-a00090-posewrangler-bundle.md)(`<driver>_default`, v01.07) · [rule versions](wip-a00090-rule-versions.md)
- A00110 — [Follow: component target](wip-a00110-follow-component-target.md) · [Layer key copy](wip-a00110-layer-key-copy.md)(v02.13) · [Copy Key custom attrs](wip-a00110-copykey-custom-attrs.md) · [Copy Key 1->n](wip-a00110-copykey-one-to-many.md) · [V02 tab taxonomy](wip-a00110-tab-taxonomy.md) · [Fill Keys](wip-a00110-fill-keys.md) · [Stagger Offset](wip-a00110-stagger-offset.md) · [Graph Focus](wip-a00110-graph-focus.md) · [Get Sel Range](wip-a00110-get-sel-range.md) · [Euler Filter range](wip-a00110-euler-filter-range.md)
- A00120 — [FKIK constraint-free bake](wip-a00120-fkik-bake-constraintfree.md)(프레임별 matchTransform)
- A00130 V02 — [Match](wip-a00130-v02-match.md)(NS 양쪽 탐색) · [Length](wip-a00130-length-values.md) · [IK session](wip-a00130-ik-session.md)(snapEnable 이 undo 를 깬다) · [Orient & Place](wip-a00130-orient.md) · [Pair & Constrain](wip-a00130-pair-constrain.md)(parentConstraint 가 조용히 타깃을 늘린다, v02.17) · [IK axis](wip-a00130-ik-axis.md)(`twist` 로만)
- A00145 — [Mirror tab](wip-a00145-mirror-tab.md)(Reflect=`M·S`, Apply Left->Right, v01.40) · [object name match](wip-a00145-object-name-match.md) · [Update offset](wip-a00145-update-offset.md)(타깃은 전부) · [component followers](wip-a00145-component-followers.md) · [Match 1<-n](wip-a00145-match-one-to-many.md) · [(Null) match rows](wip-a00145-match-null-placeholder.md) · [Match Cache](wip-a00145-match-cache.md)
- A00145 (계속) — [Connect both directions](wip-a00145-connect-both-directions.md) · [Match from Source](wip-a00145-attr-name-matching.md) · [Target Edit](wip-a00145-target-edit.md) · [Target Replace](wip-a00145-target-replace.md) · [Attribute tab](a00145-attribute-tab-blendshape-alias.md) · [skin constraint types](wip-a00145-skin-constraint-types.md) · [Constraint Transfer](wip-a00145-constraint-transfer.md) · [Group Create](wip-a00145-group-create.md) · [Match DOOTOOL options](wip-a00145-match-dootool-options.md)
- A00170 — [AttachCrv tab](wip-a00170-attachcrv-tab.md)(Maintain offset = OPM 구동 · NURBS surface 지원, v01.23) · [Edge Loop drivers](wip-a00170-edge-loop-drivers.md) · [Lip Seal](wip-a00170-lip-seal.md)(rest 포즈를 머리 공간에, v01.21) · [Stretch tab](wip-a00170-stretch-tab.md) · [Remap List Attributes](wip-a00170-remap-listattrs.md)
- A00210 — [PathStructure tree](wip-a00210-pathstructure-tree-depth.md) · [Recreate To + Rename](wip-a00210-recreate-to-rename.md) · [PathStructure files](wip-a00210-pathstructure-files.md)(v01.29)
- A00220 — [Pin toggle](wip-a00220-pin.md) · [dino save pulse](wip-a00220-dino-save-pulse.md)
- A00270 — [Classic tab](wip-a00270-classic-tab.md)
- A00275 — [tab reorg](wip-a00275-tab-reorg.md)(탭 인덱스 판단 주의) · [Copy Weights](wip-a00275-copy-weights.md)(v01.18) · [Edit Mesh](wip-a00275-edit-mesh.md) · [Expand Bind](wip-a00275-expand-bind.md) · [Move Joints](wip-a00275-move-joints.md) · [Bind Pose](wip-a00275-skintool-bindpose.md) · [Transfer tab](wip-a00275-transfer-tab.md)
- A00280 — [cloth-corrective](metahuman-cloth-corrective-A00280.md)(알렘빅 → RBF 코렉티브)
- A00290 — [Naming tab](wip-a00290-naming-tab.md)(FBX 엔 별칭뿐, v01.22) · [Target Order](wip-a00290-target-order-tab.md) · [Bake Delete](wip-a00290-bake-delete-tab.md) · [Mix Targets](wip-a00290-mix-targets-tab.md) · [Shape Editor](wip-a00290-shape-editor-tab.md)(`sculptTarget` 필수)
- A00300 — [batch summary](wip-a00300-batch-summary-table.md) · [zero-area rework](wip-a00300-zero-area-quality-rework.md)(**진행 중**)
- A00310 — [SearchTool](wip-a00310-searchtool-merge.md)(Maya 테스트 대기) · A00330 — [Set Rename](wip-a00330-set-rename.md)
- A00340 — [SelectionTool](wip-a00340-selectiontool.md) · [button colors](wip-a00340-button-colors.md) · [split layout](wip-a00340-split-layout.md)
- A00350 — [ArrayCreator](wip-a00350-arraycreator.md) · A00360 — [SortTool](wip-a00360-sorttool.md) · A00370 — [ToolLauncher](wip-a00370-toollauncher.md)
- A00380 — [MeshTool Peak](wip-a00380-meshtool-peak.md) · [Match tab](wip-a00380-match-tab.md)
- A00390 — [WindTool](wip-a00390-windtool.md) · [Chain Wave](wip-a00390-chain-wave.md) · [V02 axis & driver](wip-a00390-v02-axis-driver.md) · [V02 Envelope](wip-a00390-v02-envelope.md) · [Lite debug curve](wip-a00390-lite-debug-curve.md)(v02.03)
- A00400 — [CurveTool](wip-a00400-curvetool.md) · [Smooth](wip-a00400-smooth-tab.md)(닫힌 커브 우회, v01.09) · [Points to Curve](wip-a00400-points-to-curve.md) · [Wrap](wip-a00400-curve-wrap.md) · [Joints](wip-a00400-curve-joints.md)
- A00410 — [SecondaryMotion](wip-a00410-secondarymotion.md)(FK 관성 굽기, v01.08) · A00420 — [Wrapper](wip-a00420-wrapper.md) · A00430 — [DemBone](wip-a00430-dembone.md)
- A00440 — [SetTool](wip-a00440-settool.md)(v01.01) · A00450 — [ManipulatorTool](wip-a00450-manipulatortool.md) · A00460 — [FK & IK](wip-a00460-fk-ik.md)(v01.04)
