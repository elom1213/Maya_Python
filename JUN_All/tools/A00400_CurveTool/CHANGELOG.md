# Changelog — A00400_CurveTool

## v01.24 (2026-09-22)
**[Change] `Create > Controls` 의 `Thickness` 칸 삭제 — 선 굵기는 `Display > Shape Edit` 하나로.**

- **왜**: 같은 일(`nurbsCurve.lineWidth`)을 두 탭이 했다. v01.21 에 옛 `Line Width` 탭이
  `Display > Shape Edit` 안으로 들어가면서, 목록에 담은 커브의 굵기를 언제든 바꿀 수 있게 됐다.
  만들 때 한 번 정하는 칸은 더 필요하지 않다.
- **[Remove]** `controls_tab.py` 의 `Thickness` 스핀박스와 `control_manager.create_controls()` /
  `_make_curve()` 의 `thickness` 인자. 새 컨트롤의 `lineWidth` 는 **아예 건드리지 않는다**
  (마야 기본값 `-1` = 전역 설정을 따름). 굵기를 바꾸려면 `Display > Shape Edit` 의
  `Line Width` 를 쓴다.
- **형상은 그대로** — `Framework.core.control_shapes.build()` 의 `thickness` 인자는 남아 있고
  (다른 툴도 쓰는 공용 함수) 이 툴이 넘기지 않을 뿐이다. 셰이프 34종의 CV 는 바뀌지 않는다.
- 탭 안내문에 굵기가 어디 있는지 적었다.

## v01.23 (2026-09-22)
**[Feature] `Display > Replace` — **Resolve Pair from Selection** 버튼.**

- **무엇을 하나**: 교체본(`Replacement`)마다 **반대쪽 이름**을 만들어, 그 이름의 커브가 씬에 있으면
  왼쪽 `Shapes to replace` 에 짝지어 채운다. 리그 한쪽을 만들어 두고 반대쪽에 같은 모양을 입힐 때
  대상을 손으로 고르는 일이 없어진다. `A00110_animTool_V02` 의 `Resolve Pairs from Selection` 과 같은 규칙.
- **대상**: 씬 선택이 있으면 그것, 없으면 이미 담겨 있는 `Replacement` 리스트.
- **[Add] 토큰 규칙은 Framework 공용 파일 하나** (`Framework/rules/mirror_tokens.json`,
  `MirrorTokenStore`). 단순 substring 치환이 아니라 **경계 매칭**이라 `sample_lip_l_ctl` 의 `_lip` 을
  잘못 집지 않는다.
- **★ 양쪽 리스트를 짝지어진 것만으로 함께 다시 채운다** — 짝은 **리스트 순서**로 맺어지므로
  왼쪽만 채우면 짝을 못 찾은 교체본 때문에 순서가 밀려 **엉뚱한 셰이프가 적용**된다.
- **건너뛰는 것은 사유와 함께 로그에** — 좌/우 토큰이 없는 이름(센터), 반대쪽이 씬에 없는 경우,
  같은 이름의 노드가 **커브가 아닌** 경우(조인트 등), 자기 자신으로 미러되는 경우.
  같은 이름의 커브가 여럿이면 첫 번째를 쓰고 그 사실을 적는다.

## v01.22 (2026-09-22)
**[Feature] `Display > Replace` — 대상이 **레퍼런스**면 셰이프를 바꾸는 대신 **CV 를 맞춘다**.**

- **문제**: `Shapes to replace` 에 올린 커브가 레퍼런스로 들어온 것이면 셰이프 노드를 **지울 수 없다.**
  기존 경로는 "기존 셰이프 삭제 → 새 셰이프 붙이기" 라서
  `Cannot delete ... as it has locked or read-only children` 로 막히고 교체가 되지 않았다.
- **[Add] CV 매칭 경로 (`control_manager.match_cv_positions`)** — 셰이프 노드는 그대로 두고
  **`crv_to_replace.cv[i]` 를 `crv_replacement.cv[i]` 로 옮긴다.** 두 커브의 모양이 원래 같고
  CV 개수가 같으면(= 미러 쌍) 의도한 모양이 된다.
  - **Mirror Shapes 켬** — 대응 CV 의 **월드** 위치를 X 만 뒤집어(`-x, y, z`) 대상의 오브젝트 공간으로
    가져온다. 즉 교체본을 **월드 기준 scaleX = -1** 한 모양이다(셰이프 교체 경로의 mirror 와 같은 결과).
  - **Mirror Shapes 끔** — 대응 CV 의 **오브젝트** 위치를 그대로 가져온다
    (셰이프 교체 경로의 non-mirror = `matchTransform` 후 freeze 와 같은 결과).
- **[Add] 대상마다 자동으로 갈린다** — 레퍼런스면 CV 매칭, 아니면 기존 셰이프 교체. 화면에 켤 것은 없고
  **어느 쪽으로 처리했는지 로그에 적는다.** 레퍼런스와 로컬이 섞인 리스트도 한 번에 돌아간다.
- **[Add] 안 되는 경우는 사유와 함께 건너뛴다** — 셰이프 개수가 다르거나 CV 개수가 다르면
  **아무 것도 쓰지 않고**(반쪽만 옮겨 어긋나지 않게) 사유를 로그에 남긴다.
- 쓰기는 `Shape Edit` 탭과 같은 `shape_xform_manager.write_cv_points`(`cmds.curve -replace`) 를
  공유한다(`_write_points` 를 공개 이름으로). **undo 한 스텝**이고 닫힌(주기) 커브의 매듭도 보존한다.

## v01.17 (2026-09-18)
**[Feature] `Create > Controls` 색에 **팔레트 팝업**(임의 RGB) 추가.**

- **요청**: `ref/ref_01.mel` 을 참고해 정해진 색이 아니라 **팔레트에서 고른 색**을 쓸 수 있게, 팔레트는 **별도 팝업**으로.
- **[Add] `Color Palette...` 버튼 + 마지막 색 견본** — 견본을 누르면 그 색을 다시 입힌다. 취소하면 아무것도 안 바뀐다.
- **[Add] `control_manager.set_color_rgb(rgb)`** — ref 와 같은 어트리뷰트(`overrideRGBColors` 1 + `overrideColorRGB`), 값은 0~1 로 클램프.
- **[Fix] 인덱스 색도 `overrideRGBColors` 를 0 으로 되돌린다** — 스위치가 RGB 에 남아 있으면 인덱스를 바꿔도 화면 색이 안 바뀐다.
  `Reset Color` 도 스위치와 RGB 값을 함께 되돌린다.
- 팔레트는 마야 `colorEditor` 대신 **Qt 팔레트** — PySide 창이라 팝업도 같은 계열이어야 부모·테마가 맞물린다.

**검증**(mayapy 2024 + 오프스크린 Qt, **16항목 통과**): RGB 적용·클램프·선택 유지 · 인덱스↔RGB 스위치 왕복 ·
reset · template/reference 해제 · 선택 없음 · 잘못된 값 거절 · UI(버튼·견본·색 적용·재적용·취소·창 폭).

## v01.16 (2026-09-18)
**[Change] 셰이프 교체를 `Create > Controls` 에서 떼어 **`Display > Replace`** 하위 탭으로. 두 칸을 **TSL** 로, 개수가 다르면 **적은 쪽만큼** 1:1.**

- **요청**: Control 탭의 Shape Replace 를 잘라내 Display 하위 탭 `Replace` 로 이식, 두 칸을 TSL 로,
  두 리스트 개수가 같으면 1:1 · 다르면 **더 작은 개수만큼** 동작.
- **[Add] `app/ui/replace_tab.py`** — `Shapes to replace` / `Replacement` TSL 두 개 + `Mirror Shapes` + `Replace Shapes`.
  TSL 이라 Add / Del / Up / Down 으로 목록과 순서를 손볼 수 있고, UUID 로 이름이 바뀌어도 대상을 놓치지 않는다.
- **[Change] `replace_shapes` 의 짝 규칙** — 교체본이 하나면 전부, 여럿이면 순서대로 1:1,
  개수가 다르면 `min(개수)` 쌍만 하고 몇 쌍을 했는지 로그에 적는다(v01.15 까지는 거절).
- **[Change] `Display` 카테고리 설명** — "그려지는 방식만 바꾼다(형상 불변)" → "어떻게 보이는지(굵기 · 컨트롤의 셰이프)".
  Replace 는 셰이프 노드를 바꾸므로 성격은 Edit 에 가깝지만, 쓰는 사람은 "어떤 모양으로 보이게 할까" 로 찾는다.

**검증**(mayapy 2024 + 오프스크린 Qt, **13항목 통과**): 같은 개수 1:1 · 대상이 많을 때 · 교체본이 많을 때 ·
교체본 1개 · 탭 구성(Display 2개, Controls 에서 제거됨) · TSL 리스트업 · UI 실행 · 빈 리스트 경고 · 창 폭.

## v01.15 (2026-09-18)
**[Feature] `Create > Controls` — `bs_controls`(Brandon Schaal) 이식 : 컨트롤러 커브 34종 생성 + 색 + 셰이프 교체.**

- **요청**: 마야 셸프에서 `bs_controlsUI.BSControlsUI().bsControlsUI()` 로 쓰던 툴을 A00400 의 새 탭으로 이식.
  이어서 **셰이프 CV 데이터는 특정 툴이 아니라 공용으로** 관리.
- **[Add] `Framework/rules/control_shapes.json` + `Framework.core.control_shapes`** — 셰이프 34종(Circle 은 `cmds.circle`,
  나머지 33종은 degree 1 커브 하나, Gear 만 셰이프 2개). `mirror_tokens` 와 같은 자리·같은 규칙.
  좌표는 **원본 값 그대로** — 6자리로 반올림했더니 8개 셰이프가 원본과 `1e-5` 어긋났다.
- **[Add] `app/core/control_manager.py`** — 만들기(Parent/Child/World/Origin) · 색(31색 + T/R + Reset) · 셰이프 교체(1→N, N→N, Mirror).
- **[Add] `app/ui/controls_tab.py`** — 원본 창의 세 섹션을 순서 그대로.
- 원본과 달라진 것: `cmds.error` 대신 로그 경고 · 버튼 한 번 = undo 한 스텝 · 색 바꿔도 **선택 유지** ·
  `parentConstraint` 대신 `matchTransform` · 셰이프 없는 노드에서 죽던 `Reset Color` 수정.

**검증**(mayapy 2024 + 오프스크린 Qt, **33항목 통과**): 34종 전부 원본과 **CV 단위 일치**, 이름 규칙,
4가지 배치 모드의 계층·위치, undo, 색/T/R/Reset, 셰이프 교체 6가지, UI 스모크.

## v01.14 (2026-09-17)
**[Feature] `Edit > Joints` — NURBS surface 도 원하는 개수만큼 조인트 + 바인드 + zro/con/ctl/tgt 스택.**

- **요청**: Joints 탭에서 커브뿐 아니라 NURBS surface 도 같은 구조를 만들고, U / V 중 어느 방향으로 조인트를 나열할지 고를 수 있게.
- **[Add] `Surface Direction` U / V** — U 면 V 를 고정한 줄을 따라, V 면 U 를 고정한 줄을 따라 놓는다. 커브는 무시.
- **[Add] `Across` 0~1 (기본 0.5)** — 그 줄이 반대 방향 파라미터 범위의 어디에 있는지. 0.5 = 가운데 줄.
- 리스트에 **커브와 서피스를 섞어** 담아도 된다. Count / Spacing / 닫힘 / 바인드 / 스택 / 컨스트레인트는 커브와 같다.
  - **By length** = 줄을 스팬당 32점으로 찍은 꺾은선 길이로 역보간(아이소파름 길이 MFn 함수가 없다).
  - 그 방향으로 닫힌 서피스(`formU/formV`)는 마지막 자리를 뺀다(원통 둘레).
  - **Aim** — X = 줄 접선, **Y = 서피스 노멀 쪽**(`Z = X × N` 으로 직교화, 왼손계 회피).
  - 극점처럼 접선이 0 인 자리는 월드 방향으로 두고 경고.
  - 최상위 그룹 이름은 `<name>_srfJnt_grp`.
- **[Change] UI 문구** — 리스트 `Curves / Surfaces` · `List Selected`, `Count per Object`, 버튼 `Create Joints`, 로그 `... curve(s) and N surface(s)`.
- core API: `build_joints_on_curves(..., direction=, across=)` 추가, 결과 dict 에 `surfaces`. `sample_curve` 는 `(위치, 접선, None)` 3-튜플로.

**검증**(mayapy 2024 + 오프스크린 Qt, **22항목 전부 통과**): 서피스 위 · 등간격 · U/V 직교 · Aim X/Y · 컨트롤러로 서피스 변형 ·
Across 0/1 · 불균등 스팬 By length/parameter · 원통 닫힌 방향 · 구 극점 · 커브 회귀 · 혼합 리스트 · 잘못된 방향 · UI 생성 + 단일 undo · 창 폭.

## v01.13 (2026-09-17)
**[Change] `Edit > Combine` — 기본으로 Source 를 Target 월드 위치로 옮긴 모양이 합쳐진다.**

- **요청**: Combine Shapes 결과가 *Source 오브젝트를 Target 의 월드 위치로 이동한 뒤의 커브 모양* 이어야 한다.
  v01.11 은 Source 가 보이던 자리 그대로 붙어서, Target 에서 떨어진 곳에 쉐입이 생겼다.
- **[Add] `Placement` 라디오 3 개** (`Keep world position` 체크박스 대체)
  - **`Move to Target position`(기본)** — Source 의 월드 CV 에 `(Target rotate pivot − Source rotate pivot)` 을 더한다.
    Source 의 회전·스케일은 그대로.
  - `Keep Source world position` — v01.11 의 켬 동작.
  - `Keep local CV values` — v01.11 의 끔 동작(MEL `parent -s -add` 와 같음).
- **[Note] 피벗끼리 맞춘다** — mayapy 실측: `matchTransform -pos` 후 A 의 월드 rotate pivot == B 의 월드
  rotate pivot 이고, translate 값끼리는 다르다. 그래서 Maya Match Transformation > Position 과 같은 기준을 썼다.
- core API: `combine_shapes(..., keep_world=)` → `combine_shapes(..., placement=PLACE_TARGET | PLACE_WORLD | PLACE_LOCAL)`.

**검증**(mayapy 2024 + 오프스크린 Qt, **12항목 전부 통과**): 기본 결과 == Source 복제본에 `matchTransform -pos`
한 모양(회전 · 비균등 스케일 · 피벗이 옮겨진 Source, 회전·스케일된 Target) · Source 불변 · 인스턴스 아님 ·
단일 undo · World / Local 모드 · 잘못된 placement 거절 · 부모가 있는 Source/Target 에서 N→1 · UI 기본 라디오 · UI 실행.

## v01.11 (2026-09-17)
**[Feature] `Edit > Combine` — 좌측 Source 커브의 쉐입을 우측 Target 커브에 합친다.**

참고 MEL(`parent -s -add $shape $target`)의 문제를 없앴다.

- **[Note] `parent -s -add` 는 쉐입을 인스턴스로 붙인다** — 노드는 하나, 부모가 둘
  (mayapy 실측: `listRelatives(shape, allParents=True)` -> `['A', 'B']`). 그래서
  - `select -hi A; delete`(아웃라이너에서 계층째 지우기) · `delete |A|AShape` → **B 의 쉐입도 삭제**
  - `delete A` / `doDelete`(트랜스폼만) → B 에 남는다
  - 지우지 않아도 A 의 CV 를 움직이면 B 도 같이 움직인다.
- **[Add] 복제한 독립 쉐입을 옮겨 붙인다** — Source 를 `duplicate`(upstream 없음 → 히스토리 없는
  현재 모양) → 새 쉐입을 `parent -r -s` 로 Target 에 **이동** → 임시 트랜스폼 삭제.
  결과 쉐입 이름은 `<Target>Shape#`.
- **[Add] `Keep world position`(기본 켬)** — `parent -r -s` 는 로컬 CV 값을 그대로 가져가서 두
  트랜스폼이 다르면 모양이 튄다(MEL 원본도 같다). 켜면 CV 를 원래 월드 위치로 되돌린다. 끄면 MEL 과 같은 로컬 동작.
- **[Add] `Delete Source curves after combining`** — Target 이기도 하거나 밑에 Target 이 있는 Source 는 남긴다.
- 짝 짓기: Target 1 개면 모든 Source 를 거기에, 여러 개면 Source 와 **행 순서대로 1:1**(개수가 다르면 거절).
- intermediate 쉐입(스킨된 커브의 Orig 등)은 제외하고, 보이는 쉐입의 **현재(디폼된) 모양**을 복사한다.
- 전부 **한 번의 undo**.

**검증**(mayapy 2024 + 오프스크린 Qt, **22항목 전부 통과**): 인스턴스 아님 · 임시 트랜스폼 잔여 없음 ·
회전/비균등 스케일/닫힌 커브에서 월드 위치 유지 · Source CV 편집·**계층째 삭제에도 복사본 유지** ·
단일 undo · 로컬 모드 · 히스토리 Source(입력 없음, 이후 변경 무관) · 스킨된 Source(쉐입 1개, 디폼 위치) ·
멀티 쉐입 Source · N→1 · N:N · 개수 불일치 거절 · 커브 아닌 항목 건너뛰기 · 같은 커브 건너뛰기 ·
Source 삭제 옵션(+ 밑에 Target 이 있으면 보존, undo 복원) · UI(탭 위치 · 실행 · 지운 Source 리스트 정리).

## v01.09 (2026-09-09)
**`Edit > Smooth` — 닫힌 커브에 한 번 적용하면 그 뒤로 아무것도 안 되던 것 수정.**

- **[Fix] 임시 커브를 만들고 지우는 것이 사용자의 CV 선택을 지우고 있었다.** 닫힌 커브에
  Smooth 를 걸면 한 번은 되고(`Smooth 0.070 -> 1 curve(s), 12 of 12 CV(s) moved`),
  그 다음부터는 `Select some curve CVs first ...
  [RuntimeError: (kFailure): Object does not exist]` 만 떴다. 뒤의 예외는 **빈 선택에서
  `getRichSelection()` 이 던지는 것** — 즉 진짜 원인은 "선택이 사라졌다" 였다.
- **[Note] `cmds.curve` 는 만든 커브를 선택 상태로 만든다.** 닫힌 커브의 임시 사본만
  이 경로(감아 넣은 커브를 새로 만든다)를 쓰고, 열린 커브는 `cmds.duplicate`(선택을 안 건드린다)를
  써서 **닫힌 커브에서만** 증상이 났다. 이어서 `cmds.delete` 가 그 선택을 비운다.
- **[Change] 선택을 건드리는 구간을 공용 `keep_selection()` 컨텍스트로 묶었다** —
  임시 커브 생성 · 삭제 · `smoothCurve` 세 군데 전부. 선택을 지우는 마야 명령을 이 툴에서
  찾은 것이 이제 **셋**(`smoothCurve` v01.05, `curve` · `delete` v01.09)이라 한 군데서 관리한다.
- 검증(mayapy 2024): 닫힌 · 닫힌+히스토리 · 열린 커브 각각 — **연속 3회 적용** 후에도 선택 동일,
  드래그 세션 중/후 선택 동일, 임시 커브 잔여 없음, **그 다음 `capture()` 가 여전히 CV 를 찾는다**.

## v01.08 (2026-09-09)
**`Edit > Smooth` 가 닫힌(주기) 커브에도 듣는다 — 이음매를 넘어서 고르게.**

- **[Fix] 닫힌 커브가 통째로 걸러지던 것을 풀었다** — 지금까지 닫힌 커브의 CV 를 고르면
  `periodic curve - Maya's smoothCurve cannot handle it` 로 **통째로 건너뛰었다.**
  이제 열린 커브와 같은 슬라이더 · 같은 소프트 셀렉션 폴오프 · 같은 Rough 로 동작하고,
  **결과도 마야 기본 Smooth 와 같은 계산**이다.
- **[Add] 이음매(seam)를 넘어가는 스무딩** — 닫힌 커브에는 끝이 없으므로 **고정되는 CV 가
  하나도 없다.** `cv[0]` 과 마지막 CV 만 골라도 서로를 이웃으로 보고 고르게 밀린다.
  `Check Selection` 은 각 커브가 `open` 인지 `closed` 인지도 함께 적는다.
- **[Note] 마야 알고리즘을 그대로 쓴다** — 라플라시안 같은 대체 스무딩을 따로 지어 붙이면
  열린 커브와 닫힌 커브가 **다른 느낌**으로 갈라진다. 대신 닫힌 커브의 CV 목록을 앞뒤로
  **감아 복사해 늘린 열린 임시 커브**를 만들고, 거기에 마야의 `smoothCurve` 를 그대로 돌린 뒤
  **가운데 구간만** 읽어 돌아온다. 마야가 커브 끝을 고정하는 것은 패딩 구간에서만 일어나므로
  읽어 오는 구간은 전부 "안쪽" 이다. 결과는 마야의 내부 스텐실(degree 3 기준
  `[-1/18, 2/9, 2/3, 2/9, -1/18]`)을 **순환으로** 건 것과 소수점까지 같다(실측 오차 `8.9e-16`).
  패딩은 `2 * degree + 4` — degree 7 까지 이 값이면 패딩을 40 으로 키운 결과와 같다.
- **[Note] 닫힌 커브는 CV 가 두 가지로 세어진다** — `.cv[i]` 로 고를 수 있는 것은 `spans` 개인데
  `MFnNurbsCurve.cvPositions()` 는 `spans + degree` 개를 돌려준다(뒤의 `degree` 개는 앞의 복사본).
  쓸 때 **그 복사본까지 같이 갱신**해야 이음매가 벌어지지 않는다.
- **[Note] 주기 커브에는 `cmds.curve(replace=True)` 가 그냥은 안 통한다** —
  `Must specify knots with the -per option`. 원본의 `periodic` + `knot` 을 그대로 다시 넘겨야
  형태가 열린 커브로 바뀌지 않는다. `setAttr .controlPoints` 로 쓰는 길은 쓰지 않았다 —
  히스토리가 붙은 커브(예: `makeNurbCircle` 이 살아 있는 원)에서는 그 값이 **절대 위치가 아니라
  트윅(델타)** 이 되어 값이 두 번 섞인다.
- 검증(mayapy 2024): 닫힌 커브 순환 스텐실 일치, 이음매 복사본 동기화, 이음매 CV 만 고른 경우,
  부분 선택·Rough 대칭, degree 5 · 히스토리 살아 있는 원 · 3스팬 최소 커브, 드래그 중 무누적과
  임시 커브 정리, **undo 1스텝**, 열린+닫힌 동시 선택, 그리고 **열린 커브 결과가 이전과 똑같음**.

## v01.07 (2026-09-07)
**`Edit > Joints` 탭 추가 — 커브 위에 조인트를 균일하게 놓고, 그 조인트로 커브를 움직인다.**

- **[Add] Edit > Joints** — TSL 에 담은 커브마다 ① 조인트를 균일 배치 → ② 그 조인트로 **커브를
  바인드**(skinCluster) → ③ 조인트마다 **`_zro` / `_con` / `_ctl` / `_tgt` 컨트롤러 스택**을 세우고
  스택 마지막 노드로 조인트를 컨스트레인트한다. 컨트롤러를 움직이면 조인트가 따라오고, 조인트가
  커브를 움직인다. 스택 구성·옵션·툴팁은 `A00460_ControllerTool` 의 FK 탭과 같은 모양으로 맞췄다.
  - **Count per Curve** — 커브의 처음~끝을 `[0, 1]` 로 보고 그만큼 균일 배치.
    `1` → `0.5` 하나, `2` → `0, 1`, `3` → `0, 0.5, 1`.
  - **Spacing: By length / By parameter** — 기본은 **호 길이 균등**
    (`MFnNurbsCurve.findParamFromLength`). 파라미터 균등은 스팬 길이가 제각각인 커브
    (엣지에서 뜬 커브가 대표적)에서 짧은 스팬에 조인트가 몰린다.
  - **Aim joints along the curve** (기본 켬) — 조인트 X 축을 커브 접선으로. up 힌트는 월드 Y,
    접선이 Y 와 나란하면 월드 Z 로 갈아탄다. 컨트롤러는 조인트에 맞춰지므로 같이 돈다.
  - **Bind the curve to the new joints** (기본 켬) / **Group the new nodes per curve** (기본 켬,
    `<curve>_crvJnt_grp` > `_jnt_grp` · `_ctl_grp`).
  - **Controller Stack** — `zro` / `con` / `tgt` 개별 토글(`ctl` 은 항상 생성), **Control Size**,
    컨스트레인트 **Parent / Point / Orient / Scale**.
  - 커브가 아닌 항목 · 씬에 없는 이름 · **이미 skinCluster 가 걸린 커브**는 사유와 함께
    건너뛰고 로그에 남긴다(중단하지 않는다). 전체가 **undo 한 스텝**.
- **[Note] 닫힌 커브의 seam** — 엣지 루프에서 뜬 커브는 닫혀 있는 경우가 많고, 닫힌 커브에서
  `u=0` 과 `u=1` 은 **같은 점**이다. 그대로 두면 마지막 조인트가 첫 조인트 위에 겹치므로
  닫힌/주기 커브는 마지막 자리를 빼고 `count` 등분한다(`4` → `0, 0.25, 0.5, 0.75`).
- **[Note] 조인트를 그룹에 넣은 뒤 이름이 바뀐다** — 리페어런트하면 롱네임이 통째로 죽는다.
  결과 dict 에는 **옮긴 뒤의 경로**를 담고, 컨트롤러 스택은 리페어런트 전에 **UUID** 를 잡아
  두었다가 다시 해석한다.
- **[Note] `A00460` 의 `fk_manager` 를 import 하지 않고 같은 로직을 이 툴 안에 두었다** —
  `dev/build_release.py` 가 **툴 하나 + Framework** 만 복사하므로 다른 툴의 core 를 참조하면
  릴리스에서 곧바로 깨진다.
- 검증(mayapy 2024): `uniform_us` 경계(1/2/3/닫힘), 호 길이 균등 실측, 열린·닫힌 커브 배치,
  `skinCluster` 웨이트 분포와 컨트롤 → 조인트 → CV 전달, 재바인드 차단, 커브 아님·없는 노드 방어,
  옵션 전부 끈 조합, UI 빌드 후 탭에서 실행 + **undo 1스텝** 복원.

## v01.02 (2026-08-13)
- **[Change] Line Width 탭에서 `Apply` 버튼을 없애고 자동 적용으로** — 슬라이더를 끄는 동안
  실시간으로 반영되고, **손을 떼는 순간 그 값으로 확정**된다(버튼을 누를 필요가 없다).
  스핀박스는 Enter/포커스 아웃이 곧 확정, 화살표 키·그루브 클릭처럼 한 번에 끝나는 변경은
  그 자리에서 적용된다. `Get` / `Use Maya Default (-1)` 는 그대로.
- **[Fix] 확정 적용을 undo 청크 안에서** — 청크를 닫은 뒤에 마지막 값을 쓰면 드래그 하나가
  undo **두 스텝**(드래그 + 커밋)으로 갈라져 `Ctrl+Z` 를 두 번 눌러야 했다. 이제 다시
  **드래그 한 번 = undo 한 스텝**(회귀 테스트로 고정).

## v01.01 (2026-08-13)
**탭 2개로 분리 + Line Width 탭 추가.**

- **[Change] 탭 구성** — 기존 기능(엣지 → 커브 생성 / Reverse Direction)은 **`Create / Direction`**
  탭에 그대로 두고, 새 **`Line Width`** 탭을 더했다. 로그창은 두 탭이 공유한다.
- **[Add] Line Width 탭** — TSL 에 리스트업한 커브들의 **뷰포트 표시 굵기**
  (`nurbsCurve.lineWidth`)를 슬라이더로 조절한다. 목적은 **씬에서 커브를 눈으로 찾고 클릭으로
  집기 쉽게** 하는 것 — 형상·히스토리는 전혀 건드리지 않는 표시 전용 어트리뷰트다.
  - 슬라이더(0.0~10.0, 0.1 단위)와 스핀박스가 서로 동기화되며 **드래그 중 실시간 반영**.
  - **드래그 한 번 = undo 한 스텝**(`sliderPressed` 에서 청크를 열고 `sliderReleased` 에서 닫는다).
  - **Apply** / **Get**(첫 커브 값 읽기) / **Use Maya Default (-1)**.
    `-1` 은 마야 전역 라인 굵기를 따른다는 뜻이고 이게 커브의 기본값이다.
  - 커브가 아닌 항목, `lineWidth` 가 없는 구버전(Maya 2019 미만), 잠기거나 연결된 어트리뷰트는
    **사유와 함께 건너뛴다**(중단하지 않는다).
- 검증(mayapy 2024): 코어·UI 28항목 — 기본값/설정/역읽기, 셰이프 이름 입력, 메시·잠김 스킵,
  탭 분리 후 기존 Create·Reverse 회귀, 슬라이더↔스핀박스 동기, 드래그 undo 1스텝, 빈 리스트 방어.

## v01.00 (2026-07-29)
첫 릴리스. 선택한 메시 엣지로 커브를 만들고 커브 방향을 정렬하는 in-Maya PySide 툴.

- **[Add] 엣지 → 커브 생성 (그룹마다 하나씩)** — 선택한 폴리곤 엣지를 **연결 성분(붙어 있는 엣지 덩어리)별로
  그룹**지어 그룹마다 커브 1개를 만든다. `ref/ref_01.mel`(`duplicateCurve`+`attachCurve`)은 선택 전체를 커브
  **1개**로만 묶어 여러 커브를 못 만들었는데, 그 한계를 푼다. 예) `e[156:158]`, `e[196:199]`, `e[236:239]` → 커브 3개.
  - 엔진은 그룹별 `polyToCurve(form=2, degree, ch=1)` — cv 순서를 스스로 정렬해 견고하고 끝점이 명확.
    `ch=1` 이라 커브가 **메시에 부착**(엣지가 움직이면 따라감).
  - **Name Prefix**(기본 `edgeCurve`), **Smooth curve (degree 3)** 옵션(끄면 직선 degree 1).
- **[Add] Reverse Direction (방향 통일)** — TSL 에 리스트업한 커브들의 `cv[0]`/`cv[n]` 월드 위치를 지정 축
  (**X/Y/Z**, 기본 Y)으로 비교해, `cv[0]` 이 **Max end**(기본, 예=위) 또는 **Min end** 에 오도록 `reverseCurve`
  로 뒤집는다. 이미 맞는 커브·판단 불가(두 끝 축값 동일)·커브 아님은 건너뛰고 로그 표시. (A00360_SortTool 축 비교 이식.)
- **[Add] 셸프 아이콘** — 커브 + CV 포인트 + 방향 화살표(house style).
