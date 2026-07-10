---
name: wip-a00300-zero-area-quality-rework
description: IN-PROGRESS — A00300_meshDoctor zero_area_faces 판정을 형상품질 기반으로 재작업 (크래시 복구용 체크포인트)
metadata: 
  node_type: memory
  type: project
  originSessionId: 67f36f12-b669-4c14-94ed-e1c1529c6b41
---

**진행 중 작업 (크래시 복구 체크포인트).** 컴퓨터가 꺼져 대화 맥락이 사라져도, 디스크의 파일 + git status + 이 메모로 재개할 수 있게 기록한다. 관련: [[kangaroo-plugin-external-readonly]].

## 목표
`A00300_meshDoctor` 의 `zero_area_faces` 진단을 **절대 면적/Maya `zeroArea()` 의존**에서 **스케일 무관 형상 품질** 기반으로 바꿔, 진짜 슬라이버(케이스 A)와 작지만 멀쩡한 면(케이스 B)을 구분한다. 사용자 확인: **실제 본 메시는 케이스 A(진짜 슬라이버)에 가깝다.**

## 배경 (이미 docs/A00300_meshDoctor.md "진단 노트" 섹션에 기록됨 — 단 아직 커밋 안 됨)
- 현재 진단: `it.zeroArea()` OR 오브젝트공간 `getArea() < 1e-10(AREA_EPS)` → FAIL.
- polyCleanup: zeroGeom `1e-05` 미만 제거. → 둘이 어긋나, polyCleanup이 안 지운 면을 `zeroArea()`가 잡음.
- 케이스 A(슬라이버: 정점 일직선/겹침, 면적~0): Transfer barycentric 깨짐 → FAIL 유지 맞음. 필요한 면이면 closestVertex 모드 우회.
- 케이스 B(작지만 정상): barycentric은 면적 비율이라 정상 → FAIL은 오탐 → INFO/WARN로 강등.
- 결정: 필요한 면은 삭제 금지. 무조건 무시도 금지(A는 진짜 깨짐).

## 변경할 파일
1. `JUN_All/tools/A00300_meshDoctor/app/core/mesh_scan.py`
   - 상수부(~line 33-37): AREA_EPS 옆에 `AREA_DEGEN=1e-10`, `AREA_TINY=1e-5`, `QUALITY_EPS=1e-2` 추가.
   - `_check_topology` 의 per-face 루프(~line 299-331, `zero_area` 수집부): face별 area + 형상품질 q 계산.
     q = 등주지수 `(4*pi*area)/(perimeter^2)` (원=1, 정삼각형≈0.60, 슬라이버→0). perimeter = it.getPoints(kObject) 루프 둘레 합.
     후보 = `it.zeroArea() or area < AREA_TINY`. 후보면 중 `area < AREA_DEGEN or q < QUALITY_EPS` → 슬라이버(FAIL `zero_area_faces`),
     아니면 → 작지만 정상(INFO `tiny_faces`). 샘플은 `"f{idx} a={area:.2e} q={q:.3f}"` 문자열로(JSON/TXT에서 A/B 식별).
   - zero_area 메시지: "Degenerate/sliver faces ... 필요한 면이면 closestVertex 모드로 transfer, 삭제 말 것. polyCleanup은 쓰레기 면일 때만."
2. `JUN_All/tools/A00300_meshDoctor/app/core/mesh_fix.py`
   - `select_zero_area_faces`(~line 158-): 동일 기준(q<QUALITY_EPS or area<AREA_DEGEN)으로 슬라이버만 선택하도록 맞춤.
3. `app/config/version.py` → VERSION "01.01", LAST_UPDATE 2026-06-25.
4. `CHANGELOG.md` → v01.01 항목.
5. `docs/A00300_meshDoctor.md` → "진단 노트" 섹션의 "향후 개선 방향(미적용)"을 **적용됨**으로 수정.
6. `docs/WORKLOG.md` → 2026-06-25 최상단 항목 추가.
7. `JUN_All/tools/A00300_meshDoctor/app/ui/main_window.py` → **로그창 Clear 버튼 추가**(사용자 추가 요청).
   Diagnose 행 또는 로그뷰 위/아래에 `Clear Log` 버튼 → `self.te_log.clear()`.

## 상태 체크리스트
- [x] 메모리 체크포인트 작성
- [x] docs "진단 노트" 분석 기록
- [x] mesh_scan.py 형상품질 판정 구현 (`face_quality` + sliver/tiny 분리 + 상수 AREA_DEGEN/AREA_TINY/QUALITY_EPS)
- [x] mesh_fix.py select_zero_area_faces 동기화
- [x] main_window.py 로그 Clear 버튼 추가
- [x] version 01.01 + CHANGELOG
- [x] docs 진단노트 "v01.01 적용"으로 갱신 + 진단항목 목록 + WORKLOG
- [x] py_compile 통과 (mesh_scan/mesh_fix/main_window)
- [ ] (사용자 요청 시) Dnable_repo/dev 푸시 — **아직 푸시 안 함**
- [ ] 마야 실기 테스트(드롭→셸프, 실제 케이스 A 메시로 q 값 확인 + Clear Log 동작) — 사용자 측

**상태: 구현 완료 (커밋/푸시 전).** 재개 시 `git status` 로 변경 확인 후, 필요하면 푸시([[push-target-dnable-dev]]).
**작업 완료되어 사용자 검증·푸시만 남으면 이 메모는 삭제해도 됨.**
