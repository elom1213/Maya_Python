# Push 계획서 — 외부 의존성 중앙 관리

- **작성일**: 2026-06-16
- **브랜치**: `dev`
- **Push 대상**: `Dnable_repo/dev` (현재 upstream)
- **기준 커밋**: `f8be5d0 docs(plans): add push plan documents (A00110 Smart bake, dragDrop rename)`

---

## 1. 배경

JUN_All의 외부 의존성(PySide·pymel 등)을 한곳에서 관리하기 위한 작업. 흩어진
per-tool `requirements.txt`를 정리하고, 설치 가능한 루트 매니페스트 + Maya 안 import 검증
doctor 스크립트 + 의존성 문서를 추가한다.

- 실제 외부 pip 의존성은 `PySide6`(+`PySide2` 폴백) + 빌드용 `pyinstaller`뿐.
- in-Maya 실행은 Maya가 PySide·pymel을 제공 → pip 설치 불필요. standalone/exe 빌드에서만 pip 필요.
- 기존 per-tool 파일 중 A00008·A00090은 표기(PySide6)와 실제 import(PySide2)가 어긋나 있었음.

---

## 2. 커밋 구성 (단일 커밋)

```
chore(deps): centralize external dependency management

루트에 설치 가능한 단일 진실 소스 requirements.txt 추가, Maya 안 import 검증용
dev/check_dependencies.py(doctor) 추가, docs/DEPENDENCIES.md 로 의존성/버전 매트릭스
정리. 흩어진 per-tool requirements.txt 에 단일 진실 소스 포인터 주석 추가, 표기가
어긋났던 A00008·A00090 을 실제 import(PySide2)에 맞게 수정.
```

### 포함 파일

| 분류 | 파일 |
|------|------|
| 신규 — 루트 매니페스트 | `JUN_All/requirements.txt` |
| 신규 — doctor 스크립트 | `JUN_All/dev/check_dependencies.py` |
| 신규 — 의존성 문서 | `JUN_All/docs/DEPENDENCIES.md` |
| 수정 — per-tool 정리(9) | `JUN_All/tools/A00004/08/80/90/110/120/130/140/150 .../requirements.txt` |

> A00008·A00090: `PySide6` → 실제 import 기준 `PySide2` 로 수정 + 주석.
> 나머지 7개: 단일 진실 소스 포인터 주석만 추가(내용 동일).

### 결정 필요 — 마이그레이션 계획서 포함 여부

- `JUN_All/docs/plans/qt_wrapper_migration_plan.md` *(신규)* — qt 래퍼 마이그레이션은 **나중에 작업**.
  단, `DEPENDENCIES.md` 가 이 파일을 참조하므로 **함께 push 하면 참조가 유효**해진다.
- 옵션 A (권장): 이번 커밋에 함께 포함(또는 `docs(plans)` 별도 커밋) → dangling 참조 없음.
- 옵션 B: 마이그레이션을 실제로 시작할 때까지 보류 → 그때까지 DEPENDENCIES.md 참조는 미존재 파일을 가리킴.

---

## 3. 검증 (push 전 확인 완료)

- [x] `python dev/check_dependencies.py` 실행 → PySide6/pyinstaller OK, pymel/maya.cmds는
      Maya 밖이라 MISSING으로 정확히 보고(정상). 정렬/포맷 확인.
- [x] 루트 `requirements.txt` 는 `pip install -r` 형식 유효(PySide6, pyinstaller).
- [x] per-tool 9개 표기와 실제 import 일치(특히 A00008·A00090 = PySide2).
- [ ] (선택) Maya 스크립트 에디터에서 `dev.check_dependencies.run()` 실행해 in-Maya 출력 확인.

---

## 4. 실행 명령

```bash
# 1) 의존성 관리 파일 스테이징
git add JUN_All/requirements.txt \
        JUN_All/dev/check_dependencies.py \
        JUN_All/docs/DEPENDENCIES.md \
        JUN_All/tools/A000*/requirements.txt
# (결정 시) 마이그레이션 계획서 포함
git add JUN_All/docs/plans/qt_wrapper_migration_plan.md

# 2) 커밋 (위 메시지)
git commit

# 3) push
git push Dnable_repo dev
```

> push 대상 remote 는 기본값 `Dnable_repo` (origin 아님).
> 이 push 계획서 자체(`dependency_management_push_plan.md`)는 기존 관례대로
> `docs(plans)` 묶음에 함께 커밋하거나 제외 — 선택.
