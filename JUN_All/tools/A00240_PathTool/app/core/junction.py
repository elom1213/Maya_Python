# Python Script by Ji Hun Park
# last Update date : 2026-10-13
# A00240_PathTool - Windows directory junction helpers (UI/DCC 비의존)
#
# v01.22 : 정션 이름 충돌 자동 해소 - 같은 폴더에 만들 소스들의 **끝 폴더 이름이 같으면**
#          (`ProjA\Content` · `ProjB\Content`) 상위 폴더 이름을 앞에 붙여 `ProjA_Content` · `ProjB_Content`
#          로 짓는다(필요하면 더 위로, 그래도 같으면 `_2`). 전에는 두 번째 행부터
#          "same junction path as an earlier row" 로 막혀 하나만 만들어졌다.
# v01.19 : Junction 탭의 로직. `cmd /c mklink /J <link> <source>` 를 대신 치고, 지울 때는
#          **정션인지 먼저 확인한 뒤** `os.rmdir` 로 링크만 걷어낸다(원본 폴더·내용은 건드리지 않는다).
#
# 정션(junction) 은 **폴더에만** 걸 수 있다(mklink /J). 파일은 하드링크(/H)·심볼릭링크 영역이라
# 여기서는 다루지 않는다 - 파일을 소스로 주면 계획 단계에서 걸러 사유를 돌려준다.
#
# 판별은 `os.lstat` 의 리파스 태그로 한다 - IO_REPARSE_TAG_MOUNT_POINT(0xA0000003) 가 정션이다.
# `os.path.islink` 는 정션에 False 를 주고(심볼릭링크만 True), Python 3.12 의 `os.path.isjunction`
# 은 이 저장소의 런타임(Maya 2024 = 3.10) 에 없다.
#
# 삭제는 `os.rmdir` - 정션에 대고 부르면 링크만 사라지고 타깃 내용은 남는다(RemoveDirectoryW).
# ★ 빈 **실제** 폴더에 대고 불러도 성공하므로, 부르기 전의 `is_junction` 확인이 안전장치의 전부다.

import os
import stat
import subprocess

#: 계획(plan) 행의 상태. ready 만 실제로 만든다.
READY = "ready"


def is_junction(path):
    """path 가 디렉터리 정션인가. 없거나 못 읽으면 False."""
    if not path:
        return False
    try:
        st = os.lstat(path)
    except OSError:
        return False
    attrs = getattr(st, "st_file_attributes", 0)
    if not attrs & stat.FILE_ATTRIBUTE_REPARSE_POINT:
        return False
    return getattr(st, "st_reparse_tag", 0) == stat.IO_REPARSE_TAG_MOUNT_POINT


def junction_target(path):
    """정션이 가리키는 경로(`\\\\?\\` 접두사는 벗긴다). 정션이 아니거나 못 읽으면 ""."""
    if not is_junction(path):
        return ""
    try:
        target = os.readlink(path)
    except OSError:
        return ""
    if target.startswith("\\\\?\\"):
        target = target[4:]
    return target


def plan(sources, targets, mode="n1", target_is_link=False):
    """만들 정션 목록을 계산한다(아직 만들지 않는다).

    sources        : 원본 폴더 경로들.
    targets        : n1 이면 첫 항목만 쓴다(만들 **폴더**). nn 이면 행 순서로 짝을 맺는다.
    mode           : "n1" = 소스 전부를 한 폴더 안에, "nn" = 소스 i 를 타깃 i 에.
    target_is_link : nn 에서만 - 타깃 행을 "만들 폴더" 가 아니라 **정션 경로 그 자체**로 본다
                     (mklink 의 <Link> 처럼 이름까지 정한다).

    정션 이름은 원본 폴더 이름이다. 같은 폴더에 만들 소스들의 끝 이름이 겹치면(`A/Content` 와
    `B/Content`) 겹치는 행들만 상위 폴더 이름을 앞에 붙여 `A_Content` · `B_Content` 로 구분한다
    (`unique_names` 참고). 같은 소스를 두 번 담은 행은 "same source as an earlier row" 로 거른다.

    반환: [(source, link, status)] - status 가 READY 면 만들 수 있다. 아니면 사유 문장.
    """
    sources = [os.path.normpath(s) for s in sources if s]
    targets = [os.path.normpath(t) for t in targets if t]

    # 1차: 행마다 (src, parent, link). link 가 None 이면 이름을 아직 안 정한 것(원본 이름 규칙).
    entries = []
    for i, src in enumerate(sources):
        if mode == "n1":
            tgt = targets[0] if targets else ""
        else:
            tgt = targets[i] if i < len(targets) else ""
        if not tgt:
            entries.append((src, "", None))
        elif mode == "nn" and target_is_link:
            entries.append((src, os.path.dirname(tgt), tgt))
        else:
            entries.append((src, tgt, None))

    # 2차: 원본 이름 규칙인 행들을 "만들 폴더" 별로 묶어 이름을 겹치지 않게 정한다.
    named = {}
    by_parent = {}
    for i, (src, parent, link) in enumerate(entries):
        if parent and link is None:
            by_parent.setdefault(os.path.normcase(parent), []).append(i)
    for idxs in by_parent.values():
        # 같은 소스를 두 번 담은 행은 이름 계산에서 빼고 첫 행의 이름을 그대로 받는다
        # (안 그러면 둘을 가르려고 이름이 전체 경로까지 길어진다 - 뒤에서 사유로 걸러진다).
        first = {}
        for i in idxs:
            first.setdefault(os.path.normcase(entries[i][0]), i)
        uniq = list(first.values())
        names = dict(zip(uniq, unique_names([entries[i][0] for i in uniq])))
        for i in idxs:
            name = names[first[os.path.normcase(entries[i][0])]]
            named[i] = os.path.join(entries[i][1], name)

    rows = []
    seen_links = set()
    seen_sources = set()
    for i, (src, parent, link) in enumerate(entries):
        if not parent:
            rows.append((src, "", "no target folder for this row"))
            continue
        if link is None:
            link = named[i]

        src_key = (os.path.normcase(src), os.path.normcase(parent))
        status = _check(src, link, parent)
        if status == READY:
            key = os.path.normcase(link)
            if src_key in seen_sources:
                status = "same source as an earlier row"
            elif key in seen_links:
                status = "same junction path as an earlier row"
            seen_links.add(key)
        seen_sources.add(src_key)
        rows.append((src, link, status))
    return rows


def unique_names(sources):
    """한 폴더 안에 만들 정션들의 이름. 기본은 원본 폴더 이름(`basename`).

    대소문자 무시로 이름이 겹치는 소스들만 상위 폴더 이름을 `_` 로 앞에 이어 붙인다
    (`D:/ProjA/Content` -> `ProjA_Content`). 그래도 겹치면 한 단계씩 더 올라가고, 경로 성분을
    다 써도 같으면(같은 폴더를 두 번 담은 경우) `_2`, `_3` 을 붙인다. 겹치지 않는 소스의 이름은
    바뀌지 않는다. 입력과 같은 순서로 돌려준다.
    """
    parts = [_name_parts(src) for src in sources]
    depth = [1] * len(sources)
    while True:
        names = ["_".join(p[-d:]) for p, d in zip(parts, depth)]
        groups = {}
        for i, name in enumerate(names):
            groups.setdefault(name.lower(), []).append(i)
        dup = [idx for idx in groups.values() if len(idx) > 1]
        if not dup:
            return names
        progressed = False
        for idx in dup:
            for i in idx:
                if depth[i] < len(parts[i]):
                    depth[i] += 1
                    progressed = True
        if not progressed:
            break

    # 성분을 다 썼는데도 같다 - 번호를 붙여 구분한다(첫 행은 그대로).
    taken = set(n.lower() for n in names)
    for idx in dup:
        for n, i in enumerate(idx[1:], start=2):
            cand = "{0}_{1}".format(names[i], n)
            while cand.lower() in taken:
                n += 1
                cand = "{0}_{1}".format(names[i], n)
            names[i] = cand
            taken.add(cand.lower())
    return names


def _name_parts(src):
    """경로 성분(이름에 쓸 수 있는 꼴). `D:/ProjA/Content` -> ["D", "ProjA", "Content"]."""
    norm = os.path.normpath(src).rstrip("\\/")
    parts = [p for p in norm.replace("/", "\\").split("\\") if p]
    parts = [p.rstrip(":") for p in parts]              # 드라이브 "D:" -> "D"
    return [p for p in parts if p] or [norm]


def _check(src, link, parent):
    if not os.path.exists(src):
        return "source does not exist"
    if not os.path.isdir(src):
        return "source is a file - a junction links a folder"
    if not os.path.isdir(parent):
        return "target folder does not exist"
    if os.path.lexists(link):
        if is_junction(link):
            tgt = junction_target(link)
            if os.path.normcase(os.path.normpath(tgt)) == os.path.normcase(src):
                return "already a junction to this source"
            return "a junction to another folder is already there"
        return "a folder or file with this name is already there"
    if _same_or_inside(link, src):
        # 합법이지만 자기 자신을 품는 순환이 된다(트리를 끝없이 내려간다) - 막는다.
        return "junction would be inside its own source (loop)"
    return READY


def _same_or_inside(path, folder):
    """path 가 folder 자신이거나 그 안인가(대소문자 무시)."""
    p = os.path.normcase(os.path.normpath(path))
    f = os.path.normcase(os.path.normpath(folder))
    return p == f or p.startswith(f + os.sep)


def create_junction(link, source):
    """`cmd /c mklink /J link source` 를 실행한다. 반환 (ok, message).

    콘솔 창을 띄우지 않는다(CREATE_NO_WINDOW). cmd 의 출력은 OEM 코드페이지(한국어 윈도우는
    cp949)라 `oem` 으로 읽는다. 성공 여부는 반환 코드가 아니라 **만들어진 뒤 정션인지** 로 본다.
    """
    if os.name != "nt":
        return False, "junctions are a Windows feature"
    try:
        proc = subprocess.run(
            ["cmd", "/c", "mklink", "/J", link, source],
            capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
    except OSError as exc:
        return False, str(exc)

    out = _decode(proc.stdout) or _decode(proc.stderr)
    if is_junction(link):
        return True, out
    return False, out or "mklink failed (code {0})".format(proc.returncode)


def remove_junction(link):
    """정션 **링크만** 지운다. 반환 (ok, message). 정션이 아니면 아무것도 하지 않는다.

    `os.rmdir` 는 정션에서 링크만 걷어내고 타깃 폴더의 내용은 건드리지 않는다.
    빈 실제 폴더도 지울 수 있는 명령이므로 **먼저 정션인지 확인**한다 - 그게 이 함수의 전부다.
    """
    if not os.path.lexists(link):
        return False, "does not exist"
    if not is_junction(link):
        return False, "not a junction - left untouched"
    target = junction_target(link)
    try:
        os.rmdir(link)
    except OSError as exc:
        return False, str(exc)
    if os.path.lexists(link):
        return False, "still exists after removal"
    if target and not os.path.isdir(target):
        # 타깃이 원래 없던(끊긴) 정션일 수 있다 - 지운 것은 링크뿐이라는 것만 알린다.
        return True, "removed (target {0} was not reachable)".format(target)
    return True, "removed - original folder kept: {0}".format(target)


def find_junctions(folder, recursive=False, max_depth=0):
    """folder 아래의 정션 경로 목록(이름순). recursive 면 하위 폴더도 훑는다(정션 안은 안 들어간다).

    max_depth : recursive 일 때 내려갈 깊이(0 = 제한 없음). folder 바로 아래가 1.
    """
    found = []
    stack = [(folder, 1)]
    while stack:
        cur, depth = stack.pop()
        try:
            entries = sorted(os.scandir(cur), key=lambda e: e.name.lower())
        except OSError:
            continue
        for e in entries:
            try:
                if not e.is_dir():
                    continue
                st = e.stat(follow_symlinks=False)
            except OSError:
                continue
            if (st.st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT
                    and st.st_reparse_tag == stat.IO_REPARSE_TAG_MOUNT_POINT):
                found.append(e.path)
                continue                         # 정션 안은 타깃의 내용 - 훑지 않는다
            if recursive and (not max_depth or depth < max_depth):
                stack.append((e.path, depth + 1))
    return sorted(found, key=lambda p: p.lower())


def _decode(data):
    if not data:
        return ""
    for enc in ("oem", "utf-8"):
        try:
            return data.decode(enc).strip()
        except (LookupError, UnicodeDecodeError):
            continue
    return data.decode("utf-8", errors="replace").strip()
