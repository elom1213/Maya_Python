---
name: wip-a00350-arraycreator
description: A00350_ArrayCreator — new in-Maya PySide tool; TSL objects -> UE Control Rig Item Array node text (clipboard + 0020_out) (v01.00)
metadata: 
  node_type: memory
  type: project
  originSessionId: 746d699d-9d82-44da-b966-14caefd575fd
---

DONE (verified + pushed Dnable/dev, commit dc0225d), v01.00: NEW tool A00350_ArrayCreator. Guide doc `JUN_All/docs/A00350_ArrayCreator.md` created.

**Request:** list Maya objects in a TSL, generate a UE Control Rig **Item Array** node (RigVMDispatchNode, `TArray<FRigElementKey>`) whose elements are the listed objects in order, copy the text to clipboard for direct paste into UE, and also write the file. Per-element **Type** selectable (ERigElementType: None/Bone/Null/Control/Curve/Reference/Connector/Socket), default Bone. Reference templates in `app/core/0010_src/`: `A0010_Src_Array_node_v01.py` (canonical = single node, 6 Bone elements, joints dyn_pants_chain_*), `A0010_Src_Array_node_v02.py` (a type CATALOG = 8 separate 1-element nodes, one per type — NOT a mixed node). Actively referenced A00080_KWI_creator_V03 + A00260_ConstraintConverter (PathManager 0010_src/0020_out + TemplateEngine {{KEY}} + NodeBuilder decl/def/subpins + clipboard).

**Design decision:** global Type combo (applies to ALL elements), default Bone — faithful to v01 (homogeneous) and the wording; v02 is just a catalog, not evidence of mixed-type need. Per-element could be a future enhancement.

**Structure (cloned A00260 arch):**
- `app/core/0010_src/`: `A0001_Src_array_node.py` (full node, {{NODE}}/{{ASSET}}/{{NODE_TITLE}}/{{POS_X/Y}}/{{VALUE_DECL}}/{{VALUE_DEF}}/{{SUBPINS}}), `A0002_Src_element_decl.py` ({{IDX}}), `A0003_Src_element_def.py` ({{IDX}}/{{TYPE}}/{{NAME}}). Reference v01/v02 kept in same dir.
- `app/core/`: `template_engine.py` ({{KEY}} replace), `tool_path.py` (CreatorPaths dataclass), `node_builder.py` (NodeBuilder + ArrayOptions + ELEMENT_TYPES + DEFAULT_* consts; ASSET/NODE from v01, node just needs uniqueness on paste per A00260 note), `array_creator.py` (ArrayCreator orchestrator, PathManager, writes `0020_out/A001_array_node_out.py`, `_element_name` strips DAG path to leaf).
- `app/ui/main_window.py`: TSL (`JUN_mod_tsl_qt_v01`, Select/Add on, show_sort off) + Element Type combo (default Bone) + Node Title lineedit (default "Test_array") + "Create Array Node -> Copy to Clipboard" + log. Local-imports ArrayCreator/ArrayOptions for reload safety (A00260 pattern).
- `launch.py`/`__init__.py`/`__dragDrop_A00350.py` (shelf "ArrayCreator"), `app/config/version.py` (01.00). Icon svg + 32px png (teal `[ ]` brackets + light rows), PIL 8x supersample.

**VERIFIED:** round-trip test — building the 6 v01 joints with defaults (Bone/Test_array/ItemArray_7/pos) produces output **byte-identical to v01** (204 lines). Variant test (3 elems, Socket, custom title) correct. All modules py_compile. NOTE: template .py files in 0010_src are non-Python text (data), never imported — safe (same as A00080/A00260).

**Next:** user verifies in Maya (list joints, pick type, Create → paste into Control Rig graph). Then push Dnable/dev + WORKLOG + guide doc `JUN_All/docs/A00350_ArrayCreator.md`. Stage A00350 paths explicitly. See [[push-includes-tool-guide-docs]], [[worklog-maintenance]], [[prefer-pyside-for-new-tools]], [[wip-a00360-sorttool]] (built same day).
