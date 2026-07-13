# -*- coding: utf-8 -*-

# last Update date : 2026-06-29
# Python Script by Ji Hun Park

# KWI Constraint creator
# 언리얼 Kawaii Physics 의 Bone Constraints Data Asset 내용을 생성한다.
# 브래킷 패턴 두 줄(Chain A / Chain B)을 받아 인덱스 1:1 zip 으로 본 쌍을 만들고,
# 각 쌍을 (BoneReference1=...,BoneReference2=...) 항목으로 치환해 한 줄 문자열로 합친다.

import re
import itertools

from .template_engine import TemplateEngine
from Framework.core.path_manager import PathManager


class ConstraintCreator:
    def __init__(self):
        self.pm = PathManager(
            __file__,
            read_dir="0010_src",
            write_dir="0020_out",
        )
        self.extension = "py"

        self.read_entry = self.pm.path(
            "read", f"A0202_Src_LDA_constraint_entry.{self.extension}"
        )
        self.write_out = self.pm.path(
            "write", f"A020_LDA_constraint_out.{self.extension}"
        )

    # ------------------------------------------------------------------
    # pattern expansion

    @staticmethod
    def expand_pattern(pattern):
        # "dyn_asset_side_0[1-7]_0[1-5]" -> ['dyn_asset_side_01_01', ... , 'dyn_asset_side_07_05']
        # [a-b] 는 정수 a..b 로 치환한다. 한쪽 경계에 리딩 0 이 있으면(예: [01-10])
        # 두 경계 폭의 최대값으로 제로패딩한다([01-10] -> 01,02,...,10). 리딩 0 이
        # 없으면 패딩 없음([1-10] -> 1..10) — 기존 동작 유지.
        # 다중 브래킷은 왼쪽이 바깥 루프(가장 느리게 변함) = itertools.product 기본 동작.
        pattern = (pattern or "").strip()
        if not pattern:
            return []

        # 리터럴 조각과 [a-b] 토큰을 순서대로 분해
        segs = re.split(r"(\[\d+-\d+\])", pattern)

        ranges = []
        # 각 브래킷의 제로패딩 폭(0 = 패딩 없음). ranges 와 순서가 같다.
        widths = []
        # template_parts: 리터럴 문자열 또는 None(브래킷 자리)
        template_parts = []
        for seg in segs:
            m = re.fullmatch(r"\[(\d+)-(\d+)\]", seg)
            if m:
                a_str, b_str = m.group(1), m.group(2)
                a, b = int(a_str), int(b_str)
                step = 1 if a <= b else -1
                ranges.append(range(a, b + step, step))
                # 한쪽 경계라도 리딩 0 이 있으면 두 경계 폭의 최대값으로 패딩.
                has_lead_zero = ((len(a_str) > 1 and a_str[0] == "0") or
                                 (len(b_str) > 1 and b_str[0] == "0"))
                widths.append(max(len(a_str), len(b_str)) if has_lead_zero else 0)
                template_parts.append(None)
            else:
                template_parts.append(seg)

        if not ranges:
            return [pattern]

        results = []
        for combo in itertools.product(*ranges):
            values = iter(zip(combo, widths))  # 브래킷 순서대로 (값, 패딩폭)
            parts = []
            for p in template_parts:
                if p is None:
                    val, width = next(values)
                    parts.append(str(val).zfill(width))  # width=0 이면 그대로
                else:
                    parts.append(p)
            results.append("".join(parts))
        return results

    def build_pairs(self, pattern_a, pattern_b):
        # 두 패턴을 펼쳐 인덱스 1:1 로 zip. 길이가 다르면 명확한 에러.
        list_a = self.expand_pattern(pattern_a)
        list_b = self.expand_pattern(pattern_b)

        if not list_a or not list_b:
            raise ValueError("Both Chain A and Chain B must be non-empty.")

        if len(list_a) != len(list_b):
            raise ValueError(
                "Chain A and Chain B expand to different counts "
                f"(A={len(list_a)}, B={len(list_b)}). They must match for 1:1 pairing."
            )

        return list(zip(list_a, list_b))

    # ------------------------------------------------------------------
    # text build

    def build_text(self, pattern_rows):
        # pattern_rows : [(chain_a, chain_b), ...]  (여러 쌍을 순서대로 합친다)
        # -> "((BoneReference1=...,BoneReference2=...),(...), ...)"
        with open(self.read_entry, "r", encoding="utf-8") as f:
            entry_tpl = f.read().strip()

        all_pairs = []
        for chain_a, chain_b in pattern_rows:
            # 빈 행(둘 다 공백)은 건너뛴다. 한쪽만 비면 build_pairs 가 에러를 낸다.
            if not (chain_a or "").strip() and not (chain_b or "").strip():
                continue
            all_pairs.extend(self.build_pairs(chain_a, chain_b))

        if not all_pairs:
            raise ValueError("No bone pairs to generate. Fill at least one pair.")

        entries = [
            TemplateEngine.apply(entry_tpl, {"BONE_1": a, "BONE_2": b})
            for a, b in all_pairs
        ]

        return "(" + ",".join(entries) + ")"

    def create_file(self, pattern_rows):
        text = self.build_text(pattern_rows)
        self.pm.ensure_dir(self.write_out)
        with open(self.write_out, "w", encoding="utf-8") as f:
            f.write(text)
        return self.write_out, text
