# Claude Code 메모리 (PC 간 공유)

이 폴더는 Claude Code 의 **프로젝트 메모리**(규칙 · 패턴 · 작업 기록) 원본이다.
git 으로 추적해서 **여러 PC 가 같은 기억을 공유**한다.

- `MEMORY.md` — 세션마다 컨텍스트에 로드되는 인덱스 (한 메모리당 한 줄)
- `*.md` — 메모리 1개 = 파일 1개 (frontmatter 의 `type`: `user` / `feedback` / `project` / `reference`)

---

## 동작 방식

Claude Code 는 메모리를 **`~/.claude/projects/<프로젝트경로해시>/memory/`** 에서 읽고 쓴다.
그 경로를 이 폴더로 **디렉터리 정크션(junction)** 걸어 두면, Claude 가 메모리를 저장하는 순간
곧바로 이 repo 의 변경으로 잡히고 커밋/푸시할 수 있다.

```
~/.claude/projects/<해시>/memory   ──junction──▶   <repo>/.claude/memory   (원본, git 추적)
```

> `<해시>` 는 **프로젝트 절대경로에서 파생**된다. PC 마다 repo 경로가 다르면 해시 폴더명도 다르므로,
> **PC 마다 아래 셋업을 1 회** 해 줘야 한다.

---

## 새 PC 셋업 (1회)

1. repo 를 clone 한다. (메모리는 `.claude/memory/` 에 같이 딸려 온다)

2. 그 PC 에서 이 프로젝트로 Claude Code 를 **한 번 실행**한다.
   → `~/.claude/projects/` 아래에 그 PC 기준의 해시 폴더가 생긴다.

3. 해시 폴더 이름을 확인한다.

   ```powershell
   Get-ChildItem "$env:USERPROFILE\.claude\projects" | Select-Object Name
   ```

4. 그 폴더 안에 `memory` 가 **이미 있으면 비우거나 백업**한 뒤(정크션은 빈 경로에만 생성 가능),
   repo 쪽으로 정크션을 건다. **관리자 권한 불필요.**

   ```powershell
   $link   = "$env:USERPROFILE\.claude\projects\<해시폴더>\memory"
   $target = "<repo 절대경로>\.claude\memory"

   if (Test-Path $link) { Rename-Item $link "memory_backup" }
   New-Item -ItemType Junction -Path $link -Target $target
   ```

5. 확인.

   ```powershell
   Get-Item $link | Select-Object LinkType, Target     # LinkType = Junction
   (Get-ChildItem $link).Count                          # repo 의 파일 수와 같아야 함
   ```

6. 잘 되면 3 단계의 `memory_backup` 을 지운다.

---

## 주의

- **`~/.claude/projects/<해시>/` 폴더째로 올리지 말 것.** 같은 폴더에 세션 전체 대화 로그(`*.jsonl`,
  수십 MB)가 들어 있다. 공유 대상은 `memory/` 하위뿐이다.
- `.claude/settings.local.json` 은 **PC 별 개인 설정**이라 `.gitignore` 로 제외돼 있다.
- 메모리를 갱신했으면 다른 PC 로 넘어가기 전에 **커밋 + 푸시**, 새 PC 에서는 **작업 전 pull**.
  (양쪽 PC 에서 같은 메모리를 고치면 평범한 git 충돌이 난다 — 텍스트라 병합은 쉽다)
- 이 repo(`Dnable_repo` = `elom1213/JUN_Dnable`)는 **private** 임을 전제로 한다.
