# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-28
# A00340_SelectionTool - 네임스페이스 교체 (v01.18, 계획서 docs/plans/A00340_SelectionTool_namespace_remap_plan.md)
#
# 프로파일 json 의 오브젝트 이름은 캡처한 그대로 둔다. 선택할 때만 {원래 ns: 대상 ns} 매핑으로 바꿔 끼워
# 같은 리그의 다른 아바타(예: test:ZIHAN:Cage -> test:IVI:Cage)를 고른다.
#
#   - 교체는 **네임스페이스가 정확히 같을 때만** - 'a:b:obj' 의 ns 는 마지막 ':' 앞 'a:b'. 부분 문자열은 안 바꾼다.
#   - 이름에 '|' 부분 경로가 섞이면(cmds.ls 가 중복 이름에 주는 'grp|ns:obj') 마디마다 같은 규칙.
#   - '' (네임스페이스 없음) 도 원래 ns 가 될 수 있다.
# 위쪽은 순수 로직(마야 없이 시험), 아래 '씬 조회' 만 maya.cmds 를 lazy 로 쓴다.

from collections import Counter, OrderedDict


# ================================================================ 순수 로직

def split_ns(name):
    """'a:b:obj' -> ('a:b', 'obj'), 'obj' -> ('', 'obj')."""
    head, sep, short = name.rpartition(":")
    return (head, short) if sep else ("", name)


def remap_name(name, mapping):
    """mapping = {원래 ns: 대상 ns}. '|' 마디마다 ns 가 mapping 에 정확히 있으면 바꾼다."""
    if not mapping:
        return name
    parts = []
    for part in name.split("|"):
        if not part:
            parts.append(part)
            continue
        ns, short = split_ns(part)
        if ns in mapping:
            target = mapping[ns]
            part = (target + ":" + short) if target else short
        parts.append(part)
    return "|".join(parts)


def remap_names(names, mapping):
    """순서를 지켜 remap_name."""
    return [remap_name(n, mapping) for n in names]


def reverse_mapping(mapping):
    """{대상: 원래}. 대상이 겹치면 첫 것을 쓴다."""
    out = OrderedDict()
    for src, dst in (mapping or {}).items():
        out.setdefault(dst, src)
    return dict(out)


def effective(mapping):
    """실제로 바뀌는 쌍만 (원래 == 대상 은 뺀다)."""
    return dict((s, d) for s, d in (mapping or {}).items() if s != d)


def profile_objects(data):
    """프로파일 dict 의 모든 버튼 objects (순서 · 중복 그대로)."""
    out = []
    for cat in (data or {}).get("categories", []):
        for btn in cat.get("buttons", []):
            out.extend(btn.get("objects", []))
    return out


def object_namespaces(names):
    """이름 목록 -> Counter{ns: 개수}. '|' 경로는 마지막 마디의 ns."""
    counter = Counter()
    for name in names:
        counter[split_ns(name.split("|")[-1])[0]] += 1
    return counter


def profile_namespaces(data):
    """프로파일 dict -> Counter{ns: 오브젝트 수} (네임스페이스 없음은 '')."""
    return object_namespaces(profile_objects(data))


def short_names_in(names, ns):
    """names 중 마지막 마디의 ns 가 ns 인 것들의 짧은 이름 (순서 유지, 중복 제거)."""
    out = []
    for name in names:
        n, short = split_ns(name.split("|")[-1])
        if n == ns and short not in out:
            out.append(short)
    return out


# ================================================================ 씬 조회 (maya.cmds)

def _cmds():
    import maya.cmds as cmds
    return cmds


_SKIP_NAMESPACES = ("UI", "shared")


def scene_namespaces():
    """씬의 모든 네임스페이스 (중첩 포함, 'UI' · 'shared' 제외)."""
    cmds = _cmds()
    found = cmds.namespaceInfo(":", listOnlyNamespaces=True, recurse=True) or []
    return [ns for ns in found if ns not in _SKIP_NAMESPACES]


def candidates(names, source_ns):
    """source_ns 오브젝트들의 짧은 이름이 씬의 각 네임스페이스에 몇 개 있나.

    반환 [(ns, found, total)] - found > 0 인 것만, found 내림차순 -> ns 이름순. source_ns 자신도 (있으면) 들어간다.
    source_ns 가 '' 이면 네임스페이스 없는 자리('')도 후보로 센다.
    """
    cmds = _cmds()
    shorts = short_names_in(names, source_ns)
    total = len(shorts)
    if not total:
        return []
    out = []
    pool = scene_namespaces() + [""]
    for ns in pool:
        prefix = ns + ":" if ns else ""
        found = sum(1 for s in shorts if cmds.objExists(prefix + s))
        if found:
            out.append((ns, found, total))
    out.sort(key=lambda t: (-t[1], t[0]))
    return out
