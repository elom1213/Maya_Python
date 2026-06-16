# Push 계획서 — 드래그&드롭 설치 파일 이름 충돌 버그 수정

- **작성일**: 2026-06-16
- **브랜치**: `dev`
- **Push 대상**: `Dnable_repo/dev` (현재 upstream: `Dnable_repo/dev`)
- **기준 커밋**: `7818961 feat(A00110_animTool): add "Mirror Current Frame" to Mirror Key (v01.06)`

---

## 1. 배경 / 문제

드롭 설치 파일을 Maya 뷰포트에 드래그&드롭하면 **버튼이 생성되지 않거나, 이전에 드롭했던 툴의 버튼이 생성**되는 버그.

- **원인**: `TOOL_LABEL` 전역 변수가 아니라 **드롭 파일의 파일명(basename) 충돌**.
  Maya 는 드롭된 `.py` 를 `importlib.import_module(basename)` 로 import 한다.
  모든 (B) 툴의 드롭 파일이 똑같이 `config.py` 였기 때문에:
  - 첫 드롭 → `sys.modules["config"]` 에 캐시
  - 다음 툴 드롭 → 캐시된 **이전 모듈** 재실행(이전 버튼 생성) 또는 전역 `JUN_All/config.py` 와 충돌(버튼 미생성)
- **해결**:
  1. 드롭 파일을 툴마다 고유 이름 `__dragDrop_<번호>.py` 로 rename
  2. `onMayaDroppedPythonFile` 끝에서 `sys.modules.pop(__name__, None)` 로 자기 자신을 캐시에서 제거

---

## 2. 커밋 구성 (2개 — 버그 수정 / 무관 데이터 분리)

### 커밋 1 — 버그 수정 (이번 작업의 본체) ✅ push 대상

```
fix(dragDrop): unique install-file names to stop shelf-button collision

드롭 파일이 전부 config.py / __dragDrop.py 라 Maya 의 basename import 가
sys.modules 에 첫 모듈만 캐시 → 다른 툴 드롭 시 이전 버튼 생성/미생성.
파일을 __dragDrop_<번호>.py 로 고유화하고 onMayaDroppedPythonFile 에서
sys.modules.pop(__name__) 으로 자기 캐시를 제거.
```

포함 파일 (rename 13 + 문서 9):

| 분류 | 파일 |
|------|------|
| (B) config.py → __dragDrop_\<번호\>.py | A00110, A00120, A00130, A00140, A00150, A00160, A00170, A00180, A00190 |
| (A) __dragDrop.py → __dragDrop_\<번호\>.py | A00000, A00040, A00050, A00060 |
| 문서(파일명 동기화) | docs/A00110·A00140·A00150·A00160·A00170·A00180·A00190.md, docs/A00190_..._plan.md, docs/plans/A00180_..._rework.md |

> 모든 13개 드롭 파일에 `onMayaDroppedPythonFile` + `sys.modules.pop` 적용 확인 완료.

### 커밋 2 — KWI 작업 데이터 (무관, **분리 권장 / push 보류 검토**) ⚠

```
M JUN_All/tools/A00080_KWI_creator_V02/app/core/0010_src/A0003_Src_KWI_LD_v02.py
M JUN_All/tools/A00080_KWI_creator_V02/app/core/0010_src/A0101_tgtBones.py
```

- 이번 버그와 무관. KWI 노드 템플릿 GUID 재생성 + `tgtBones` 타겟 본 목록을
  `cv_spline_necklace_*` → `DHA_hair_*` 로 교체한 **작업용 입력 데이터**.
- `A0101_tgtBones.py` 는 사실상 스크래치 입력 데이터이므로, 함께 커밋할지
  아예 제외(`git restore`)할지 **사용자 확인 필요**.

---

## 3. 검증 (push 전 확인 완료 항목)

- [x] 13개 드롭 파일 전부 고유 이름 + `sys.modules.pop` 적용
- [x] import 깨짐 없음 — `launch.py` 의 `import config as jun_config` 는 툴 로컬이 아닌
      전역 `JUN_All/config.py`(DEV_MODE) 를 가리킴(rename 무관). `app/config/` 하위 패키지도 무관
- [x] A00010/20/30 의 `config.py` 는 드롭 파일이 아닌 설정 파일(드롭 진입점 없음) → 그대로 둠
- [x] 옛 파일명 잔재 문서 정리(A00190_plan, A00180_rework)
- [ ] (선택) Maya 2023 에서 임의 2개 툴 연속 드롭하여 각각 올바른 버튼 생성 확인

---

## 4. 실행 명령

```bash
# 1) 버그 수정 커밋 (rename + docs)
git add JUN_All/tools/*/__dragDrop_A*.py JUN_All/docs/
git commit   # 위 "커밋 1" 메시지

# 2) (확인 후) KWI 데이터 분리 커밋  ─ 또는 git restore 로 제외
git add JUN_All/tools/A00080_KWI_creator_V02/
git commit   # 위 "커밋 2" 메시지

# 3) push
git push Dnable_repo dev
```

> push 대상 remote 는 기본값 `Dnable_repo` (origin 아님).
