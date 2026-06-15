# A00110_animTool — Mirror Key 탭 추가 계획서

작성일: 2026-06-15 / 대상 툴: `JUN_All/tools/A00110_animTool` / 버전: v01.04

---

## 0. 한 줄 요약

한쪽 컨트롤러의 키프레임을 **반대쪽 컨트롤러로 좌우 미러**하는 네 번째 탭("Mirror Key")을 추가한다.
언리얼 *Mirror Data Table* 로 애니메이션을 미러하는 것과 같은 결과를 Maya 컨트롤러 단계에서 만든다
(예: 달리기 사이클에서 왼팔 스윙 → 오른팔 대칭). **소스/타겟의 rotateOrder 가 달라도 정확**해야 한다.

---

## 1. 요구사항

1. **rotate order 무관** — 오일러 채널 부호 반전이 아니라 **월드 매트릭스 반사 → 타겟 rotateOrder
   재분해** 방식으로 처리한다(부호 반전은 rotateOrder·축 정렬에 의존하므로 불가).
2. **자동 토큰 페어링** — 선택한 컨트롤만으로 반대쪽을 찾는다. 좌/우 토큰은 **JSON 파일로 관리**해
   코드 수정 없이 계속 확장한다(`_l/_r`, `_L/_R`, `_lf/_rt`, `Left/Right` 기본).
3. **수동 인덱스 매칭 폴백** — 비대칭 네이밍이면 Source/Target 리스트로 직접 짝짓는다.

비목표(v01): 탄젠트 완전 미러, 임의 오브젝트 기준 미러 평면, non-TRS 어트리뷰트.

---

## 2. 핵심 미러 수학 (rotate order 무관)

소스 `src` → 타겟 `tgt`, 시각 `t` 마다 (`maya.api.OpenMaya` 2.0):

```
Ms  = MMatrix(getAttr(src.worldMatrix[0],        time=t))   # 소스 rotateOrder 무관
Mpi = MMatrix(getAttr(tgt.parentInverseMatrix[0], time=t))  # 부모 애니 t시점 평가
local = (refl * Ms * refl) * Mpi      # refl=반사축 대각행렬(X→diag(-1,1,1,1))
tm  = MTransformationMatrix(local)
pos = tm.translation(kTransform)
eul = tm.rotation(asQuaternion=True).asEulerRotation()
eul.reorderIt( RO_ENUM[ getAttr(tgt.rotateOrder) ] )        # 타겟 order 로 기록(라디안→도)
setKeyframe(tgt.<attr>, time=t, value=...)                  # 활성 채널만
```

- **읽기**는 worldMatrix(오일러 무관), **쓰기**는 reorderIt(타겟 order) → 양쪽 order 무관 보장.
- `refl * Ms * refl` 은 위치를 반사축으로 반사 + 회전을 켤레(conjugate)하여 **det +1(정상 회전)** 유지.
- `getAttr(..., time=t)` 로 currentTime 을 옮기지 않고 평가(빠르고 안전, 부모 애니도 정확).
- **월드 경유**이므로 타겟의 실제 부모 공간 기준으로 로컬값을 역산 → 리그가 behavior/orientation
  어느 셋업이든 동작(대칭 리그 전제).
- 센터 컨트롤(좌/우 토큰 없음)은 `src==tgt` self-mirror 로 자연 처리.

### 검증(구현 시 numpy 없이 순수 파이썬으로 row-vector 규약 재현해 확인 완료)
- pos(3,2,5)/RotZ(30°), axis X → 결과 pos(-3,2,5)/RotZ(-30°) ✓
- 복합 회전에서 `det(반사 회전)=+1` ✓
- 대칭 부모(타겟 부모 = 소스 부모의 거울상)에서 타겟 로컬이 정확히 복원 ✓

---

## 3. 좌/우 토큰 JSON (확장 가능)

파일: `app/config/mirror_tokens.json` (A00090 의 `rules_v01/*.json` 데이터 주도 방식과 동일 컨셉).

```json
{
  "version": 1,
  "token_pairs": [
    {"left": "_l",   "right": "_r",    "enabled": true},
    {"left": "_L",   "right": "_R",    "enabled": true},
    {"left": "_lf",  "right": "_rt",   "enabled": true},
    {"left": "Left", "right": "Right", "enabled": true}
  ]
}
```

- 로더 `MirrorTokenStore.load()`: `enabled` 쌍만 반환. **파일 없음/파싱 실패/빈 목록이면 코드 내장
  `DEFAULT_TOKEN_PAIRS` 로 폴백**(+로그 메시지) → 항상 동작 보장.
- `MirrorTokenStore.save(pairs)`: UI 편집 결과를 같은 JSON 으로 기록(`encoding="utf-8"`).
- 위→아래 순서가 매칭 우선순위. 새 네이밍은 JSON 행 추가만으로 지원.

### 페어링 규칙 (`resolve_pairs`)
- 이름의 토큰을 양방향 치환 → 후보가 씬에 존재하면(`objExists`) 페어 확정. substring 오탐(`_l` ⊂
  `arm_lower`)은 존재 검사로 걸러짐.
- 토큰 없음 → center(self). 토큰 있는데 반대쪽 노드 없음 → unpaired(건너뜀, 로그).
- 좌·우 모두 선택해도 한 방향만(먼저 본 쪽이 소스) → 스왑 오염 방지.

---

## 4. 파일 변경

| 파일 | 변경 | 내용 |
|------|------|------|
| `app/core/mirror_key_manager.py` | 신규 | `MirrorKeyManager` (정적 + undoInfo 청크 + `(count,msg)`). `resolve_pairs`, `mirror_keys`, `_mirror_one`, `AXES`/`RO_ENUM`. OpenMaya 2.0. |
| `app/core/mirror_token_store.py` | 신규 | `MirrorTokenStore.load()/save()` + `DEFAULT_TOKEN_PAIRS` 폴백. |
| `app/config/mirror_tokens.json` | 신규 | 좌/우 토큰 쌍 데이터. |
| `app/core/__init__.py` | 수정 | `MirrorKeyManager`, `MirrorTokenStore` export. |
| `app/ui/main_window.py` | 수정 | `_build_mirror_key_tab()` + addTab + `on_mirror_key`/`on_mir_resolve` + 토큰 테이블 핸들러. 공용 `te_log` 재사용. |
| `app/config/version.py` | 수정 | `VERSION="01.04"`. |
| `docs/A00110_animTool.md` | 수정 | 5.4 Mirror Key 탭 + 사용 순서/동작 규칙/로그 섹션. |

재사용: `JUN_mod_tsl_qt_v01`(Source/Target 리스트), 공용 `te_log`/`log()`, 기존 매니저의
undo·`(count,msg)` 컨벤션, Copy Key 탭의 시간범위/검증 흐름.

---

## 5. UI (Mirror Key 탭) — 모든 텍스트 영문

- Mode: Auto pair from selection(기본) / Manual list
- Source / Target 리스트(`JUN_mod_tsl_qt_v01`) + Resolve Pairs(자동 결과 미리보기)
- Mirror Axis: X(기본)/Y/Z · Channels: [v]Translate [v]Rotate
- Start/End(기본 playback) · Time: Source keys(기본)/Bake
- L/R Tokens(접이식 QTableWidget): Add/Remove Row, Save/Reload → `mirror_tokens.json`
- Mirror Selected 실행. 결과는 `te_log` 에 `"<n> pair(s) mirrored (axis: X). <m> skipped..."`

---

## 6. 엣지케이스

- 잠긴 채널(`getAttr lock`) 제외, `setKeyframe` 실패 키는 건너뜀. 키 0개 페어는 skip 집계.
- 부모 애니 → parentInverse `time=t` 평가. 비대칭/오프셋 리그 → 결과 어긋날 수 있음(문서 안내).
- 토큰 JSON 폴백(없음/깨짐/빈 목록 → DEFAULT). 전체 단일 undo 청크.

---

## 7. 검증 (Maya)

1. `src=tgt`, axis X → 대칭 포즈 시각 확인.
2. 소스 `xyz` / 타겟 `zxy` 교차 → 결과 월드 포즈가 소스 거울상과 일치.
3. 부모 애니 상태 미러 정확도. 4. 왼팔 FK 스윙 → 자동 페어 미러 → 재생 대칭 확인.
5. 잠긴 채널/키 없음/unpaired 메시지·skip.
6. 토큰 JSON: 파일 없음/깨진 JSON → DEFAULT 폴백. UI 행 추가→Save→Reload 반영. 새 토큰 인식.
