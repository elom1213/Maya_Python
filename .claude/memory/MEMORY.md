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
- [release_builder_QT](wip-release-builder-qt.md) — 릴리즈 복사 개발툴(dev/), v01.02 필터 · 공용 로그창 · 아이콘
- [Release layout & launch.py](release-layout-launch-py.md) — 릴리즈본은 Framework 를 툴 안에 동봉하고 `config.py`/`dev` 가 없다, launch.py 가 두 배치를 구분해야 남의 PC 에서 열린다
- [Release install scripts](release-install-scripts.md) — userSetup 은 이름이 고정(`userSetup_001.py` 는 안 읽힌다) · git 출력은 UTF-8 인데 콘솔은 cp949, 둘 다 고쳐야
- [Update portfolio on tool work](update-portfolio-on-tool-work.md) — portfolio EN/KR 동기, 커밋 통계 건드리지 않기
- [Launcher buttons follow current version](launcher-buttons-follow-current-version.md) — 새 버전 폴더를 만들면 A00370 프로파일 버튼도 옮길 것 (옛 폴더를 가리켜도 에러가 안 난다)
- [Prefer PySide for new tools](prefer-pyside-for-new-tools.md) — 신규 툴은 PySide(arch B)
- [kangaroo plugin read-only](kangaroo-plugin-external-readonly.md) — 외부 플러그인, 수정 금지
- [PoseWrangler fork patch](posewrangler-plugin-fork-patch.md) — 포크 위치 + serializer objExists 패치

## 검증 · 마야 공통 함정

- [FBX export selected scope](fbx-export-selected-scope.md) — 내용은 `FBXExportIncludeChildren`/`InputConnections` 로 통제
- [mayapy headless verify](mayapy-headless-verify.md) — maya.cmds 동작은 mayapy + standalone 으로 확인
- [offscreen size needs theme](offscreen-size-needs-theme.md) — 창 크기는 테마 qss 를 입히고 재라 (한 줄에 나란히 둔 것이 최소 폭) · **테마를 입혀도 오프스크린 px > 마야 px — 잰 최소 폭을 창 크기로 박지 말 것**
- [QApplication before standalone](qapplication-before-maya-standalone.md) — `QApplication` 을 `initialize()` 앞에
- [undo_chunk by default](undo-chunk-by-default.md) — 반복 씬 변경은 `undo_chunk()` 로
- [Maya 2023 compat](maya-2023-compat.md) — sin/cos 노드 없음(eulerToQuat 우회)
- [attr channel box & references](attr-channelbox-and-references.md) — 보이는 상태는 keyable / cb 둘뿐, **레퍼런스로 들어온 어트리뷰트는 표시 상태를 못 바꾼다**(만들 때 정할 것)
- [addAttr min/max raises](addattr-min-max-raises-not-clamps.md) — 범위 밖 setAttr 은 클램프 아닌 에러
- [xform silent on locked](xform-silent-on-locked-channels.md) — 잠긴 채널은 조용히 건너뛴다 → 되읽어 확인
- [getAttr settable lies](getattr-settable-lies-for-constrained.md) — 컨스트레인트 구동도 True, 연결+lock 으로 판정
- [Maya loadPlugin no __file__](maya-loadplugin-no-file.md) — loadPlugin .py 에 `__file__` 없음
- animLayer — [copy/cut traps](animlayer-copy-cut-traps.md)(`cutKey` 는 `animLayer` 를 안 받는다) · [no global selected query](animlayer-no-global-selected-query.md)(`ls(type=animLayer)` 순회)
- [node purity signals](node-purity-signals.md) — listHistory 는 짧은 이름, 깨끗한 메시에도 initialShadingGroup
- [shading: per-face assignment](shading-per-face-assignment.md) — `listConnections(shadingEngine)` 는 면별 배정을 잃는다, `getConnectedShaders` · 면 하나 `sets -remove` 는 안 비워짐 · 빈 면은 `listSets` 로 판정
- [utility nodes inherit shadingDependNode](utility-nodes-inherit-shadingdependnode.md) — multiplyDivide/vectorProduct/plusMinusAverage, 셰이딩 판정은 `getClassification`
- [Referenced node name compares](referenced-node-name-comparisons.md) — 솔버까지 네임스페이스, 타입으로 판정
- [Set rename traps](maya-set-rename-traps.md) — `select(set)` 은 멤버를 펼침, 짧은 이름 rename 은 NS 를 벗김
- [ikHandle creation traps](ikhandle-creation-traps.md) — SC 에도 poleVector, ikSpringSolver 는 MEL 로
- [name matching: token index](attr-name-matching-token-index.md) — 편집 거리 말고 토큰 역색인+IDF
- [hold mesh while moving joints](skincluster-hold-mesh-while-moving-joints.md) — `bindPreMatrix*matrix` 상수 유지
- [parentMatrix includes own OPM](parentmatrix-includes-offsetparentmatrix.md) — OPM 을 구동할 땐 `obj.parentInverseMatrix` 금지(자기 OPM 을 되먹음), 부모 `worldInverseMatrix` 직결
- [surface normal handedness](surface-normal-handedness.md) — normal = tanU×tanV, matrix pinning 의 [tanU, N, tanV] 는 왼손계 → Z = tanU×N 로 직교화
- [constraint target plugs & offset spaces](constraint-target-plugs-and-offset-spaces.md) — 노드 단위 열거, offsetT/R 공간이 다름
- [sculpt target: pnts redirect](sculpt-target-pnts-redirect.md) — 타겟 Edit 중 `setAttr pnts` 는 타겟으로 새며 에러, 아이템 `inputPointsTarget` 에 직접 더한다
- [shape.pnts is post-deformation](shape-pnts-is-post-deformation.md) — pnts 는 디포머 뒤에 더해진다
- blendShape — [delta space = origin](blendshape-delta-space-origin.md) · [target name vs alias](blendshape-target-name-vs-alias.md)(노드 이름 ≠ 웨이트 alias, 인덱스는 max+1) · [live target deltas](blendshape-live-target-inputpointstarget.md)(라이브 타겟은 메시를 옮겨야 함)
- keys — [setKeyframe insert needs a curve](setkeyframe-insert-needs-existing-curve.md)(없으면 조용히 no-op) · [pasteKey attribute = order match](pastekey-attribute-matches-by-order.md)(plug 단위로) · [animated attr: key + setAttr](animated-attr-setkeyframe-plus-setattr.md)
- [parent -s -add = instance](parent-shape-add-is-instance.md) — 소스 계층 삭제 시 붙인 쉐입도 사라짐, duplicate + `parent -r -s` + 월드 CV 복원
- [cmds.toggle not undoable](maya-toggle-cmd-not-undoable.md) — `toggle -localAxis` 대신 setAttr
- [extendToShape picks wrong shape](extendtoshape-picks-wrong-shape.md) — 금지, 공용 `maya_shape` 사용
- [pointPosition: points only](pointposition-points-only.md) — 엣지/페이스는 xform 평균
- [cmds -pivot is world](cmds-scale-rotate-pivot-is-world.md) — `scale`/`rotate` 의 `-pivot` 은 `-objectSpace` 여도 월드
- [skin weights: physical index](skincluster-weight-index-physical.md) — get/setWeights 는 물리 인덱스
- [skinCluster deforms user normals](skincluster-deforms-user-normals.md) — `deformUserNormals` 가 잠긴 노멀을 돌린다 · **노멀 쓰기는 MFnMesh + dgdirty**(컴포넌트 명령은 메모리·레퍼런스 편집 폭발), undo 는 스냅샷 명령으로
- [MPlug.asMObject lifetime](mplug-asmobject-lifetime.md) — MObject 를 붙들고 읽어야, 놓으면 쓰레기 값
- [MFn cvPositions lifetime](mfn-cvpositions-lifetime.md) — API 가 준 `MPoint` 를 들고 나오면 값이 되돌아간다, 읽는 즉시 tuple 로
- [referenced curve CV write](referenced-curve-cv-write.md) — 레퍼런스 커브 CV 는 `xform` 으로만(`curve -replace` 는 저장 안 됨 · `setAttr controlPoints` 는 델타) · 주기 커브 `cv[i]` 는 spans 까지
- [setAttr Int32Array no count](setattr-int32array-no-count.md) — Int32Array 는 개수를 붙이지 않는다
- [attr reorder = deleteAttr + undo](maya-attr-reorder-deleteattr-undo.md) — 재정렬 명령이 없다, 성공했을 때만 undo, Ctrl+Z 로 안 돌아감
- [list_attrs multi detection](list-attrs-multi-detection.md) — `attributeQuery(multi=True)`
- [UUID-safe rename](uuid-safe-rename-duplicate-names.md) — 동명 노드 대비 UUID 보관
- [standalone app package collision](standalone-app-package-collision.md) — `tools.<tool>.app.*` 로 import
- icons — [New tool needs icon](new-tool-needs-icon.md)(svg+png 32px) · [Standalone taskbar icon](standalone-taskbar-icon-method.md)(다중크기 .ico + AppUserModelID)
- [Pin for maya.cmds tools](pin-for-maya-cmds-tools.md) — maya_ui_widget() + WindowStaysOnTopHint
- [shelf childArray has separators](shelf-childarray-has-separators.md) — 구분선에 `shelfButton` 질의는 RuntimeError, 드롭 설치가 죽는다 (구분선 없는 셸프에선 재현 안 됨)

## 공용 위젯 · 프레임워크

- [zero-arg super after reload](reload-stale-instance-super.md) — Framework 클래스는 `super()` 만, `super(Class, self)` 는 reload 뒤 옛 인스턴스에서 TypeError
- [control shapes](framework-control-shapes.md) — 컨트롤러 커브 셰이프 34종 공용 json(좌표 반올림 금지)

- TSL — [UUID selection](wip-tsl-uuid-selection.md)((uuid, component) 보관) · [attach_uuids](framework-tsl-attach-uuids.md)(씬 노드 아닌 리스트는 False) · [list_limit summary](framework-tsl-list-limit.md)(500+ 요약) · [max-height squeezes buttons](tsl-widget-max-height-squeezes-buttons.md)(`list_widget` 에만) · [selection order](tsl-selection-order.md)(`trackSelectionOrder` 꺼지면 `ls(os)` 도 인덱스 순) · [select_no_expand](wip-a00440-find-tab.md)(세트를 담은 리스트는 켤 것 — 안 켜면 행 클릭이 멤버를 고른다)
- [Menu bar + common items](framework-menubar-widget.md) — 공통 메뉴 항목은 `tool_menu.COMMON_MENUS` 한 줄(42 PySide + 7 cmds 툴), PySide2 `action.menu()` 가 QMenu 를 지운다
- [Sub-tabs over collapsibles](prefer-subtabs-over-stacked-collapsibles.md) — 섹션 3~4개 넘으면 중첩 탭
- [checkList behavior](framework-checklist-behavior.md) — 체크박스 QListWidget 다중 선택+다중 체크는 `JUN_mod_checkList_qt_v01(lw)` 한 줄 (eventFilter 직접 짜지 말 것)
- Framework 위젯 — [log](framework-log-widget.md)(Expand/Shrink/Clear/Copy, **47툴 전부 교체 완료** · 내부는 QTextEdit · Shrink 는 창 높이까지) · [expand](framework-expand-widget.md)(복제 말고 이동) · [filter](framework-filter-widget.md)(v2 트리 모드 · 여러 열 `tree_columns`) · [mirror tokens](framework-mirror-tokens.md)(공용 json, 경계 매칭) · [falloff curve](framework-falloff-curve-widget.md) · [progress popup](framework-progress-widget.md)(마지막 값 스로틀 금지) · [timeRange](framework-timerange-widget.md)
- Qt 함정 — [exclusive radio: setChecked(False) 무시](qt-exclusive-radio-uncheck-ignored.md) · [QTreeWidgetItem checkable default](qtreewidgetitem-checkable-default-flag.md) · [clicked passes checked bool](qt-clicked-passes-checked-bool.md) · [QDoubleSpinBox keyboardTracking](qdoublespinbox-keyboard-tracking.md)

## 툴 작업

- A00010 — [HIK Mirror](wip-a00010-hik-mirror.md)(이름 1순위·위치 폴백, v02.01)
- A00040 — [Joints only export](wip-a00040-joints-only-export.md)(FBX 옵션으로 non-joint 제외, v02.06) · 새 파일 기능은 A00480 으로
- A00480 — [FileTool](wip-a00480-filetool.md)(A00040_V02 + quickTool File/Import 를 Export/Import/Path 탭으로, 원본 보존, 창 크기 = A00040_V02 960x853, v01.02 · Export 규칙 레지스트리 + Check Hide Mesh(메시 자신만, 조상 안 봄), 걸리면 파일 0개 · 걸린 메시 선택, v01.05)
- A00050 — [uvTool V02](wip-a00050-uvtool-v02.md)(V01 PySide 이식 · 규칙 위반을 사유와 함께 로그+선택 · rename 은 before->after 와 실패 사유, v02.00 · 바꿀 세트 이름을 화면에서 입력, 칸 하나가 Catch 의 규칙도 정한다, v02.01)
- A00060 — [Aim Root mode](wip-a00060-aim-root-mode.md)(Chain/Root, 분기는 첫 자식 · X 조준은 자식이 X 축 위일 때만 위치 보존 → 움직인 자식 원위치, v03.11) · [V03 tab reorg](wip-a00060-v03-tab-reorg.md) · [IK Edit](wip-a00060-ik-edit.md)(폴 벡터 역산) · [Pole Target](wip-a00060-pole-target.md)(pointConstraint 하나, Slide, v03.08) · [world-space joint pos](wip-a00060-world-space-joint-pos.md)
- A00090 — [PoseWrangler bundle](wip-a00090-posewrangler-bundle.md)(`<driver>_default`, v01.07) · [rule versions](wip-a00090-rule-versions.md)
- A00110 — [Mirror Key: Scale](wip-a00110-mirror-scale.md)(미러 없이 값 그대로, v02.16) · [Follow: component target](wip-a00110-follow-component-target.md) · [Layer key copy](wip-a00110-layer-key-copy.md)(v02.13) · [Copy Key custom attrs](wip-a00110-copykey-custom-attrs.md) · [Copy Key 1->n](wip-a00110-copykey-one-to-many.md) · [V02 tab taxonomy](wip-a00110-tab-taxonomy.md) · [Fill Keys](wip-a00110-fill-keys.md) · [Stagger Offset](wip-a00110-stagger-offset.md) · [Graph Focus](wip-a00110-graph-focus.md) · [Get Sel Range](wip-a00110-get-sel-range.md) · [Euler Filter range](wip-a00110-euler-filter-range.md)
- A00120 — [FKIK constraint-free bake](wip-a00120-fkik-bake-constraintfree.md)(프레임별 matchTransform)
- A00130 V02 — [Match](wip-a00130-v02-match.md)(NS 양쪽 탐색 · 부모부터 맞추고 밀려난 것은 재매칭, v02.20 · Check Position 초록/빨강, v02.21 · 행 더블클릭 set 선택, v02.23) · [Length](wip-a00130-length-values.md) · [IK session](wip-a00130-ik-session.md)(snapEnable 이 undo 를 깬다) · [Orient & Place](wip-a00130-orient.md)(쇄골 aim_at, v02.24 · **오른팔은 규칙 없이 늦은 Behavior 미러 하나** — A2 의 `+Z` 는 미러된 폴 타깃을 보므로 미러가 아니었다 · 표는 한 조인트 한 행, v02.27) · [Pair & Constrain](wip-a00130-pair-constrain.md)(parentConstraint 가 조용히 타깃을 늘린다, v02.17) · [IK axis](wip-a00130-ik-axis.md)(`twist` 로만)
- A00145 — [Mirror network offsets](wip-a00145-mirror-network-offsets.md)(박힌 maintain offset 을 미러 기준으로 다시 풀기, v01.42) · [Mirror tab](wip-a00145-mirror-tab.md)(Reflect=`M·S`, Apply Source->Target + Keep Children in Place, v01.41) · [object name match](wip-a00145-object-name-match.md) · [Update offset](wip-a00145-update-offset.md)(타깃은 전부) · [component followers](wip-a00145-component-followers.md) · [Match 1<-n](wip-a00145-match-one-to-many.md) · [(Null) match rows](wip-a00145-match-null-placeholder.md) · [Match Cache](wip-a00145-match-cache.md) · [Match Keep Children](wip-a00145-match-keep-children.md)(팔로워만 옮기고 자식은 월드 자리에, Mirror 와 공용 keep_children.py, 기본 OFF, v01.53)
- A00145 (계속) — [Connect both directions](wip-a00145-connect-both-directions.md) · [Match from Source](wip-a00145-attr-name-matching.md) · [Target Edit](wip-a00145-target-edit.md) · [Target Replace](wip-a00145-target-replace.md) · [Attribute Edit tab](a00145-attribute-tab-blendshape-alias.md) · [skin constraint types](wip-a00145-skin-constraint-types.md) · [multi constraint types](wip-a00145-multi-constraint-types.md)(체크박스, 채널 안 겹치는 조합 · 반대 순서는 pairBlend, v01.47) · [Constraint Transfer](wip-a00145-constraint-transfer.md) · [Group Create](wip-a00145-group-create.md) · [Match DOOTOOL options](wip-a00145-match-dootool-options.md) · [Set Value](wip-a00145-set-value.md)(Number Tool 이식, enum 은 이름으로, v01.51) · [채널박스 표시](attr-channelbox-and-references.md)(만든 어트리뷰트는 늘 보이게, Keyable 은 키 여부만, Edit 에 Show in Channel Box, v01.52)
- A00170 — [AttachCrv tab](wip-a00170-attachcrv-tab.md)(Maintain offset = OPM 구동 · NURBS surface 지원, v01.23) · [Edge Loop drivers](wip-a00170-edge-loop-drivers.md) · [Lip Seal](wip-a00170-lip-seal.md)(rest 포즈를 머리 공간에, v01.21) · [Stretch tab](wip-a00170-stretch-tab.md) · [Remap List Attributes](wip-a00170-remap-listattrs.md)
- A00210 — [PathStructure tree](wip-a00210-pathstructure-tree-depth.md) · [Recreate To + Rename](wip-a00210-recreate-to-rename.md) · [PathStructure files](wip-a00210-pathstructure-files.md)(v01.29)
- A00220 — [Pin toggle](wip-a00220-pin.md) · [dino save pulse](wip-a00220-dino-save-pulse.md) · [Shrink](wip-a00220-shrink.md)(공룡만 남기고 788→155px, 숨길 그룹 속 위젯은 옮겨서 살린다, v01.15)
- A00240 — [Shrink + tree anim](wip-a00240-shrink-anim.md)(350x155 = A00220 줄었을 때와 같게, 파일 트리 5행 · 굵은 선 · 1.5초 무한 반복, v01.13)
- A00270 — [Classic tab](wip-a00270-classic-tab.md)
- A00275 — [Select By Weight](wip-a00275-select-by-weight.md)(범위는 Load 때 저장, QListWidget 체크박스 클릭은 eventFilter, v01.27) · [Layer tab](wip-a00275-layer-tab.md)(N 메시 lock+Blend 합성, setWeights 는 undo 안 됨, v01.22) · [tab reorg](wip-a00275-tab-reorg.md)(탭 인덱스 판단 주의) · [Copy Weights](wip-a00275-copy-weights.md)(v01.18) · [Edit Mesh](wip-a00275-edit-mesh.md) · [Expand Bind](wip-a00275-expand-bind.md) · [Move Joints](wip-a00275-move-joints.md) · [Bind Pose](wip-a00275-skintool-bindpose.md) · [Transfer tab](wip-a00275-transfer-tab.md)
- A00280 — [cloth-corrective](metahuman-cloth-corrective-A00280.md)(알렘빅 → RBF 코렉티브)
- A00290 **V02** — [tab reorg](wip-a00290-v02-tab-reorg.md)(Shape/Target/Node 3x7 · Default→Extract · 1400x1158, v02.00 · Target > Delete(탭은 2단까지만), 삭제는 MEL `blendShapeDeleteTargetGroup` 이라 undo 안전, v02.03) — **아래 V01 메모의 탭 경로는 V01 기준**
- A00290 — [Naming tab](wip-a00290-naming-tab.md)(FBX 엔 별칭뿐, v01.22) · [Target Order](wip-a00290-target-order-tab.md) · [Bake Delete](wip-a00290-bake-delete-tab.md) · [Mix Targets](wip-a00290-mix-targets-tab.md) · [Shape Editor](wip-a00290-shape-editor-tab.md)(`sculptTarget` 필수)
- A00300 — **A00380 의 MeshDoctor 탭으로 이식됨**([[wip-a00380-meshdoctor-tab]], 2026-09-22 · 원본은 보존) · [batch summary](wip-a00300-batch-summary-table.md) · [zero-area rework](wip-a00300-zero-area-quality-rework.md)
- A00310 — [Type/Token/Rules](wip-a00310-searchtool-rules.md)(공유 Objects 리스트 · 규칙 레지스트리 · Standalone/No Upstream/No Downstream, v01.04) · A00330 — [Set Rename](wip-a00330-set-rename.md) · [Token tab](wip-a00330-token-tab.md)(Rename 하위 탭, 칸 수 자유 Custom/Numbering + Profile, 마야는 `01_a` 를 `_a` 로, 칸 폭 80px, v01.08)
- A00340 — [SelectionTool](wip-a00340-selectiontool.md) · [button colors](wip-a00340-button-colors.md) · [split layout](wip-a00340-split-layout.md)
- A00350 — [ArrayCreator](wip-a00350-arraycreator.md) · A00360 — [SortTool](wip-a00360-sorttool.md) · A00370 — [ToolLauncher](wip-a00370-toollauncher.md)
- A00380 — [MeshTool Peak](wip-a00380-meshtool-peak.md) · [Match tab](wip-a00380-match-tab.md)(v01.10 좌 Source / 우 Targets, 1<=n · n<=n, 리스트 바뀌면 미리보기 세션 폐기 · Sort 버튼으로 짝 맞추기, v01.13) · [Match > By Weight](wip-a00380-match-by-weight.md)(스킨 웨이트 마스크, joint k -> mesh k, v01.09 · 타겟 Edit 중이면 델타에 직접, v01.12) · [MeshDoctor tab](wip-a00380-meshdoctor-tab.md)(A00300 통째 이식 · 첫 번째 탭 · 새 아이콘, v01.14)
- A00390 — [WindTool](wip-a00390-windtool.md) · [Chain Wave](wip-a00390-chain-wave.md) · [V02 axis & driver](wip-a00390-v02-axis-driver.md) · [V02 Envelope](wip-a00390-v02-envelope.md) · [Lite debug curve](wip-a00390-lite-debug-curve.md)(v02.03)
- A00400 — [CurveTool](wip-a00400-curvetool.md) · [Smooth](wip-a00400-smooth-tab.md)(닫힌 커브 우회, v01.09) · [Points to Curve](wip-a00400-points-to-curve.md) · [Wrap](wip-a00400-curve-wrap.md) · [Joints](wip-a00400-curve-joints.md)(v01.14 NURBS 서피스 U/V 한 줄) · [Controls](wip-a00400-controls-tab.md)(bs_controls 이식, v01.15) · Combine(v01.11, 쉐입 복사 합치기 — [instance trap](parent-shape-add-is-instance.md)) · [Shape Edit](wip-a00400-shape-transform.md)(옛 Transform · **Line Width 탭 흡수 + 개명, v01.21** — 셰이프 CV 를 피벗 기준 scale/move/rotate + 선 굵기, 트랜스폼 채널 불변, v01.18 · 값 9개 전부 슬라이더 + 범위 밖 값이면 슬라이더 범위를 넓힌다, v01.19 · 라이브 세션 = CV 원위치에서 매번 재계산 + 드래그 한 번에 undo 한 번, v01.20)
- A00410 — [SecondaryMotion](wip-a00410-secondarymotion.md)(FK 관성 굽기, v01.08) · A00420 — [Wrapper](wip-a00420-wrapper.md) · A00430 — [DemBone](wip-a00430-dembone.md)
- A00440 — [SetTool](wip-a00440-settool.md)(v01.01) · [Find tab](wip-a00440-find-tab.md)(속한 세트 역조회 · `listSets` 는 트랜스폼/셰이프/컴포넌트가 다르고 중복을 준다 · 공용 TSL `select_no_expand`, v01.04) · A00450 — [ManipulatorTool](wip-a00450-manipulatortool.md) · A00460 — [FK & IK](wip-a00460-fk-ik.md)(Skip End Joints = FK 체인 끝 n 개 생략, v01.07)
- A00470 — [MaterialTool](wip-a00470-materialtool.md)(머티리얼 이름 규칙 진단 · 토큰 정렬 DP · 고칠 이름 제안, v01.03) · Copy Material(소스 UUID 기억 → 면별 머티리얼 복사 + 되읽어 확인, v01.05) · **Rename to Suggested**(자리표시 `{character}` 남으면 건너뜀 · 기본 노드는 `ls -defaultNodes` 로 · 리포트는 (글,종류) 목록 하나로 색 HTML + 클립보드, v01.07) · 기본 프로파일은 목록 순서 아닌 `DEFAULT_PROFILE` = Set_v001 (v01.09)
