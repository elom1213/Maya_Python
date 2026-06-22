# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-06-22
# A00250_SceneMemo - MemoStore
#
# 메모를 씬 내부 storage 노드(network)에 JSON 으로 보관/관리한다.
# 키는 노드 UUID — 리네임/부모변경에도 메모가 끊기지 않는다.
# JSON 은 string 어트리뷰트에 들어가므로 한국어(유니코드)가 안전하게 저장된다.

import json
import time

import maya.cmds as cmds


STORE_NODE = "JUN_memo_store"   # 씬에 만드는 storage 노드 이름
DATA_ATTR = "junMemoData"       # JSON 을 담는 string 어트리뷰트
SCHEMA_VERSION = 1


class MemoStore:
    """씬 내부 storage 노드 ↔ 메모 JSON 의 CRUD."""

    # --------------------------------------------------
    # storage node
    # --------------------------------------------------

    def _ensure_store(self):
        """storage 노드와 데이터 어트리뷰트를 보장하고 노드명을 반환."""
        nodes = cmds.ls(STORE_NODE, type="network") or []

        if nodes:
            node = nodes[0]
        else:
            node = cmds.createNode("network", name=STORE_NODE)

        if not cmds.attributeQuery(DATA_ATTR, node=node, exists=True):
            cmds.addAttr(node, longName=DATA_ATTR, dataType="string")

        # 실수로/Optimize Scene Size 로 삭제되지 않도록 노드를 잠근다 (어트리뷰트 set 은 여전히 가능).
        if not cmds.lockNode(node, query=True, lock=True)[0]:
            cmds.lockNode(node, lock=True)

        return node

    def _read_raw(self):
        node = self._ensure_store()
        raw = cmds.getAttr(node + "." + DATA_ATTR) or ""

        if not raw:
            return {"version": SCHEMA_VERSION, "memos": {}}

        try:
            data = json.loads(raw)
        except Exception:
            data = {"version": SCHEMA_VERSION, "memos": {}}

        data.setdefault("version", SCHEMA_VERSION)
        data.setdefault("memos", {})
        return data

    def _write_raw(self, data):
        node = self._ensure_store()
        text = json.dumps(data, ensure_ascii=False)
        cmds.setAttr(node + "." + DATA_ATTR, text, type="string")

    # --------------------------------------------------
    # read
    # --------------------------------------------------

    def get_data(self):
        """원본 dict 반환 (export 용)."""
        return self._read_raw()

    def list_memos(self):
        """[{uuid, node(현재명 or None), missing, memo, ts, name_hint}] (최신순)."""
        data = self._read_raw()
        out = []

        for uuid, rec in data["memos"].items():
            nodes = cmds.ls(uuid) or []
            cur = nodes[0] if nodes else None
            out.append({
                "uuid": uuid,
                "node": cur,
                "missing": cur is None,
                "memo": rec.get("memo", ""),
                "ts": rec.get("ts", 0),
                "name_hint": rec.get("name_hint", ""),
            })

        out.sort(key=lambda r: r.get("ts", 0), reverse=True)
        return out

    # --------------------------------------------------
    # write
    # --------------------------------------------------

    def set_memo(self, uuid, memo, name_hint=None):
        """메모 추가/수정 (upsert)."""
        data = self._read_raw()
        rec = data["memos"].get(uuid, {})
        rec["memo"] = memo
        rec["ts"] = int(time.time())
        if name_hint is not None:
            rec["name_hint"] = name_hint
        data["memos"][uuid] = rec
        self._write_raw(data)

    def add_selected(self):
        """선택된 노드들을 빈 메모로 등록. (추가개수, 영향받은 uuid 목록) 반환."""
        sel = cmds.ls(selection=True, long=True) or []
        if not sel:
            return 0, []

        data = self._read_raw()
        added = 0
        touched = []

        for node in sel:
            uuids = cmds.ls(node, uuid=True) or []
            if not uuids:
                continue
            uuid = uuids[0]

            if uuid not in data["memos"]:
                short = node.split("|")[-1]
                data["memos"][uuid] = {
                    "memo": "",
                    "ts": int(time.time()),
                    "name_hint": short,
                }
                added += 1
            touched.append(uuid)

        if added:
            self._write_raw(data)

        return added, touched

    def remove(self, uuid):
        data = self._read_raw()
        if uuid in data["memos"]:
            del data["memos"][uuid]
            self._write_raw(data)
            return True
        return False

    def clean_orphans(self):
        """현재 씬에 없는 노드(UUID)의 메모를 제거. 제거 개수 반환."""
        data = self._read_raw()
        removed = 0

        for uuid in list(data["memos"].keys()):
            if not (cmds.ls(uuid) or []):
                del data["memos"][uuid]
                removed += 1

        if removed:
            self._write_raw(data)

        return removed

    def merge(self, incoming, overwrite=True):
        """다른 데이터 dict 를 현재 store 에 병합. (added, updated) 반환."""
        data = self._read_raw()
        added = 0
        updated = 0

        for uuid, rec in (incoming.get("memos", {}) or {}).items():
            if uuid in data["memos"]:
                if overwrite:
                    data["memos"][uuid] = rec
                    updated += 1
            else:
                data["memos"][uuid] = rec
                added += 1

        self._write_raw(data)
        return added, updated

    # --------------------------------------------------
    # scene helpers
    # --------------------------------------------------

    def select_in_scene(self, uuids):
        """UUID(단일 또는 목록) 로 노드들을 찾아 선택. 찾은 노드 개수 반환."""
        if isinstance(uuids, str):
            uuids = [uuids]

        nodes = []
        for u in uuids:
            nodes.extend(cmds.ls(u) or [])

        if nodes:
            cmds.select(nodes, replace=True)
            return len(nodes)

        cmds.select(clear=True)
        return 0
