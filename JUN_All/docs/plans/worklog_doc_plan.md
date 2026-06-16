# 작업 일지(WORKLOG) 문서 — 생성/운영 계획서

## 배경 / 목적

하루하루 작업한 내용을 git(GitHub) 기록을 근거로 **간단히 요약**해 누적 기록하는 문서를 만든다.
- 첫 작성 시 **어제(2026-06-15)** 작업분을 요약한다.
- 이후 **오늘(2026-06-16) 및 이후 날짜**도 같은 파일에 누적한다.
- 내용은 **커밋 메시지/변경을 판단**해 작성한다(자동 덤프가 아니라 도메인별로 묶은 요약).

## 결정 사항 (확정)

| 항목 | 결정 |
|------|------|
| 파일 구조 | **단일 누적 파일, 최신 날짜가 위** |
| 갱신 방식 | **수동** — 요청 시 Claude 가 git 기록을 읽고 해당 날짜 섹션 추가/갱신 |
| 언어 | **한국어 요약** (커밋 해시/툴명/식별자는 영어) |
| 렌더 호환 | **Obsidian + GitHub 양쪽에서 보이도록** 작성 |

## 산출물 위치 (경로 제안 포함)

- **권장**: `JUN_All/docs/WORKLOG.md` (단일 파일)
  - 메모리 규칙상 분석/설명 md 는 `JUN_All/docs` 아래에 둔다 → 별도 top-level `docs_history/` 는
    문서가 두 루트로 갈라져 발견성이 떨어진다. **같은 `docs` 안**에 두는 것을 권장.
  - 단일 파일이므로 하위 폴더(`worklog/`)도 과하다 → docs 루트의 `WORKLOG.md` 하나로 충분.
- **대안**(분석 문서들과 시각적으로 분리하고 싶을 때): `JUN_All/docs/worklog/WORKLOG.md`
  - 향후 날짜별 파일로 쪼갤 가능성을 열어두고 싶다면 이 폴더 방식이 확장에 유리.
- `.gitignore` 영향 없음(생성물 폴더 `0020_out`/`JUN_memo` 등과 무관). 일반 추적 문서.

## 데이터 소스 / "어제" 판단

- 시스템 기준 오늘 = `2026-06-16` → **어제 = `2026-06-15`**.
- 추출 명령(하루 단위):
  ```bash
  git log --since="2026-06-15 00:00" --until="2026-06-16 00:00" \
          --pretty=format:"%h | %s" --date=local
  ```
  - 머지 커밋(`Merge branch ...`)은 요약에서 제외.
  - `feat`/`fix`/`refactor`/`perf`/`docs`/`chore` 타입과 스코프(툴명)를 보고 **툴·도메인별로 그룹화**.
- 판단 기준: 같은 툴의 여러 커밋은 한 항목으로 묶고, 버전 변화(`v01.03`→`v01.04`)·핵심 동작만 남긴다.

## 문서 포맷 (Obsidian + GitHub 호환)

````markdown
---
title: 작업 일지 (WORKLOG)
aliases: [WORKLOG, 작업일지, devlog]
tags: [worklog, maya-python]
updated: 2026-06-16
---

# 작업 일지 (WORKLOG)

git 커밋 기록을 근거로 하루 작업을 요약한다. 최신 날짜가 위.

> [!info] 보기
> Obsidian 에서 `JUN_All/docs` 를 vault(또는 폴더)로 열면 속성/태그/링크가 동작한다.

---

## 2026-06-16 (오늘)

> [!summary] 신규 병합 툴 2종 + Qt 인프라 정리
- **A00145_RigConnect**: MEL ConnectionTool V04.02 + A00140 병합(4탭 PySide) 신규 툴, 사용법 [A00145 가이드](../A00145_RigConnect.md) (`5592490`, `d1750df`) #A00145_RigConnect
- **A00060_jointTool_V02**: MEL JointTool V05.03 + A00060 병합(4탭) 신규 툴, 사용법 [A00060 V02 가이드](../A00060_jointTool_V02.md) (`ec42af1`, `bbb78bd`) #A00060_jointTool_V02
- **Framework/qt**: 모든 Qt 툴을 `Framework.qt.qt` 래퍼 경유로 일원화 (`f3c8d58`) #Framework
- **deps**: 외부 의존성 관리 중앙화 (`a13792c`)
- **A00110_animTool**: Smart bake 옵션(native `bakeResults -smart`, v01.07) + 비교 문서 (`859299d`, `c0d7db8`) #A00110_animTool
- **dragDrop**: 드롭 설치 파일명 고유화로 셸프 버튼 충돌 해결 (`30f0f09`)
- **A00190_FKIK_General_Tool**: 레거시 FK/IK 툴 PySide 리팩터 (`cab90a6`) #A00190_FKIK

## 2026-06-15

> [!summary] animTool/abSymMesh PySide 강화 + bake 성능
- **A00110_animTool**: Copy Key 탭(v01.03)·Mirror Key 탭(v01.04) 추가 + 문서화 (`f6139ac`, `147fa7f`, `be41423`, `8917cbf`) #A00110_animTool
- **A00180_abSymMesh**: Python/OpenMaya 재구현(속도)·app/ 레이아웃 + PySide UI·동작 문서 (`f01ced1`, `f6f5053`, `4719e56`) #A00180_abSymMesh
- **A00170_driverTool**: RemapVal + SphericalEye 를 탭 툴로 병합 (`96acac4`) #A00170_driverTool
- **A00150_remapVal**: 보간을 enum(Linear/Smooth/Spline)으로 (`2cb49aa`) #A00150_remapVal
- **A00120_FKIK**: per-frame 루프 대신 native `bakeResults` 로 bake (`b83c591`) #A00120_FKIK
- **A00080_KWI_creator**: 결합 파일 출력(base+setting+LD) (`61c459e`) #A00080_KWI_creator
- **dev/reload**: per-tool `reload_for_tool` 추가 + 전 Qt 런처 전환 (`1660c63`)
- **Framework/styles**: 체크박스·라디오 인디케이터 전 테마 가시성 수정 (`acf285e`, `730f8b4`) #Framework

---
````

- 각 줄: `**툴/도메인**: 한국어 한 줄 요약 (관련 커밋 해시) #툴태그`.
- 날짜 헤딩은 `## YYYY-MM-DD`, 가장 최신 날짜를 머리말 아래에 prepend.
- 오늘 섹션은 작업이 진행되며 같은 날짜 헤딩 아래 항목을 누적/갱신.
- 갱신 때마다 frontmatter 의 `updated:` 를 그날 날짜로 바꾼다.

## Obsidian 호환 규칙 (양쪽에서 깨지지 않게)

- **YAML frontmatter**: Obsidian 은 속성(properties) 패널로, GitHub 은 상단 표로 렌더 → 양쪽 무해.
- **링크는 표준 마크다운 링크** `[라벨](../파일.md)` 사용. Obsidian `[[wikilink]]` 는 GitHub 에서
  literal 텍스트로 깨지므로 **사용하지 않는다**(Obsidian 도 마크다운 링크 정상 지원).
- **태그**: #A00110_animTool 인라인 태그 — Obsidian 에서 검색/그래프로 묶이고, GitHub 에선 일반 텍스트로 보임(무해).
  - frontmatter `tags:` 와 본문 인라인 #tag 를 함께 둬 Obsidian 활용도를 높인다.
  - **주의**: 인라인 태그를 백틱으로 감싸면 인라인 코드가 되어 **태그로 인식되지 않는다**.
    태그는 백틱 없이 평문으로 두고, 백틱은 커밋 해시에만 쓴다.
- **콜아웃** `> [!summary]` / `> [!info]`: Obsidian 은 콜아웃 박스로, GitHub 은 인용블록으로 렌더(무해).
- 헤딩·리스트·코드펜스는 공통 마크다운만 사용.

## 작성 절차 (수동 갱신 시)

1. `git log --since/--until` 로 해당 날짜 커밋 수집(머지 제외).
2. 스코프(툴명) 기준 그룹화, 버전/핵심 동작만 남겨 한국어 한 줄 요약 작성.
3. `WORKLOG.md` 상단 머리말 아래에 해당 날짜 섹션을 **최신이 위**가 되도록 삽입.
   - 같은 날짜가 이미 있으면 그 섹션을 갱신(중복 날짜 헤딩 금지).
   - frontmatter `updated:` 를 그날 날짜로, 툴 태그(#A00110_animTool 등)를 줄 끝에 부착.
4. (선택) 커밋/푸시 여부는 사용자 판단 — 기본은 일반 추적 문서로 커밋 가능.

## 이번 작업 범위 (승인 후 실행)

- `JUN_All/docs/WORKLOG.md` 생성:
  - 머리말 + **2026-06-15(어제) 섹션** 작성(위 포맷의 초안 기준).
  - 요청에 따라 **2026-06-16(오늘) 섹션**도 함께 누적(위 초안 포함).
- 커밋/푸시는 별도 요청 시 진행.

## 향후 확장 (옵션)

- 수동 운영이 번거로워지면 `dev/` 에 git log 파싱 → 날짜 섹션 생성 스크립트 추가 가능.
- 더 나아가 `/schedule`(cron)로 매일 자동 갱신도 가능(현재는 수동 확정).
