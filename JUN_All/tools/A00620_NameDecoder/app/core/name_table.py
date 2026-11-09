# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-11-09
# A00620_NameDecoder - 찾은 이름 표 내보내기 (마야 불필요)
#
#   export_list(entries, path)      : .csv (UTF-8 BOM - 엑셀에서 일본어가 깨지지 않게) 또는 .json
#   map_pieces(entries)             : 번역표 칸 = 이름 안의 풀린 조각(まばたき · 口左 · ' ' · 1 …) 중복 없이, 처음 나온 순서
#   export_map_template(entries, path, existing=None) : {조각: ""} json - Rename to ASCII 탭의 번역표 출발점

import csv
import io
import json

from Framework.core import fbx_name

LIST_COLUMNS = ("decoded", "raw", "type", "owner")


def entry_row(entry):
    return {
        "decoded": entry.decoded,
        "raw": entry.raw,
        "type": entry.type_label(),
        "owner": entry.owner,
    }


def export_list(entries, path):
    """.json 이면 [{decoded, raw, type, owner}], 그 밖은 csv. 쓴 행 수."""
    rows = [entry_row(e) for e in entries]
    if path.lower().endswith(".json"):
        with io.open(path, "w", encoding="utf-8") as f:
            f.write(json.dumps(rows, ensure_ascii=False, indent=2))
    else:
        with io.open(path, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=LIST_COLUMNS)
            writer.writeheader()
            writer.writerows(rows)
    return len(rows)


def map_pieces(entries):
    """이름들 안의 풀린 조각(FBXASC 구간 하나 = 조각 하나), 중복 없이 처음 나온 순서."""
    seen = []
    known = set()
    for e in entries:
        for _raw, text, kind in fbx_name.decode_parts(e.raw):
            if kind == "decoded" and text not in known:
                known.add(text)
                seen.append(text)
    return seen


def export_map_template(entries, path, existing=None):
    """{조각: 기존 번역 또는 ""} 를 json 으로. 쓴 칸 수."""
    existing = existing or {}
    data = {}
    for piece in map_pieces(entries):
        data[piece] = existing.get(piece, "")
    with io.open(path, "w", encoding="utf-8") as f:
        f.write(json.dumps(data, ensure_ascii=False, indent=2))
    return len(data)
