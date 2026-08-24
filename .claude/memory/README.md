# Claude Code 메모리 (PC 간 공유)

이 폴더는 **`Maya_Python` 저장소의** 프로젝트 메모리 원본이다.
git 으로 추적해서 여러 PC 가 같은 기억을 공유한다.

- `MEMORY.md` — 세션마다 컨텍스트에 로드되는 인덱스 (한 메모리당 한 줄)
- `*.md` — 메모리 1개 = 파일 1개 (frontmatter 의 `type`: `user` / `feedback` / `project` / `reference`)

---

## 동작 방식

Claude Code 는 메모리를 **`~/.claude/projects/<경로슬러그>/memory/`** 에서 읽고 쓴다.
그 경로를 이 폴더로 **디렉터리 정크션(junction)** 걸어 두면, Claude 가 메모리를 저장하는 순간
곧바로 이 repo 의 변경으로 잡힌다.

```
~/.claude/projects/<슬러그>/memory   ──junction──▶   <repo>/.claude/memory   (원본, git 추적)
```

`<슬러그>` 는 해시가 아니라 **프로젝트 절대경로의 구분자(`: \ / _ .`)를 `-` 로 치환한 문자열**이다.

```
C:\Users\USER\Desktop\JP\0030_maya_python_JUN\Maya_Python
→ C--Users-USER-Desktop-JP-0030-maya-python-JUN-Maya-Python
```

경로가 PC 마다 다르면 슬러그도 달라지므로 **PC 마다 셋업을 1 회** 해 줘야 한다.

---

## 새 PC 셋업

**손으로 하지 않는다.** 형제 저장소 `JUN_Claude` 의 스크립트가 전부 처리한다.

```powershell
.\JUN_Claude\setup.ps1          # 정크션 + paths.local.md + ~/.claude/CLAUDE.md
.\JUN_Claude\setup.ps1 -Check   # 점검
```

절차와 설계 배경은 `JUN_Claude/README.md`, `JUN_Claude/DESIGN.md` 참고.

---

## 주의

- **`~/.claude/projects/<슬러그>/` 폴더째로 올리지 말 것.** 같은 폴더에 세션 전체 대화 로그(`*.jsonl`,
  수십 MB)가 들어 있다. 공유 대상은 `memory/` 하위뿐이다.
- `.claude/settings.local.json` 은 **PC 별 개인 설정**이라 `.gitignore` 로 제외돼 있다.
- 메모리를 갱신했으면 다른 PC 로 넘어가기 전에 **커밋 + 푸시**, 새 PC 에서는 **작업 전 pull**.
  (푸시는 그 턴에 요청이 있을 때만 — 전역 규칙 2장)
- 이 repo(`Dnable_repo` = `elom1213/JUN_Dnable`)는 **private** 임을 전제로 한다.
- 메모리는 **저장소마다 따로** 있다. `JUN_Study` 와 `JUN_UE` 도 각자 `.claude/memory/` 를 갖는다.
  이 폴더의 메모리는 `Maya_Python` 세션에서만 로드된다.
