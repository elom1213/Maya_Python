---
name: wip-a00620-namedecoder
description: A00620_NameDecoder - FBXASC 이름(일본어·중국어·띄어쓰기)을 원래 글자로 보여 주는 툴, 마야는 유니코드 이름 불가 · FBX 익스포터는 FBXASC 를 원래 글자로 복원
metadata:
  type: project
---

2026-11-09 v01.00. 마야 FBX 임포터의 `FBXASC###`(UTF-8 바이트 10진수) 이름을 풀어 보여 주는 in-Maya PySide 툴.
공용 코드: `Framework/core/fbx_name.py`(encode/decode, 마야 불필요) · `Framework/core/maya_fbx_names.py`(씬 스캔).

실측 사실 (mayapy 2024):
- 마야는 노드 이름에 유니코드를 못 쓴다 - `rename` · `aliasAttr` 는 에러, **OpenMaya `MFnDependencyNode.setName` 은 에러 없이 무시**(띄어쓰기는 `_`). 플러그인으로도 불가 → 아웃라이너 · Shape Editor 글자는 못 바꾼다.
- **FBX 익스포터는 FBXASC 를 원래 글자로 되돌려 쓴다**(`Model::あ`) → FBXASC 이름은 손실 없는 왕복 형식. ASCII 로 바꾸면 원래 이름이 사라진다(그래서 Rename 탭은 View 메뉴로 켜는 선택 기능 + Restore).
- 임포터는 **맨 앞 숫자도** 인코딩(`1abc` → `FBXASC049abc`, `9` → `FBXASC057`). 옛 `fbx_binary.maya_node_name` 은 이걸 빠뜨렸다 → 공용 encode 로 교체.
- blendShape 웨이트는 동적 어트리뷰트가 아니라 nice name 도 못 붙인다. 문자열 어트리뷰트 값에는 유니코드 저장 OK.
- 원래 이름 저장은 network 노드 하나(`a00620Originals` json, UUID 키) - 노드별 사용자 어트리뷰트는 FBX 사용자 속성으로 따라 나가서 피했다.

**Why:** 사용자가 MMD(PMX) 계열 모델(Miyabi)의 모프 `まばたき` · `あ` 를 Shape Editor 에서 못 읽어서 요청.
번호는 원래 A00610 이었으나 다른 세션 `A00610_PmxImporter` 와 충돌(드롭 파일 이름 같음) → A00620.
PmxImporter 에도 같은 규칙의 `encode_name/decode_name` 이 따로 있다 - 공용 `fbx_name` 으로 합치는 건 그쪽 작업 끝난 뒤 요청 시.

사용처: A00290_BSTool_V02 v02.06 Shape Editor `Names: Decoded(기본) / Raw (FBXASC)` - 표시만, 필터는 두 이름 다 (2026-11-09).
A00620 v01.01 Blend Shapes 게이지는 A00290 WeightSlider 방식(테마가 QSlider 를 안 꾸밈 → 슬라이더 전용 qss), 0~1 이라 채움 = 웨이트.

**How to apply:** FBXASC 관련 작업은 `fbx_name` 을 쓴다(새로 짜지 말 것). 마야 GUI 확인 아직 - 마야 Qt 창의 일본어 · 중국어 글꼴(□ 로 깨지면 Yu Gothic / Microsoft YaHei 폴백).
관련: [[mayapy-headless-verify]] · [[wip-a00480-filetool]] · [[maya-fbx-import-nonxyz-flip]]
