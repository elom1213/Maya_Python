---
title: A00620_NameDecoder 사용법
aliases: [Name Decoder, NameDecoder, A00620, FBXASC]
tags: [maya-python, tool-guide, fbx, fbxasc, unicode, blendshape, naming]
updated: 2026-11-09
---

# A00620_NameDecoder 사용법

마야 FBX 임포터가 `FBXASC227FBXASC129FBXASC130` 처럼 바꿔 놓은 이름(일본어 · 중국어 · 띄어쓰기 · 맨 앞 숫자)을
**원래 글자로 풀어 보여 주는** in-Maya PySide 툴(arch B). 기본 동작은 **읽기만** 하고 씬을 바꾸지 않는다.

- **버전**: `app/config/version.py` (v01.01)
- **설치**: `__dragDrop_A00620.py` 를 Maya 뷰포트로 드래그&드롭 → 셸프 버튼 **Decode** → `tools.A00620_NameDecoder.run(True)`
  (ToolLauncher `UTIL` 프로파일 `Scene` 칸에도 있다)
- **계획서**: [`plans/A00620_NameDecoder_plan.md`](plans/A00620_NameDecoder_plan.md) (실측 근거 §2)
- **공용 코드**: `Framework/core/fbx_name.py` (인코딩 · 디코딩, 마야 불필요) · `Framework/core/maya_fbx_names.py` (씬 스캔)

## 1. FBXASC 가 무엇인가

마야 이름에는 `[A-Za-z0-9_]` 만 쓸 수 있고 숫자로 시작할 수 없다. FBX 임포터는 그 밖의 글자를
**UTF-8 바이트 하나마다** `FBXASC` + 10진수 3자리로 바꾼다.

| 원래 | 마야 이름 |
|------|-----------|
| `あ` (UTF-8 `E3 81 82`) | `FBXASC227FBXASC129FBXASC130` |
| `Left ankle` | `LeftFBXASC032ankle` |
| `1_003` | `FBXASC049_003` (맨 앞 숫자만) |
| `a-b` · `a.b` | `aFBXASC045b` · `aFBXASC046b` |

### 마야 한계 (2026-11-09 실측)

- `rename` · `aliasAttr` 는 일본어를 **거부**하고, OpenMaya `setName` 은 **에러 없이 무시**한다(띄어쓰기는 `_` 로 바꿈).
  → 아웃라이너 · 채널 박스 · Shape Editor 의 글자는 바꿀 수 없다. **이 툴 창에서 풀어 본다.**
- **FBXASC 이름은 FBX 로 내보내면 원래 글자로 돌아간다**(`Model::あ`, 블렌드셰이프 채널 `い`). 손실 없는 형식이다.
  **FBX 로 다시 나갈 파일이면 이름을 그대로 두는 것이 안전하다.**

## 2. Names 탭

| 항목 | 설명 |
|------|------|
| `Scope` | `Scene` 전부 / `Selected` 고른 노드 + 셰이프 + 거기 걸린 blendShape / `Selected + Hierarchy` 아래 전부 |
| `Encoded only` | 켬(기본) = FBXASC 가 든 이름만, 끔 = 범위 안 모든 이름(FBXASC 없는 것은 회색) |
| `Attributes` | 사용자 어트리뷰트 이름 · enum 필드 이름도 찾는다 |
| `Scan` | 표를 채운다: `Decoded` · `Raw (Maya name)` · `Type` · `Owner` |
| Filter | **풀린 글자로 검색**(`まば` → `まばたき`). Raw · Type · Owner 로도 맞는다 |
| 행 클릭 | 마야에서 그 노드 선택(블렌드셰이프 타겟 = blendShape 노드) |
| `Sync with Selection` | 마야에서 고른 노드의 행을 표에서 고른다 |
| 우클릭 | `Copy Decoded` · `Copy Raw` · `Copy Both (tab)` · `Select in Maya` |
| `Export List...` | 보이는 행을 `.csv`(UTF-8 BOM, 엑셀에서 안 깨짐) 또는 `.json` |
| `Export Map Template...` | 이름 안의 풀린 조각(`まばたき`, `口`, ` ` …)을 `{"조각": ""}` json 으로 - 번역표 출발점 |

- 깨진 FBXASC(UTF-8 이 아닌 바이트)는 추측하지 않고 raw 그대로 **노란 글자**로 둔다.
- Ctrl + 휠 또는 `- 100% +` 로 표 확대.

## 3. Blend Shapes 탭

Shape Editor 가 FBXASC 로만 보여 주는 타겟을 **풀린 이름 + 웨이트 슬라이더**로 본다.

- `blendShape` 콤보 / `From Selection`(고른 메시의 blendShape) / `Refresh`.
- 슬라이더 0~1, 숫자 칸 -10~10. **setAttr 만 한다 - 키는 찍지 않는다.** 슬라이더 한 번 끌기 = undo 한 번.
- 게이지는 **채운 길이 = 웨이트**(0~1). 줄마다 배경이 번갈아 칠해지고, 웨이트가 0 이 아닌 타겟 이름은 밝게 · 굵게 (v01.01, A00290 Shape Editor 슬라이더 방식).
- 연결이 들어온 웨이트 · 잠긴 웨이트는 회색(툴팁에 연결 소스).
- `Reset All` = 바꿀 수 있는 웨이트 전부 0 (undo 한 번).

## 4. Rename to ASCII 탭 (선택 기능)

**`View > Rename to ASCII Tab` 으로 켠다**(기본 숨김). 사내 이름 규칙 때문에 ASCII 이름이 꼭 필요할 때만.

1. Names 탭에서 `Scan`.
2. `Fill from Names` → 번역표에 조각이 채워진다. `ASCII` 칸을 채운다(또는 `Load Map...`).
   - 조각마다 **가장 긴 키부터** 바꾼다: `{"口": "mouth", "左": "L"}` → `口左Shape` = `mouthLShape`.
   - `{" ": "_"}` 로 띄어쓰기도 바꾼다. 빈 칸은 아직 번역 안 한 것으로 본다.
   - 자동 번역 · 로마자 변환은 하지 않는다.
3. `Preview` → `Decoded` · `New name` · `Status`.

   | Status | 뜻 |
   |--------|----|
   | `Ready` | 바꿀 수 있다 |
   | `Not mapped: 'あ'` | 번역표에 없는 글자가 남았다 |
   | `Invalid name` | 숫자로 시작하는 등 마야 이름이 될 수 없다 |
   | `Broken FBXASC` | 깨진 바이트 |
   | `Referenced` · `Locked` | 레퍼런스 · 잠긴 노드 |
   | `Name in use` | blendShape 에 같은 이름의 어트리뷰트가 있다 |
   | `Not supported` | 어트리뷰트 이름 · enum 필드(1 차 범위 밖) |

4. `Apply ASCII Names` → 경고 확인 → `Ready` 만 바꾼다. **Ctrl+Z 한 번**에 되돌아간다.
5. `Restore Original Names` → 이 툴이 바꾼 이름을 원래 FBXASC 이름으로 되돌린다.

원래 이름은 씬의 network 노드 **`A00620_originalNames`**(어트리뷰트 `a00620Originals`, json) 하나에 UUID 기준으로 기억한다.
노드마다 어트리뷰트를 붙이지 않는 이유: 조인트 · 메시의 사용자 어트리뷰트는 FBX 사용자 속성으로 따라 나간다.
Restore 가 전부 성공하면 이 노드는 지워진다.

## 5. 구조

```
tools/A00620_NameDecoder/
├─ __init__.py · launch.py · __dragDrop_A00620.py · icon/A00620_NameDecoder.svg(+png)
├─ app/config/version.py
├─ app/core/name_table.py      # Export List / Map Template
├─ app/core/bs_weights.py      # Blend Shapes 탭
├─ app/core/ascii_rename.py    # 번역 · Preview · Apply · Restore
├─ app/ui/main_window.py
└─ tests/test_name_decoder.py  # mayapy 오프스크린, 예시 씬이 있으면 그것도
```

## 6. 시험

```
"C:\Program Files\Autodesk\Maya2024\bin\mayapy.exe" tools/A00620_NameDecoder/tests/test_name_decoder.py
```

61 개 - 실제 이름 디코드 · **마야 FBX 임포터 실측 표와 인코더 일치** · 왕복 · 깨진 바이트 · 스캔 범위 · 내보내기 ·
웨이트 · Rename/undo/Restore · UI(오프스크린) · 예시 씬 `0010_Miyabi_base_02.mb`(노드 149 · 타겟 52, 열기만).

마야 GUI 확인 아직 - 특히 마야 Qt 창에서 일본어 · 중국어 글꼴이 □ 로 깨지지 않는지.
