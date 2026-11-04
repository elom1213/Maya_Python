# Python Script by Ji Hun Park
# last Update date : 2026-11-04
# A00210_FileManager - git sync (UI/DCC 비의존)
#
# 중앙 데이터 리포(records/thumbs)를 시스템 git 으로 pull/push 한다.
# GitPython 의존 없이 subprocess 로 PATH 의 git 을 호출한다.
# 자격증명은 캐시된 git creds 에 의존한다(별도 입력받지 않음).
#
# 모든 메서드는 (ok: bool, output: str) 을 반환하고, 예외로 죽지 않는다.
#
# v01.45 : 브랜치는 main 하나, 프로파일 데이터는 <repo>/profiles/<data_folder>/ 폴더.
#   - push 는 **이 프로파일 폴더만** 스테이징한다(다른 프로파일 폴더의 미커밋 변경은 섞지 않는다).
#   - pull / push 전에 `pull --rebase --autostash` - 다른 PC 가 다른 폴더를 올렸어도 충돌 없이 이어 붙인다.
#   - 푸시가 거절되면(그 사이 누가 올림) 한 번 더 받고 다시 올린다.
#   - 클론의 현재 브랜치가 설정과 다르면 아무것도 하지 않는다(check_branch) - 옛 프로파일 브랜치 클론 보호.

import os
import subprocess

# Windows 에서 콘솔 창이 깜빡이지 않게 한다.
_NO_WINDOW = 0
if os.name == "nt":
    _NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)

GITIGNORE_CONTENT = "# Maya 원본 파일은 이 데이터 리포에 두지 않는다 (안전망)\n*.mb\n*.ma\n__pycache__/\n"


class GitSync:

    PROFILES_DIR = "profiles"

    def __init__(self, store_dir, remote="origin", branch="main", data_folder=""):
        self.store_dir = os.path.abspath(store_dir) if store_dir else ""
        self.remote = remote or "origin"
        self.branch = branch or "main"
        self.data_folder = (data_folder or "").strip()
        # 저장소 루트 기준 이 프로파일 데이터 폴더(git 경로라 슬래시)
        self.data_rel = "{0}/{1}".format(self.PROFILES_DIR, self.data_folder) if self.data_folder else ""

    # ---------------------------------------------------------------- run

    def _run(self, *args):
        """git 명령 실행 → (ok, output)."""
        if not self.store_dir:
            return False, "Store directory is not set."

        try:
            proc = subprocess.run(
                ["git"] + list(args),
                cwd=self.store_dir,
                capture_output=True,
                text=True,
                creationflags=_NO_WINDOW,
            )
        except FileNotFoundError:
            return False, "git not found. Install git and ensure it is on PATH."
        except OSError as exc:
            return False, f"git failed to start: {exc}"

        out = (proc.stdout or "") + (proc.stderr or "")
        return proc.returncode == 0, out.strip()

    # -------------------------------------------------------------- state

    def is_repo(self):
        return os.path.isdir(os.path.join(self.store_dir, ".git"))

    def _write_skeleton(self):
        """profiles/<data_folder>/records · thumbs + 루트 .gitignore 기본 구조 생성."""
        base = os.path.join(self.store_dir, *self.data_rel.split("/")) if self.data_rel else self.store_dir
        os.makedirs(os.path.join(base, "records"), exist_ok=True)
        os.makedirs(os.path.join(base, "thumbs"), exist_ok=True)

        gitignore = os.path.join(self.store_dir, ".gitignore")
        if not os.path.isfile(gitignore):
            with open(gitignore, "w", encoding="utf-8") as f:
                f.write(GITIGNORE_CONTENT)

    # ------------------------------------------------------------- public

    def ensure_repo(self, remote_url=""):
        """store_dir 을 git repo 로 준비한다.

        - 이미 repo 면 그대로 둔다.
        - remote_url 이 있고 store_dir 이 비어있으면 clone 시도.
        - 아니면 git init + (remote_url 있으면 remote add) + 스켈레톤 생성.
        """
        if not self.store_dir:
            return False, "Store directory is not set."

        os.makedirs(self.store_dir, exist_ok=True)

        if self.is_repo():
            return True, "Repository already initialized."

        logs = []

        is_empty = not os.listdir(self.store_dir)

        if remote_url and is_empty:
            ok, out = self._run_in_parent_clone(remote_url)
            logs.append(out)
            if ok:
                return True, "\n".join(logs)
            # remote_url 이 있는데 clone 실패 → 로컬 init 으로 '조용히' 폴백하지 않는다.
            # (인증/네트워크/권한 문제를 사용자가 인지하도록. 중앙 리포와 끊긴 빈 repo 생성 방지.)
            logs.append(
                "Clone failed. Check the Remote URL, your network, and git "
                "credentials / repo access. No local repository was created."
            )
            return False, "\n".join([l for l in logs if l])

        ok, out = self._run("init")
        logs.append(out)

        ok, out = self._run("checkout", "-B", self.branch)
        logs.append(out)

        if remote_url:
            self._run("remote", "remove", self.remote)
            ok, out = self._run("remote", "add", self.remote, remote_url)
            logs.append(out)

        self._write_skeleton()

        return True, "\n".join([l for l in logs if l])

    def _run_in_parent_clone(self, remote_url):
        """store_dir 위치로 clone. (빈 폴더 가정)"""
        parent = os.path.dirname(self.store_dir)
        target = os.path.basename(self.store_dir)

        try:
            proc = subprocess.run(
                ["git", "clone", "-b", self.branch, remote_url, target],
                cwd=parent,
                capture_output=True,
                text=True,
                creationflags=_NO_WINDOW,
            )
        except FileNotFoundError:
            return False, "git not found. Install git and ensure it is on PATH."
        except OSError as exc:
            return False, f"git clone failed to start: {exc}"

        out = (proc.stdout or "") + (proc.stderr or "")
        return proc.returncode == 0, out.strip()

    # ------------------------------------------------------------ branch

    def current_branch(self):
        ok, out = self._run("rev-parse", "--abbrev-ref", "HEAD")
        return out.strip() if ok else ""

    def check_branch(self):
        """클론의 현재 브랜치가 설정(self.branch)과 같은지. 다르면 (False, 안내문) - pull/push 는 아무것도 안 한다."""
        if not self.is_repo():
            return False, "Not a git repository. Run Init/Clone first."
        cur = self.current_branch()
        if cur != self.branch:
            return False, ("This clone is on branch '{0}', but the profile expects '{1}'. "
                           "Push any old work first, then use 'Switch to {1}'.".format(cur or "?", self.branch))
        return True, ""

    def has_local_changes(self):
        ok, out = self._run("status", "--porcelain")
        return ok and bool(out.strip())

    def switch_branch(self):
        """설정 브랜치로 옮긴다. 미커밋 변경이 있으면 거부(옛 데이터 보호)."""
        if not self.is_repo():
            return False, "Not a git repository."
        if self.has_local_changes():
            return False, ("Uncommitted changes in this clone - push them on the old branch first "
                           "(or move them aside). Nothing was switched.")
        logs = []
        ok, out = self._run("fetch", self.remote)
        logs.append(out)
        ok, out = self._run("checkout", self.branch)
        if not ok:
            ok, out = self._run("checkout", "-b", self.branch, "--track",
                                "{0}/{1}".format(self.remote, self.branch))
        logs.append(out)
        return ok, "\n".join([l for l in logs if l])

    def list_data_folders(self):
        """<repo>/profiles/ 아래 폴더 이름(정렬). Data Folder 콤보용."""
        root = os.path.join(self.store_dir, self.PROFILES_DIR)
        if not self.store_dir or not os.path.isdir(root):
            return []
        return sorted((n for n in os.listdir(root) if os.path.isdir(os.path.join(root, n))), key=str.lower)

    # -------------------------------------------------------- pull / push

    def pull(self):
        if not self.is_repo():
            return False, "Not a git repository. Run Init/Clone first."
        ok, msg = self.check_branch()
        if not ok:
            return False, msg
        return self._run("pull", "--rebase", "--autostash", self.remote, self.branch)

    def push(self, message):
        """이 프로파일 폴더만 커밋 -> 받아서 이어 붙이기 -> 푸시(거절되면 한 번 더)."""
        if not self.is_repo():
            return False, "Not a git repository. Run Init/Clone first."
        ok, msg = self.check_branch()
        if not ok:
            return False, msg

        logs = []
        # data_folder 가 없으면(옛 설정) 예전처럼 전체. 있으면 내 폴더만.
        add_args = ["add", "-A", "--", self.data_rel] if self.data_rel else ["add", "-A"]
        ok, out = self._run(*add_args)
        logs.append(out)

        nothing_staged, _ = self._run("diff", "--cached", "--quiet")     # 바뀐 게 없으면 종료 코드 0
        if nothing_staged:
            logs.append("No changes to commit in {0}. Pushing anyway.".format(self.data_rel or "the repository"))
        else:
            ok_commit, out_commit = self._run("commit", "-m", message)
            logs.append(out_commit)
            if not ok_commit:
                return False, "\n".join([l for l in logs if l])

        ok_push = False
        for _attempt in range(2):
            ok_pull, out_pull = self._run("pull", "--rebase", "--autostash", self.remote, self.branch)
            logs.append(out_pull)
            # 원격에 아직 브랜치가 없으면(첫 푸시) 받기 실패는 무시하고 올린다.
            if not ok_pull and "couldn't find remote ref" not in out_pull.lower():
                return False, "\n".join([l for l in logs if l])
            ok_push, out_push = self._run("push", self.remote, self.branch)
            logs.append(out_push)
            if ok_push:
                break
            low = out_push.lower()
            if not ("rejected" in low or "non-fast-forward" in low or "fetch first" in low):
                break
            logs.append("Push was rejected (someone pushed meanwhile) - pulling again and retrying.")

        return ok_push, "\n".join([l for l in logs if l])

    def status(self):
        if not self.is_repo():
            return False, "Not a git repository."
        return self._run("status", "-s", "-b")

    def list_branches(self):
        """로컬 + 원격추적 브랜치의 짧은 이름 목록을 반환. (ok, names).

        네트워크 fetch 없이 로컬 ref 만 읽는다(이미 clone/fetch 된 origin/* 포함).
        예: 로컬 'master' + 원격 'origin/master' → ['master'] 로 합쳐 중복 제거.
        """
        if not self.is_repo():
            return False, []

        names = []

        ok, out = self._run("branch", "--format=%(refname:short)")
        if ok:
            names += [ln.strip() for ln in out.splitlines() if ln.strip()]

        ok_r, out_r = self._run("branch", "-r", "--format=%(refname:short)")
        if ok_r:
            for ln in out_r.splitlines():
                ln = ln.strip()
                # remote/branch 형태(슬래시 포함)만. 'origin'(= origin/HEAD 심볼릭의
                # short)·'origin/HEAD -> ...' 류는 제외.
                if not ln or "->" in ln or "/" not in ln:
                    continue
                short = ln.split("/", 1)[1]     # 'origin/master' → 'master'
                if short and short != "HEAD":
                    names.append(short)

        # 순서 보존 중복 제거 후 정렬.
        seen = set()
        uniq = []
        for n in names:
            if n not in seen:
                seen.add(n)
                uniq.append(n)
        return True, sorted(uniq)
