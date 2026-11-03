---
title: 작업 일지 (WORKLOG)
aliases: [WORKLOG, 작업일지, devlog]
tags: [worklog, maya-python]
updated: 2026-11-03
---

# 작업 일지 (WORKLOG)

git 커밋 기록을 근거로 하루 작업을 요약한다. 최신 날짜가 위.

**이 파일은 현재 월을 담는다.** 지난 달은 [`worklog/`](worklog/) 로 내려간다 —
파일 자체는 늘 이 경로에 있으므로 이 문서를 가리키는 링크는 깨지지 않는다.
트리거와 절차는 [`worklog/README.md`](worklog/README.md).

> [!info] 보기
> Obsidian 에서 `JUN_All/docs` 를 vault(또는 폴더)로 열면 속성/태그/링크가 동작한다.
> 굵게/링크가 별표째 보이면 소스 모드이므로 `Ctrl+E` 로 읽기/라이브 프리뷰 전환.

---

## 지난 달 보관

| 월 | 파일 | 작업일 |
|----|------|--------|
| 2026-10 | [`worklog/2026-10.md`](worklog/2026-10.md) | 14일 |
| 2026-09 | [`worklog/2026-09.md`](worklog/2026-09.md) | 16일 |
| 2026-08 | [`worklog/2026-08.md`](worklog/2026-08.md) | 18일 |
| 2026-07 | [`worklog/2026-07.md`](worklog/2026-07.md) | 18일 |
| 2026-06 | [`worklog/2026-06.md`](worklog/2026-06.md) | 12일 |

---

## 2026-11-03 (오늘)

> [!summary] A00110_animTool_V02 **v02.35 Hot Key > Main `Animation Layers > Delete BaseAnimation` — MEL `delete BaseAnimation;` 과 같은 결과** · A00030_quickTool_V02 v02.10 에서 제거 `#A00110_animTool_V02` `#A00030_quickTool_V02`
- 요청: "delete BaseAnimation 이 mel 명령이 친 것과 같은 결과가 되도록 버튼을 추가." → 처음엔 A00030 v02.09 에 넣었다가 "A00110_animTool_V02 / Hot Key / Main 에 이식하고 A00030 에서 빼" 로 옮겼다. A00030 v02.10 은 코드가 v02.08 과 같다(이력만 남김).
- 구현: `AnimLayerManager.delete_root()` — 루트를 `animLayer -q -root` 로 찾아(이름을 박지 않음) `cmds.delete`. 마야가 자식 레이어 · blend 노드 · 레이어 커브를 지우고 Base 커브를 다시 직접 연결한다. UI 는 Hot Key > Main 의 새 `Animation Layers` 그룹 버튼 + 확인 팝업(기본 No), 지운 뒤 View > Layers 갱신. 되돌릴 수 없어 단축키는 걸지 않았다.
- mayapy 실측: 레이어 3단에서 mel 과 **남은 노드 · 프레임 1/5/10 값 · tx 입력 연결이 같다**. 이 삭제는 **undo 로 레이어가 돌아오지 않아서**(standalone, undo 켠 상태) 팝업을 둔다. 시험 `tests/test_anim_layers.py` **46/46**(D1~D6 추가). **마야 GUI 확인 아직** — 팝업 · GUI 에서의 undo.

---
