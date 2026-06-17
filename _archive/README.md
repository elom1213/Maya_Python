# `_archive/` — 동결(frozen) 레거시 영역

이 디렉터리는 **예전 세대의 코드와 학습 메모**를 모아둔 아카이브다.
가끔 참고용으로만 열어보고, **수정하지 않는다(read-only)**. 모든 신규 작업은 `JUN_All/`에서 한다.

> 여기 있던 폴더들은 원래 repo 루트에 흩어져 있었으나 2026-06-17에 `git mv`로 이곳에 모았다.
> git 히스토리는 그대로 보존되며(`git log --follow <파일>`), 과거 경로도 추적 가능하다.

---

## 구조

```
_archive/
├── legacy_tools/   # 옛 Maya 툴 (현행 JUN_All 툴로 이미 대체됨)
└── study_notes/    # Python/Maya 학습 메모 (프로덕션 코드 아님)
```

## `legacy_tools/` — 옛 Maya 툴 → 현행 대응

| 아카이브 폴더 | 성격 | 현행(`JUN_All/tools`) 대응 |
|------|------|------|
| `00_Old/` | 옛 프레임워크(`JUN_Tools`, UI/utils) | `JUN_All/Framework`로 대체 |
| `00_RUN/` | Maya 붙여넣기 실행 스니펫 | (실행 조각) |
| `01_Modules/` | 버전별 단일파일 Maya 툴 본체 | ControlRig→`A00130`, FKIK→`A00120`/`A00190`, skinWeight→`A00020`, Quick→`A00030`, Naming/Search/Selection·Shader 등 |
| `01_Modules_Small/` | 소형 단일기능 스니펫 | — |
| `02_Modules_Old/` | 더 오래된 Selection/Shader 버전 | (deprecated) |
| `03_Modules_Test/` | `01_Modules` 툴들의 개발/테스트 버전 | 동일 툴군의 작업 흔적 |
| `04_KWI_generator/` | KWI 노드 생성기 전신 | `A00080_KWI_creator_V02` |

## `study_notes/` — 학습 메모 (비프로덕션)

| 아카이브 폴더 | 내용 |
|------|------|
| `100_Memo/` | Python/Maya 테크닉, 페이셜, naming 등 실험 노트 |
| `101_cellular_automata/` | 셀룰러 오토마타 실험 |
| `101_maya_python_technic/` | 교재 페이지별 연습 코드 |

---

**주의**: 이 영역의 파일을 현행 코드(`JUN_All`)에서 import하지 않는다. 의존성 없음.
