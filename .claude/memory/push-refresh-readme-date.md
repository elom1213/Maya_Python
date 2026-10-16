---
name: push-refresh-readme-date
description: "Maya_Python 에서 푸시할 때 루트 README.md 의 날짜(최근 갱신)를 진단하고 최신화해서 함께 푸시"
metadata:
  type: feedback
---

Maya_Python 저장소에서 푸시할 때는 루트 `README.md` 의 날짜를 확인하고, 오래됐으면 최신화해서 그 푸시에 함께 담는다.
날짜는 머리의 `> 최근 갱신: YYYY-MM-DD · 툴 폴더 N개 ...` 줄에 있다. 같은 줄의 툴 개수와 아래 최근 작업 표도 함께 맞는지 본다.

**Why:** 사용자가 2026-10-16 에 지정했다. README 가 실제 작업보다 뒤처져 있었다(2026-09-16 에 멈춤).

**How to apply:** 푸시 자체는 그 턴에 요청이 있을 때만 한다(전역 규칙 2장). 푸시 요청이 있으면 [[push-includes-tool-guide-docs]] 의 문서 점검과 같이,
README 날짜를 오늘로 고치고 커밋에 넣는다. README 는 공용 파일이므로 다른 세션 변경이 섞였는지도 본다. 푸시 대상은 [[push-target-dnable-dev]].
