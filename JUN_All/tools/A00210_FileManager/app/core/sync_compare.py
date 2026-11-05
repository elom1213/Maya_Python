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


def summarize(rows, pc=None):
    """{status: count} - pc 를 주면 그 PC 기준, 아니면 각 행의 status."""
    counts = dict((s, 0) for s in ALL_STATUSES)
    for r in rows:
        s = r.pc_status.get(pc, MISSING) if pc else r.status
        counts[s] = counts.get(s, 0) + 1
    return counts
