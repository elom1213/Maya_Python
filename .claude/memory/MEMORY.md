# Memory Index

한 줄 = 한 메모(같은 툴은 한 줄에 묶음). 상세 · 버전 이력은 각 파일에 — 여기엔 훅만.

> 저장소 규칙은 루트 `CLAUDE.md`, 세션 공통 규칙(한국어 · 푸시 · 커밋 · 라우팅)은 전역 `JUN_Claude/CLAUDE.md`.
> 학습 노트 메모는 `JUN_Study/.claude/memory/`, UE 메모는 `JUN_UE/.claude/memory/` (2026-08-24 이동).

## ⏰ 날짜 알림 (해당 날짜가 지났으면 첫 답 맨 앞에서 먼저 말할 것)

- (현재 없음)

## 작업 방식 · 사용자 선호

- [진행 상황 문장도 한국어](feedback-korean-progress-notes.md) — 도구 사이 중간 설명 · 짧은 답까지 한국어(세 번 지적: 11-03, 11-04 두 번 — 사용자 중간 메…
- [Push target Dnable/dev](push-target-dnable-dev.md) — push 대상은 Dnable_repo 의 dev
- [Push: 나가는 커밋을 따로 보고 push](push-check-outgoing-separately.md) — `git log ..HEAD` 와 `git push` 를 한 줄로 묶지 말 것(11-05 다른 세션 A006…
- [No history rewrite / master on request](no-history-rewrite-master-on-request.md) — 재작성 금지, master 최신화는 그 턴 요청 시만
- [Push includes tool guide docs](push-includes-tool-guide-docs.md) — 툴 push 에 docs 가이드 · version · WORKLOG 함께
- [Push refreshes README date](push-refresh-readme-date.md) — 푸시 때 루트 README 의 `최근 갱신` 날짜 진단 · 최신화해 함께 담기
- [WORKLOG maintenance](worklog-maintenance.md) — 최신이 위, 날짜 헤딩 중복 금지, 월 롤링
- [Docs go in JUN_All/docs](docs-go-in-jun-all-docs.md) — 툴 안내 = docs/, 계획 = docs/plans/, 학습 = JUN_Study
- [A00500_reloader](wip-a00500-reloader.md) — v01.01 재노출 옛 클래스 재리로드(첫 클릭 AttributeError) · dev 리로더는 `dev/A…
- [A00520 icon_builder · A00530 dependency_check](wip-a00500-reloader.md) — dev 툴 4개 전부 같은 모양(launch.run · __dragDrop · icon · docs), 옛…
- [A00510_release_builder](wip-release-builder-qt.md) — 릴리즈 복사 개발툴(dev/, v01.03 A 번호 + __dragDrop_A00510, **v01.04 마…
- [Release layout & launch.py](release-layout-launch-py.md) — 릴리즈본은 Framework 동봉 · config/dev 없음, launch.py 가 두 배치 구분. **툴…
- [Release install scripts](release-install-scripts.md) — userSetup 이름 고정, git 출력 UTF-8 vs 콘솔 cp949
- [Update portfolio on tool work](update-portfolio-on-tool-work.md) — portfolio EN/KR 동기, 커밋 통계 건드리지 않기
- [Launcher buttons follow current version](launcher-buttons-follow-current-version.md) — 새 버전 폴더면 A00370 버튼도 옮길 것
- [Sliders use shared style](feedback-sliders-use-shared-style.md) — 새 QSlider 는 `JUN_mod_sliderStyle_qt_v01(self)` 한 줄(테마 qss 에…
- [C:\JUN 정션 구조](project-c-jun-junction-layout.md) — PC 간 같은 논리 경로로 레퍼런스, 정션 경유 파일 아직 적음 → 이름 확정 적기, 확정 뒤엔 경로 불변
- [Prefer PySide for new tools](prefer-pyside-for-new-tools.md) — 신규 툴은 PySide(arch B)
- [No filename-dependent data](no-filename-dependent-data.md) — 파일 이름 규칙(예: `_f0105_0429`)에서 값을 읽어 데이터를 만들지 말 것, 이름은 출력 이름에만
- [JUN_Memo repo](jun-memo-repo.md) — 스티커 메모 독립 PySide6 앱, `D:\D__3010_JUN_Memo`, 푸시 = origin main
- [JUN_JALI repo](jun-jali-repo.md) — VisemeNet 포크, 푸시는 origin main, `.venv` 추론 · angela_JALI 리그 적…
- [kangaroo plugin read-only](kangaroo-plugin-external-readonly.md) · [PoseWrangler fork patch](posewrangler-plugin-fork-patch.md)

## 검증 · 창 크기

- [Bash heredoc collapses backslashes](bash-heredoc-backslash-collapse.md) — `python - <<'EOF'` 안 백슬래시 두 개가 하나로 줄어듦(문자열에 진짜 줄바꿈), 백슬래시 들어간 패치는 Write 로 스크립트 파일
- [mayapy headless verify](mayapy-headless-verify.md) — maya.cmds 동작은 mayapy + standalone 으로 실측
- [offscreen size needs theme](offscreen-size-needs-theme.md) — 테마 입히고 재라, 오프스크린 px > 마야 px (잰 값을 박지 말 것)
- [tabFit: 탭마다 창 높이 자동](framework-tabfit-widget.md) — `JUN_mod_tabFit_qt_v01(window, tabs)` 한 줄, **★ PySide6 enum…
- [QTabWidget min size = all pages](qtabwidget-min-size-hidden-pages.md) — 숨은 페이지까지 최소의 최댓값 → 창이 못 줄어듦, 탭을 QScrollArea 에 + fit_to_conte…
- [window taller than screen](window-taller-than-screen-ghost.md) — 화면 밖 잘림 = "로그창 2개", 탭 스크롤 + 작업 영역 높이
- [QApplication before standalone](qapplication-before-maya-standalone.md) · [standalone app package collision](standalone-app-package-collision.md)
- icons — [New tool needs icon](new-tool-needs-icon.md) · [Standalone taskbar icon](standalone-taskbar-icon-method.md) · [Pin for maya.cmds tools](pin-for-maya-cmds-tools.md)
- [shelf childArray has separators](shelf-childarray-has-separators.md) — 구분선에 `shelfButton` 질의는 RuntimeError

## 마야 공통 함정

- [maya reference import traps](maya-reference-import-traps.md) — `loadReferenceDepth none` 저장은 언로드로 굳음 · 언로드는 import 불가 · 부모…
- [reference fcurve edit traps](maya-reference-fcurve-edit-traps.md) — 레퍼런스 커브 편집은 `saveReference` 로만 파일에, **미저장 편집은 재로드 때 24fps 기준…
- [Kangaroo headless golden test](kangaroo-headless-golden-test.md) — Kangaroo 원본을 mayapy 에서 돌려 이식 결과를 숫자로 대조(kt_cmdUndo 로드 + repo…
- [Maya FBX import flips non-XYZ joints](maya-fbx-import-nonxyz-flip.md) — 임포터가 XYZ 동치 공식으로 연속화 → 비 XYZ 조인트(Hips 등) 자세가 틀림, 쿼터니언 3모드 다,…
- [FBX export selected scope](fbx-export-selected-scope.md) · [Maya 2023 compat](maya-2023-compat.md) · [Maya loadPlugin no __file__](maya-loadplugin-no-file.md) · [loaded plugin stays stale](maya-loaded-plugin-stays-stale.md)
- [undo_chunk by default](undo-chunk-by-default.md) · [cmds.toggle not undoable](maya-toggle-cmd-not-undoable.md) · [attr reorder = deleteAttr + undo](maya-attr-reorder-deleteattr-undo.md) · [cmds.surface not undoable](maya-surface-cmd-not-undoable.md)
- attrs — [channel box & references](attr-channelbox-and-references.md) · [lock: parent compound overrides child unlock](maya-attr-lock-parent-compound.md) · [addAttr min/max raises](addattr-min-max-raises-not-clamps.md) · [xform silent on locked](xform-silent-on-locked-channels.md) · [getAttr settable lies](getattr-settable-lies-for-constrained.md) · [list_attrs multi detection](list-attrs-multi-detection.md) · [setAttr Int32Array no count](setattr-int32array-no-count.md)
- connections — [compound connect leaves child connections](compound-connect-leaves-child-connections.md) · [isDestination true for child of connected compound](connectioninfo-isdestination-compound-child.md) · [constraint target plugs & offset spaces](constraint-target-plugs-and-offset-spaces.md) · [parentMatrix includes own OPM](parentmatrix-includes-offsetparentmatrix.md)
- animLayer — [copy/cut traps](animlayer-copy-cut-traps.md) · [no global selected query](animlayer-no-global-selected-query.md) · [`keyframe -q -name` = 활성 레이어 커브만, GE 레이어 필터는 `outlinerEditor -animLayerFilterOptions`](wip-a00110-graph-focus.md) · [merge = bakeResults -rwl · children[0] 이 맨 아래 · override 멤버는 키 없이도 덮음 · scaleAccumulationMode Additive(0):Multiply(1) · dest Base 는 소스 커브 삭제](wip-a00110-layer-range-merge.md)
- keys — [keyframe over squeezes on collision](keyframe-over-squeezes-on-collision.md) · [setKeyframe insert needs a curve](setkeyframe-insert-needs-existing-curve.md) · [pasteKey attribute = order match](pastekey-attribute-matches-by-order.md) · [animated attr: key + setAttr](animated-attr-setkeyframe-plus-setattr.md)
- shading — [per-face assignment](shading-per-face-assignment.md) · [utility nodes inherit shadingDependNode](utility-nodes-inherit-shadingdependnode.md) · [node purity signals](node-purity-signals.md)
- names — [connectAttr ambiguous short name is silent](connectattr-ambiguous-short-name-silent.md) · [Referenced node name compares](referenced-node-name-comparisons.md) · [Set rename traps](maya-set-rename-traps.md) · [UUID-safe rename](uuid-safe-rename-duplicate-names.md) · [name matching: token index](attr-name-matching-token-index.md)
- rig — [ikHandle creation traps](ikhandle-creation-traps.md) · [hold mesh while moving joints](skincluster-hold-mesh-while-moving-joints.md) · [surface normal handedness](surface-normal-handedness.md)
- skin — [weights: physical index](skincluster-weight-index-physical.md) · [deforms user normals](skincluster-deforms-user-normals.md)
- blendShape — [geo-less blendShape dies on connected delete](maya-delete-cascades-geoless-blendshape.md) · [delta space = origin](blendshape-delta-space-origin.md) · [target name vs alias](blendshape-target-name-vs-alias.md) · [live target deltas](blendshape-live-target-inputpointstarget.md) · [sculpt target: pnts redirect](sculpt-target-pnts-redirect.md) · [shape.pnts is post-deformation](shape-pnts-is-post-deformation.md)
- shapes/curves — [parent -s -add = instance](parent-shape-add-is-instance.md) · [extendToShape picks wrong shape](extendtoshape-picks-wrong-shape.md) · [pointPosition: points only](pointposition-points-only.md) · [cmds -pivot is world](cmds-scale-rotate-pivot-is-world.md) · [referenced curve CV write](referenced-curve-cv-write.md)
- [Reference parent → click selects shape](maya-reference-parent-selects-shape.md) — 틀이 Reference 면 컨트롤 트랜스폼에도 override normal 을 줄 것
- [cp949 non-ASCII traps](maya-codepage-nonascii-traps.md) — cp949 밖 글자 경로는 텍스처 못 읽음 · .ma 문자열 `?` · getVertexNormal 은 잠긴…
- [time-context traps](maya-time-context-traps.md) — **스크립트 `currentTime` = 호출마다 undo 하나(스크럽은 MAnimControl)** · `…
- [VP2 x-ray · hotkey filter](maya-vp2-xray-and-hotkey-filter.md) — x-ray 는 점만, **3D 선은 전부 가려짐 → 화면 2D 로 투영** · 컨텍스트 중 `b` 등 핫키는…
- [viewport Tab is MTK](maya-viewport-tab-is-mtk.md) — 뷰포트 Tab 은 hotkey 무시, `nexOpt mayaTabPressCmd` 를 바꿔 끼울 것 (GUI…
- [Euler closestSolution not equivalent](euler-closest-solution-not-equivalent.md) — 짐벌 근처 다른 회전, closestCut + alternate 로 · 오일러는 축별로 안 더해진다
- API lifetime — [MPlug.asMObject](mplug-asmobject-lifetime.md) · [MFn cvPositions](mfn-cvpositions-lifetime.md)

## 공용 위젯 · 프레임워크

- [zero-arg super after reload](reload-stale-instance-super.md) — Framework 클래스는 `super()` 만
- [token name widget](framework-token-name-widget.md) — Profile + 칸, A00330 · A00480 공유, 칸 편집은 `Save` 버튼으로만 저장
- [control shapes](framework-control-shapes.md) · [mirror tokens](framework-mirror-tokens.md)
- [TSL name_display](framework-tsl-name-display.md) — 같은 이름 `A|dup` 을 `dup` 으로 그리기만(글자 불변, 델리게이트), 툴팁 = 경로, 기본 Out…
- TSL — [(Null) is red](framework-tsl-null-placeholder-red.md) · [UUID selection](wip-tsl-uuid-selection.md) · [attach_uuids](framework-tsl-attach-uuids.md) · [list_limit summary](framework-tsl-list-limit.md) · [max-height squeezes buttons](tsl-widget-max-height-squeezes-buttons.md) · [selection order](tsl-selection-order.md) · [select_no_expand](wip-a00440-find-tab.md)
- [pin_style: Pinned = 연한 빨강](framework-pin-style.md) — 체크형 Pin 버튼은 `apply_pin_style` 한 줄, `:checked` 색만(padding 금지)…
- [shell_integration: Add to Start Menu](framework-shell-integration.md) — standalone 툴 시작 메뉴 .lnk + AUMID (PowerShell C#), Win10/11, A…
- [Menu bar + common items](framework-menubar-widget.md) · [Dev Mode menu widget](framework-devmode-widget.md) · [Sub-tabs over collapsibles](prefer-subtabs-over-stacked-collapsibles.md)
- [viewZoom: 리스트 · 트리 확대 / 축소](framework-viewzoom-widget.md) — `JUN_mod_viewZoom_qt_v01(view, key, default)` 한 줄(A00110 Lay…
- [TSL Rules: 규칙대로 리스트업](framework-list-rules.md) — `show_rules=True`, 세트 멤버 · 네임스페이스 무관 · **순서 = dagSetMembers…
- [checkList behavior](framework-checklist-behavior.md) — QListWidget 다중 체크는 `JUN_mod_checkList_qt_v01(lw)` 한 줄. 트리 판은…
- [treeExpand: 트리 펼치기](framework-treeexpand-widget.md) — 모든 트리에 `JUN_mod_treeExpand_qt_v01(tree)` 한 줄(화살표 = 한 단계, Shi…
- widgets — [log level colors](framework-log-level-colors.md) · [log](framework-log-widget.md) · [expand](framework-expand-widget.md) · [filter](framework-filter-widget.md) · [falloff curve](framework-falloff-curve-widget.md) · [progress popup](framework-progress-widget.md) · [timeRange](framework-timerange-widget.md)
- Qt 함정 — [exclusive radio uncheck ignored](qt-exclusive-radio-uncheck-ignored.md) · [QTreeWidgetItem checkable default](qtreewidgetitem-checkable-default-flag.md) · [clicked passes checked bool](qt-clicked-passes-checked-bool.md) · [QDoubleSpinBox keyboardTracking](qdoublespinbox-keyboard-tracking.md)

## 툴 작업

툴마다 대표 메모 하나 — **전체 목록 · 요약은 [index-tools](index-tools.md)** (툴 작업 전에 그 툴 줄을 볼 것).

- A00010 — [HIK Mirror](wip-a00010-hik-mirror.md)
- A00040 — [Joints only export](wip-a00040-joints-only-export.md)
- A00050 — [uvTool V02](wip-a00050-uvtool-v02.md)
- A00060 — [From Object Match Rotation](wip-a00060-from-object-match-rotation.md) 외 6
- A00060 · A00130 — [IK Edit keep PV offset](wip-ik-edit-keep-pv-offset.md)
- A00090 — [PoseWrangler bundle](wip-a00090-posewrangler-bundle.md) 외 1
- A00110 — [Bake range keeps outside keys v02.51](wip-a00110-bake-range-layers.md) 외 17
- A00120 — [FKIK Auto + Dev Mode](wip-a00120-fkik-auto-devmode.md) 외 1
- A00130 V02 — [Match](wip-a00130-v02-match.md) 외 5
- A00145 — [Mirror network offsets](wip-a00145-mirror-network-offsets.md) 외 9
- A00145 (계속) — [Connect both directions](wip-a00145-connect-both-directions.md) 외 14
- A00170 — [AttachCrv tab](wip-a00170-attachcrv-tab.md) 외 5
- A00210 — [데이터 폴더 구조 계획](wip-a00210-data-folders.md) 외 7
- A00220 — [Save Cache 계획](wip-a00220-save-cache.md) 외 4
- A00240 — [Drag reorder + free resize + elide](wip-a00240-drag-reorder.md) 외 4
- A00270 — [Classic tab](wip-a00270-classic-tab.md) 외 1
- A00275 — [Transfer 1:1 pairs](wip-a00275-transfer-pairs.md) 외 12
- A00290 — V02 — [tab reorg](wip-a00290-v02-tab-reorg.md) 외 5
- A00300 — A00380 MeshDoctor 탭으로 이식됨(원본 보존) · — [batch summary](wip-a00300-batch-summary-table.md) 외 1
- A00310 — [Type/Token/Rules](wip-a00310-searchtool-rules.md) 외 3
- A00340 — [SelectionTool](wip-a00340-selectiontool.md) 외 2
- A00350 — [ArrayCreator](wip-a00350-arraycreator.md) 외 3
- A00380 — [MeshTool Peak](wip-a00380-meshtool-peak.md) 외 5
- A00390 — [WindTool](wip-a00390-windtool.md) 외 5
- A00400 — [CurveTool](wip-a00400-curvetool.md) 외 8
- A00410 — [SecondaryMotion](wip-a00410-secondarymotion.md) 외 2
- A00440 — [SetTool](wip-a00440-settool.md) 외 4
- A00470 — [MaterialTool](wip-a00470-materialtool.md)
- A00480 — [FileTool](wip-a00480-filetool.md)
- A00490 — [KeyboardTool](wip-a00490-keyboardtool.md)
- A00540 — [JaliLipSync](wip-a00540-jalilipsync.md)
- A00560 · A00570 — [JaliBatch · JaliReview](wip-a00560-jalibatch.md)
- STT Converter — [wav → 대본 변환기 계획](wip-stt-converter.md)
- A00550 — [PoseMapper](wip-a00550-posemapper.md)
- A00600 — [SceneCleanup](wip-a00600-scenecleanup.md)
- A00590 — [SwingTwistNative v01.01](wip-a00590-swingtwist-native.md)
- A00580 — [FacialBoardBuilder · Ctl_Only_V05](wip-facial-arkit52-ctl-v05.md)
- JALI 슬라이더 리그 — [A0020_jali_slider_ctl](wip-jali-slider-ctl.md)
- A00620 — [NameDecoder](wip-a00620-namedecoder.md)
- A00610 — [PmxImporter](wip-a00610-pmximporter.md)
- A00630 — [MotionPathEditor v01.15](wip-a00630-motion-path.md)
- A00640 — [AttrSlider](wip-a00640-attrslider.md)
