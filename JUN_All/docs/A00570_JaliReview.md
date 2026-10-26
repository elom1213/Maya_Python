# A00570_JaliReview

`A00560_JaliBatch` 가 만든 **JALI 클립 `.mb`** 를 마야 안에서 **레퍼런스로 검수**하는 in-Maya PySide 툴.
검수 씬 = 빈 씬 + **아바타 레퍼런스** + **클립 레퍼런스(네임스페이스 `CLIP`, 고정)**. 클립 안의 `CLIP:JALI:ARKIT_OUT`(ARKit 52) 을
아바타 블렌드셰이프에 잇고, 다음 대사는 **클립 레퍼런스만 교체**해서 본다. 어색한 키는 레퍼런스 애니메이션 커브 편집으로 고치고
**Save Clip Edits** 로 클립 파일에 쓴다.

- **버전**: v01.00 (2026-10-26)
- **아키텍처**: (B) in-Maya PySide, 드래그&드롭 셸프 설치 (`__dragDrop_A00570.py` → `JaliReview` 버튼)
- **짝**: `A00560_JaliBatch`(클립 생성 · Validate) · `A00540_JaliLipSync`(클립 하나를 리그에 바로 키)
- **공용**: `Framework/jali/clip_manifest.py`(클립 목록 · 재생 범위) · 계획 [plans/A00560_JaliBatch_plan.md](plans/A00560_JaliBatch_plan.md) §5

---

## 1. 흐름

```
┌ JALI Review v01.00 ─────────────────────────────────────────────────────┐
│ Clips  [D:\...\out_en_002\maya            ][...][Reload]                  │
│   Clip                           │ Frames  │ Status                       │
│ ▶ 0030_vivian_en_01_f0105_0429   │ 1-325   │ edited                       │
│   0030_vivian_en_02_f0445_0490   │ 1-46    │ generated                    │
│   [Build Review Scene] [< Prev] [Next >] [Swap]                           │
│   Current: 0030_vivian_en_01_f0105_0429.mb  (CLIPRN, loaded)             │
│ Edits (referenced animation curves)                                      │
│   [x] Allow edits on referenced animation curves (Maya preference)       │
│   Edits: 1        JALI_CTL_PH_AAA_ty: 1 key change(s), 0 removal(s)       │
│   [Save Clip Edits] [Discard Edits] [Refresh]                             │
│ Avatar [D:\...\avatar.mb              ][...][Reference]                   │
│   BlendShape [CHN_n_Face_xx_bs ▾] [Refresh]   Rules [            ][...]  │
│   [Connect ARKIT_OUT -> BlendShape] [Disconnect]   51 connected          │
│ [Open Clip...] [Save Clip & Close]                                        │
│ Log                                                                       │
└──────────────────────────────────────────────────────────────────────────┘
```

1. **Clips** — A00560 출력 폴더(`jali_clips.manifest.json`). 표의 `Frames` · `Status` 는 매니페스트에서(레퍼런스된 클립의 fileInfo 는
   검수 씬에서 안 보인다). 매니페스트가 없으면 `.mb` 목록만(재생 범위는 못 맞춘다).
2. **Avatar** 경로를 적고 **Build Review Scene** — 새 씬 → 클립 fps 로 단위 설정 → 아바타 레퍼런스 → 선택한 클립을 `CLIP` 으로 레퍼런스
   → 재생 범위(매니페스트 start-end) · 클립의 사운드 노드(`CLIP:jali_lipsync_audio`)를 타임슬라이더에.
3. **Connect ARKIT_OUT -> BlendShape** — 별칭 이름이 같은 타겟만 잇는다. 이미 다른 것이 구동하는 타겟은 skip, 아바타에 없는 타겟
   (예: `tongueOut`)은 목록으로 보고. 이름이 다른 아바타는 `Rules` json(`{"map": {"jawOpen": "jaw_open"}}`). 연결은 **아바타 레퍼런스의
   편집**으로 남으므로 클립을 교체해도 살아 있고, 검수 씬을 저장하면 다음에도 그대로. Undo 한 번.
4. **키 고치기** — `Allow edits on referenced animation curves` 를 켜고(마야 환경설정 `animDisplay -refAnimCurvesEditable`, 꺼져 있으면
   키 편집이 **조용히 무시**된다) 그래프 에디터에서 `CLIP:JALI_CTL_PH_*_ty` 커브를 고친다. `Edits:` 가 검수 씬에서 한 편집 수다.
5. **Save Clip Edits** — `file -saveReference` 로 클립 `.mb` 에 쓴다. 매니페스트 상태가 `edited` 로 바뀐다(A00560 의 `Keep edited clips` 가
   이 클립을 지킨다). **Discard Edits** 는 편집을 버린다(unload → remove edits → load, 클립 파일은 그대로).
6. **Prev / Next / Swap** — 클립 레퍼런스를 다른 `.mb` 로 교체(`file -loadReference`). **편집이 남아 있으면 Save & Swap / Discard & Swap /
   Cancel 을 묻는다** — 아래 "알아 둘 것" 의 이유로 미저장 편집을 들고 교체하지 않는다.
7. **Open Clip...** — 커브를 크게 갈아엎을 때: 클립 `.mb` 를 직접 열고 아바타를 **임시** 레퍼런스(`REVIEW_AVATAR`)로 붙인다.
   **Save Clip & Close** 가 임시 레퍼런스를 뗀 뒤 저장하고 새 씬으로 돌아간다(매니페스트 `edited`).

## 2. 알아 둘 것 (mayapy 2024 실측, 2026-10-26)

- **"고치면 그대로 저장된다" 가 아니다.** 레퍼런스된 커브의 키 편집은 검수 씬의 **레퍼런스 편집**(`relationship "fcurve" ... add/cut`)으로
  `CLIPRN` 에 쌓이고 클립 `.mb` 는 Ctrl+S 로 바뀌지 않는다. 클립에 쓰는 길은 **Save Clip Edits**(`saveReference`) 하나다.
- **★ 미저장 편집을 들고 교체 · 재열기 하면 안 된다.** 마야가 fcurve 편집을 다시 적용할 때 시각을 **24 fps 기준으로 환산**한다 —
  30 fps 씬에서 프레임 10 의 편집이 12.5 에, 5000 이 6250 에 붙는다(마야 버그). 그 상태로 저장하면 엉뚱한 프레임에 키가 생긴다.
  바로 저장하면 정확히 써진다(재열기 확인). 그래서 Swap 은 편집 0 일 때만 바로 실행한다. 검수 씬 자체를 **편집을 남긴 채 저장했다가
  다시 열지 말 것**(같은 이유). 검수 씬은 저장하지 않아도 된다 — 아바타 · 연결만 있는 껍데기다.
- 편집 수는 `referenceQuery -editStrings -onReferenceNode CLIPRN` 으로 센다. 그냥 `-editStrings` 는 클립 파일 자체의 중첩 편집(컨트롤러에
  커브를 붙인 23건)까지 보여 준다.
- Discard 는 **언로드한 뒤** `referenceEdit -removeEdits` — 로드 상태에서는 지워지지 않는다. 연결(아바타 쪽 편집)은 그대로다.
- 컨트롤러 원본을 고칠 때 노드 이름이 바뀌면 클립 N 개의 결선이 조용히 실패한다 — `A00560` Validate 탭으로 한 번에 확인.
- 검수 씬 fps 는 클립 fps(매니페스트)로 맞춘다. 다른 fps 의 클립을 섞어 보면 Swap 이 단위를 바꾸고 로그에 적는다.

## 3. 구조 (개발자용)

```
A00570_JaliReview/
├── __init__.py · launch.py (run(reload_module)) · __dragDrop_A00570.py
├── app/config/version.py
├── app/core/
│   ├── review_scene.py   find_clip_ref · reference_avatar · reference_clip · swap_clip(편집 0 요구) · pending_edits(onReferenceNode)
│   │                     · classify_edits · describe_edit · save_clip_edits(saveReference) · discard_edits(unload/removeEdits/load)
│   │                     · anim_curve_edits_enabled/set · apply_range · attach_clip_sound · set_scene_fps · open_clip · temp avatar · save_open_clip · arkit_out_node
│   ├── arkit_connect.py  blendshape_targets · source_attrs · load_rules · plan · connect(undo 한 번) · connected_count · disconnect
│   └── prefs.py          optionVar JUN_A00570_*
├── app/ui/main_window.py
├── icon/A00570_JaliReview.svg / .png
└── tests/test_review.py(33) · test_ui.py(24)  - mayapy 2024, A00560 워커로 클립 2개를 만들고 합성 아바타(blendShape 51 타겟)로 왕복
```

**확인 기록 (2026-10-26, mayapy 2024)**: build → connect 51/52(tongueOut missing) → 편집 OFF 무시 · ON 기록 → 편집 있는 Swap 차단 → Save → 클립 재열기 값
0.9 · 키 추가 확인 · 중첩 레퍼런스 무사 · 아바타 편집 미유출 → Swap 성공 · 연결 유지 → Discard → Open Clip · Save & Close(임시 아바타 제거) · UI 24.
**마야 GUI 에서 직접 본 것은 아직** — 셸프 드롭 설치, 타임슬라이더 소리 재생(레퍼런스된 사운드 노드), 그래프 에디터 편집 흐름은 사용자 확인 대상.
