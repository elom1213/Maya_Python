# Python Script by Ji Hun Park
# last Update date : 2026-11-05
# A00210_FileManager - Sync 탭: PC 매니페스트 비교 (순수 함수, UI/DCC 비의존)
#
# v01.47 : 계획서 4-4. 한 루트의 모든 PC 매니페스트를 나란히 놓고 파일마다 PC 별 상태를 정한다.
#
#   OK         모든 PC 가 같은 해시
#   Missing    다른 PC 에 있고 이 PC 에 없다                      → 받아 와야 함
#   Outdated   이 PC 해시가 다른 PC 의 history 안에 있다          → 받아 와야 함
#   Ahead      다른 PC 가 없거나 옛것 - 이 PC 것이 최신            → 보내야 함
#   Only here  이 PC 에만 있다                                    → 보내야 함
#   Conflict   서로의 해시가 서로의 history 에 없다(양쪽이 따로 고침)  → 사람이 판단
#
# 판정은 **해시 + history**, 시각은 보조. history 로 앞뒤를 모를 때 어느 한쪽이라도 처음 본 파일(history 1개)이면
# 수정 시각이 큰 쪽을 '아마 최신' 으로 보고 uncertain=True(화면에 '?'). 둘 다 이력이 쌓였는데 모르면 Conflict.

from . import sync_settings as ss

OK = "OK"
MISSING = "Missing"
OUTDATED = "Outdated"
AHEAD = "Ahead"
ONLY_HERE = "Only here"
CONFLICT = "Conflict"

ALL_STATUSES = (MISSING, OUTDATED, CONFLICT, AHEAD, ONLY_HERE, OK)
# 받아 와야 하는 것 / 보내야 하는 것
NEED_GET = (MISSING, OUTDATED)
NEED_SEND = (AHEAD, ONLY_HERE)


class FileStatus(object):
    __slots__ = ("rel", "entries", "pc_status", "uncertain", "status", "this_pc")

    def __init__(self, rel, entries):
        self.rel = rel                  # 표시용 상대 경로(처음 본 표기)
        self.entries = entries          # {pc: entry dict}  (없는 PC 는 키 없음)
        self.pc_status = {}             # {pc: status}
        self.uncertain = {}             # {pc: bool}
        self.status = OK                # this_pc 기준 상태
        self.this_pc = ""

    # -- 요약 열(PC 가 많을 때)
    def pcs_with(self, *statuses):
        return [pc for pc, s in self.pc_status.items() if s in statuses]

    def latest_on(self):
        return self.pcs_with(OK, AHEAD, ONLY_HERE)

    def is_problem(self):
        """어느 PC 에서든 어긋났는가(Compare: All PCs)."""
        return any(s != OK for s in self.pc_status.values())

    def __repr__(self):
        return "FileStatus({0!r}, {1}, {2})".format(self.rel, self.status, self.pc_status)


def _hist(entry):
    h = list(entry.get("history") or [])
    sha = entry.get("sha256")
    if sha and (not h or h[-1] != sha):
        h.append(sha)
    return h


def _decide(entries, pcs):
    """{pc: entry} -> ({pc: status}, {pc: uncertain})."""
    present = [pc for pc in pcs if pc in entries]
    shas = {pc: entries[pc].get("sha256") for pc in present}
    hists = {pc: _hist(entries[pc]) for pc in present}

    def superseded(pc):
        h = shas[pc]
        return any(shas[q] != h and h in hists[q] for q in present if q != pc)

    status, unsure = {}, {}
    for pc in pcs:
        if pc not in entries:
            status[pc] = MISSING
            unsure[pc] = False

    # 1) 확실히 옛것
    heads = [pc for pc in present if not superseded(pc)]
    for pc in present:
        if pc not in heads:
            status[pc] = OUTDATED
            unsure[pc] = False

    # 2) 머리(head)끼리 해시가 다르면 - 이력으로는 앞뒤를 모른다
    for pc in heads:
        others = [q for q in heads if q != pc and shas[q] != shas[pc]]
        if not others:
            continue
        first_sight = len(hists[pc]) <= 1 or any(len(hists[q]) <= 1 for q in others)
        if first_sight:
            mine = entries[pc].get("mtime_ns") or 0
            newest = max(entries[q].get("mtime_ns") or 0 for q in others)
            status[pc] = OUTDATED if mine < newest else AHEAD
            unsure[pc] = True
        else:
            status[pc] = CONFLICT
            unsure[pc] = False

    # 3) 남은 머리 = 최신. 다른 PC 가 없거나 옛것이면 Ahead(보내야 함), 혼자면 Only here, 다 같으면 OK
    for pc in heads:
        if pc in status:
            continue
        unsure[pc] = False
        if len(present) == 1:
            status[pc] = ONLY_HERE if len(pcs) > 1 else OK
            continue
        behind = [q for q in pcs if q != pc and status.get(q) in (MISSING, OUTDATED)]
        status[pc] = AHEAD if behind else OK
    return status, unsure


def compare(manifests, this_pc, excluded=(), ignore=()):
    """manifests {pc: manifest} -> [FileStatus] (경로순).

    excluded / ignore 는 비교 때도 거른다 - 제외 목록을 고친 직후 다른 PC 가 아직 다시 스캔하지 않았어도 결과가 맞다."""
    pcs = sorted(manifests.keys(), key=lambda p: (p != this_pc, p.lower()))
    rows = {}
    for pc in pcs:
        for rel, entry in ((manifests[pc] or {}).get("files") or {}).items():
            if not isinstance(entry, dict):
                continue
            if ss.is_excluded(rel, excluded) or ss.is_ignored(rel, ignore):
                continue
            key = ss.rel_key(rel)
            row = rows.get(key)
            if row is None:
                row = rows[key] = FileStatus(rel, {})
            row.entries[pc] = entry

    out = []
    for key in sorted(rows):
        row = rows[key]
        row.pc_status, row.uncertain = _decide(row.entries, pcs)
        row.this_pc = this_pc
        row.status = row.pc_status.get(this_pc, MISSING) if this_pc in manifests else MISSING
        out.append(row)
    return out


class DirStatus(object):
    """빈 폴더 하나(v01.51). 어떤 PC 에서든 파일이 없는 폴더 - 파일 비교(compare)로는 안 보이는 것."""
    __slots__ = ("rel", "present", "lacking", "pc_status", "status")

    def __init__(self, rel):
        self.rel = rel              # 끝 '/' 없음
        self.present = []           # 이 폴더가 있는 PC
        self.lacking = []           # 스캔했는데 이 폴더가 없는 PC
        self.pc_status = {}
        self.status = OK

    def is_problem(self):
        return bool(self.lacking)


def empty_dirs(manifests, this_pc, excluded=(), ignore=(), rows=None):
    """빈 폴더 비교 -> [DirStatus] (경로순).

    - 어느 PC 의 manifest['empty_dirs'](가장 안쪽 빈 폴더) 에든 있는 폴더 중, **어느 PC 에도 그 아래 파일이 없고**
      다른 빈 폴더의 위 폴더도 아닌 것만(그런 폴더는 경로로 따라 나온다).
    - 그 폴더가 있다 = 그 PC 의 empty_dirs 에 그것 또는 그 아래 폴더가 있다(빈 폴더 경로의 위 폴더는 당연히 있다). 'empty_dirs' 키가 없는 옛 매니페스트(v01.50 이전 스캔)는 모른다 - 판정에서 뺀다.
    - 있는 PC 는 OK(빠진 PC 가 있으면 Only here), 없는 PC 는 Missing.
    rows : compare() 결과(주면 그 파일 경로로 '아래 파일 있음' 을 판단, 없으면 매니페스트에서 다시 모음)."""
    known = [pc for pc in manifests if isinstance((manifests[pc] or {}).get("empty_dirs"), list)]
    if not known:
        return []
    has_files = set()
    rels = [r.rel for r in rows] if rows is not None else [
        rel for m in manifests.values() for rel in ((m or {}).get("files") or {})
        if not (ss.is_excluded(rel, excluded) or ss.is_ignored(rel, ignore))]
    for rel in rels:
        d = rel.rpartition("/")[0]
        while d and d.lower() not in has_files:
            has_files.add(d.lower())
            d = d.rpartition("/")[0]
    found = {}
    have = {}                        # {pc: 그 PC 에 있는 폴더(빈 폴더와 그 위 폴더 전부, 소문자)}
    for pc in known:
        own = have.setdefault(pc, set())
        for d in manifests[pc]["empty_dirs"]:
            d = ss.norm_rel(d).rstrip("/")
            if not d:
                continue
            p = d
            while p:
                own.add(p.lower())
                p = p.rpartition("/")[0]
            if d.lower() in has_files:
                continue
            if ss.is_excluded(d + "/", excluded) or ss.is_ignored(d + "/", ignore):
                continue
            found.setdefault(d.lower(), DirStatus(d))
    # 다른 빈 폴더의 위 폴더는 줄로 만들지 않는다(그 아래 줄이 있다)
    parents = set()
    for low in found:
        p = low.rpartition("/")[0]
        while p:
            parents.add(p)
            p = p.rpartition("/")[0]
    order = sorted(known, key=lambda p: (p != this_pc, p.lower()))
    out = []
    for low in sorted(found):
        if low in parents:
            continue
        row = found[low]
        row.present = [p for p in order if low in have[p]]
        row.lacking = [p for p in order if p not in row.present]
        for p in order:
            row.pc_status[p] = MISSING if p in row.lacking else (ONLY_HERE if row.lacking else OK)
        row.status = row.pc_status.get(this_pc, MISSING)
        out.append(row)
    return out


def summarize(rows, pc=None):
    """{status: count} - pc 를 주면 그 PC 기준, 아니면 각 행의 status."""
    counts = dict((s, 0) for s in ALL_STATUSES)
    for r in rows:
        s = r.pc_status.get(pc, MISSING) if pc else r.status
        counts[s] = counts.get(s, 0) + 1
    return counts
