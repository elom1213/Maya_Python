---
name: wip-a00470-materialtool
description: "A00470_MaterialTool - 머티리얼 이름 규칙 진단(JSON 프로파일). 토큰을 앞에서부터 붙이지 말고 정렬 DP 로 맞춰야 \"생략된 토큰\" 이 나온다 (v01.03)"
metadata: 
  node_type: memory
  type: project
  originSessionId: ab0fb3dc-63c8-41e1-86da-70abc7b8ab38
  modified: 2026-09-16T01:18:06.624Z
---

`A00470_MaterialTool` **Name Check** 탭 (v01.00 → **01.02**, 2026-09-16). 아키텍처 (B) PySide, in-Maya.
메시를 TSL 에 담으면 붙은 머티리얼을 모아 **이름이 규칙에 맞는지** 진단하고 **고칠 이름을 제안**한다.
씬은 **읽기만** 한다.

**규칙은 코드가 아니라 데이터** — `data/profiles/<이름>.json` 한 파일이 규칙 한 벌이고 콤보가 그 폴더를
그대로 보여준다. 토큰 타입 `literal` / `enum` / `pattern`(접두사+자릿수) / `regex` / `any`,
공통 필드 `optional` · `repeat`(꼬리 슬롯) · `case_sensitive` · `hint`. 모르는 타입은 `any` 로 폴백.
첫 프로파일 `Set_v001` = `MT_MANU_CH_{character}_{set}_{part}_{extra...}`
(`SetXXX` 는 **3자리**로 해석 — `"digits": 3` 한 줄로 바뀐다).

**v01.01 (같은 날)** — 고정 토큰 **`CH`** 를 `MANU` 뒤에 추가. **코드는 한 줄도 안 바뀌고 JSON 만 고쳤다**
(규칙을 데이터로 둔 설계의 첫 배당). **★ `CH` 와 `CHN` 은 편집 거리 1 이라 서로 빨려들 수 있는 자리다** —
`MT_MANU_CHN_Set002_Top` 은 "`CH` 생략 + `CHN` 은 캐릭터", `MT_MANU_CH_Set002_Top` 은 "`CH` 제자리 +
캐릭터 생략" 으로 읽혀야 하고, 정렬 점수(유효 `+4` > 오타 `+2`)가 둘 다 옳게 고른다(테스트로 고정).

**★ 가장 중요한 판단 — 토큰을 앞에서부터 슬롯에 붙이면 안 된다.**
`MT_SYN_Sett002_Pantss` 는 `MANU` 가 빠진 이름이다. 순서대로 붙이면 뒤가 전부 밀려 **"전부 틀림"**
이라는 쓸모없는 리포트가 나온다. **정렬 DP**(Needleman–Wunsch 꼴, `_align`)로 푼다 — 수는 셋:
짝짓기 / 슬롯 비우기(생략) / 토큰 버리기(잉여). 점수 `+4` 유효 · **`+2` 고칠 수 있는 오타**
(= "그 자리에 오려던 토큰") · `-1` 전혀 아님 · `-2` 슬롯 비움 · `-3` 토큰 버림.
**반복 슬롯(`extra`)은 정렬에서 빼고 꼬리로 받는다**(개수가 안 정해지므로). 이 점수 배치 덕에
요청한 그대로 `SYN, Sett002, Pantss` + **생략 `MANU`** 가 나온다.

**제안은 돌려주기 전에 자기 `is_valid()` 로 다시 검사한다** — 통과 못 하는 수정 제안은 없느니만 못하다.
`enum` 은 편집 거리(4글자 이하 1, 그 위 2 — 짧은 단어는 한 글자만 달라도 다른 단어라 `CHN`/`SIN` 은
서로 안 고친다), `pattern` 은 알파벳/숫자를 갈라 재조립(`Sett002`→`Set002`, `Set0002`→`Set002`).
테스트로 **모든 제안이 그 자신 규칙을 통과하는지**를 못 박았다.

**꼬리 숫자**: 마지막 토큰에 **붙은** 숫자만 경고(`..._extra3` → `extra_3` 제안).
`_002` 처럼 갈라진 숫자 토큰은 통과. **`Set002` 도 통과** — 고정 슬롯이 원래 요구한 숫자다.

**★ 한 트랜스폼에 셰이프가 여럿이면 "첫 셰이프" 만 보는 순간 머티리얼을 놓친다**
([[extendtoshape-picks-wrong-shape]] 와 같은 계열). `geometry_shapes()` 는 non-intermediate 셰이프를
**전부** 본다. 페이스별 할당도 SG 가 셰이프에 연결되므로 같은 경로로 잡힌다(실측).
표의 행 클릭은 `noExpand` 로 **머티리얼 노드 자체**를 선택한다.

생략된 슬롯은 고정값이면 그 값(`MANU`), 아니면 자리표시(`{character}`)로 적는다 — 로그에서
"그 단어가 빠졌다" 와 "그 종류의 토큰이 빠졌다" 는 다른 말이다.

리포트는 **남에게 건네는 글**이라 기본으로 클립보드에 복사한다(체크박스 기본 켬).
`Detailed` 는 틀린 토큰마다 기대 규칙 + 고칠 값을 한 줄씩 편다.

**v01.02** — 로그창을 공용 위젯 [[framework-log-widget]](`JUN_mod_log_qt_v01`, Expand/Clear/Copy)로
교체. 이 툴이 그 위젯의 **첫 사용처**다. 탭들은 예전처럼 `appendPlainText` 를 부르면 된다.

**v01.03** — 머티리얼 표: 칸 폭 드래그 + **더블클릭으로 씬 선택**.
**★ 드래그로 폭을 바꾸려면 헤더가 `Interactive` 여야 한다** — `Stretch`/`ResizeToContents` 는
스타일이 폭을 계산해 버려 **드래그가 막힌다.** `setStretchLastSection(False)` 도 같이 꺼야
마지막 칸이 사용자 폭을 지킨다. 선택은 `itemSelectionChanged`(한 번 클릭)에서
`itemDoubleClicked` 로 옮겼다 — 안 그러면 훑어보는 동안 씬 선택이 딸려 바뀌고, 더블클릭을
얹어도 무의미해진다. 여러 행을 골라 두고 더블클릭하면 전부 선택.

검증: mayapy 2024 헤드리스 **규칙 엔진 102 + 마야 통합 27 + 로그 위젯 56 + 표 21항목**.
**마야 GUI 확인은 아직.**
코어 3개(`profiles` · `name_rules` · `reporter`)는 `maya.cmds` 무의존이라 단독 테스트된다.
문서 `JUN_All/docs/A00470_MaterialTool.md`. 관련: [[mayapy-headless-verify]],
[[prefer-pyside-for-new-tools]], [[new-tool-needs-icon]], [[framework-tsl-attach-uuids]].
