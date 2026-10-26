# -*- coding: utf-8 -*-
# A00145_RigConnect - version info

# 01.66  Connect > Connect by Rule : rule `JALI 22 Viseme` + the A0020 DUMMY_OUT_COARTIC names
#        MMM WA_PEDAL YA_PEDAL (LNTD GK FFF already there) - 36 attributes, so DUMMY_OUT_COARTIC
#        connects by the same rule too. Data only, no code change.
# 01.65  Connect > Connect by Rule : rule `JALI 22 Viseme` also carries the 16 angela /
#        A0020_jali_slider_ctl DUMMY_OUT_PHONEMES names (AAA AHH OHH UUU IEE RRR WWW SSS
#        FFF TTH SSH added; Eh Schwa LNTD GK MBP were already there) - 33 attributes, so a
#        DUMMY_OUT_PHONEMES node connects by the same rule. Data only, no code change.
# 01.64  Connect > Connect by Rule : a row whose object name does not resolve to exactly one
#        node (missing, or a duplicate leaf name like grp1|A:dup / grp2|A:dup given as 'A:dup')
#        is skipped as a whole - connectAttr would otherwise silently connect the FIRST
#        match. Resolved nodes are connected by long name. Every skip is logged with its
#        reason (row: not found / ambiguous; attribute: missing on Source / Destination,
#        locked, type mismatch ...), grouped per row and reason.
# 01.63  Connect > Connect by Rule : second rule `JALI 22 Viseme` (app/rules/connect/
#        jali_22_viseme.json) - Jaw, Lip + 20 visemes connected by the same name, Source ->
#        Destination. Data only, no code change.
# 01.53  Match : "Keep Children in Place" checkbox (off by default) - the children of a
#        follower stay at the world place they had before the Match, only the follower
#        moves. Same core as the Mirror tab's checkbox (app/core/keep_children.py).
#        With it on, followers are matched parent first, so a follower that sits under
#        another follower still ends on its own target.
# 01.52  Attribute : every attribute the tool creates (Edit > Copy, Create) is now always
#        visible in the channel box - "Keyable" off means non-keyable DISPLAYED, not
#        hidden. Maya refuses to change the channel box state of a referenced attribute,
#        so it has to be right when the attribute is made. Edit gets a "Show in Channel
#        Box" button to repair attributes that were already created hidden.
# 01.51  Attribute > Set Value (new sub tab, ported from the old Number Tool) : set an
#        attribute the listed objects share, all at once. float / int take Start + Step
#        (in list order, optional Repeat); enum / bool pick an item BY NAME. Preview table,
#        clamp to range, keyed attributes get a key.
# 01.50  Attribute > Create : the attribute list gets the same Shift / Ctrl multi-select +
#        multi-check as Attribute > Edit.
# 01.49  Attribute > Edit : Shift / Ctrl click selects several attributes; clicking the
#        check box of a selected row (or Space) checks / unchecks every selected row.
# 01.48  Attribute > Create : Add / Edit can define enum (named items + default item)
#        and string (default text; the Keyable box becomes "Channel Box") attributes.
# 01.47  Constrain > Constraint : constraint types are checkboxes - Parent + Scale,
#        or any of Point / Orient / Scale together. Types driving the same channels
#        uncheck each other; Point On Poly stays alone.

# 01.56  Attribute > Set Value : "Include Non-Common" checkbox - also list the attributes
#        only some objects have. Every row shows [k/n] (k of the n objects have it, the
#        same mark as Constrain > Target Edit's Targets list). Objects without the
#        attribute are skipped by Set Values; type / range / Get come from the first
#        object that has it. The button is now "List Attributes".
# 01.55  Default window height 900 -> 980 so the whole Match tab fits without a
#        scroll bar.
# 01.54  (Null) placeholder rows are drawn in RED in every list (the shared
#        TSL paints them; Connect > Match calls the same helper). It used to
#        be grey in one list only, and plain text in the Pair tab.

# 01.57  Constrain : the Constraint and Skin Weight sub tabs are merged into one
#        "Constraint" sub tab with a Mode row (Default / Skin Weight). Both screens and
#        their Options are unchanged.
#        Constrain > Transfer gets a Mode row too : Default (the old Transfer - move)
#        and Copy (new) - read each constraint on the left (any type) and set the same
#        constraint on every object on the right, the original stays. Copied : type,
#        targets, driven axes (skip), weights, aim / up / world up, interpType, rest
#        values, pointOnPoly U / V; offsets are re-made (Maintain Offset on) or copied
#        as values (off). Mapping All -> Each Object / Row to Row.

# 01.58  Connect > Transfer Connection (new sub tab) : move the connections of the Source
#        objects' attributes to a Destination that has the same attribute names, upstream
#        (node -> Source) and / or downstream (Source -> node). Source attributes are
#        listed with their connection counts (Channel Box Only / Connected Only), the
#        nodes connected to the checked attributes are listed with check boxes, and
#        Transfer moves only checked attributes x checked nodes. Attributes the
#        Destination lacks turn red and are skipped; a Destination attribute already
#        driven by something else is skipped too. One undo step.

# 01.59  Connect > Connect : "Connect 52 Facial Target" button is gone. Fixed attribute sets
#        are now RULES - json files in app/rules/connect/ (one file = one rule, name /
#        description / attributes / pairs). The Connect by Rule row (combo + Reload +
#        Connect by Rule) lists them; the first rule is "Apple ARKit 52 Facial Target",
#        wired exactly like the old button (objects row by row, same-name attributes,
#        missing ones skipped). New rules = drop a json in the folder, no code change.

# 01.60  Connect > Transfer Connection : "Save as Rule..." (Connected Nodes row). The
#        connections between the CHECKED attributes and the CHECKED nodes become a
#        Connect by Rule json (app/rules/connect/). A preview dialog picks ONE direction
#        (Source objects drive the nodes = pairs [Source attr, node attr] / nodes drive
#        the Source objects = [node attr, Source attr]), names the rule and the file,
#        and lets you drop pairs. Same-name pairs are written as "attributes", the rest
#        as "pairs". The Connect page's Rule combo is reloaded and set to the new rule.

# 01.61  Connect > Connect by Rule : "Manage..." button. A table of every rule (name, pair
#        count, file; description and pairs in the tooltip) with check boxes - "Delete
#        Checked" removes the checked json files after one confirmation (only files inside
#        app/rules/connect/). Broken files are listed in red but left alone. The combo is
#        reloaded when the window closes.

# 01.62  Constrain > Constraint : "All Targets -> Each Follower" checkbox (off by default) -
#        every follower gets ONE constraint per checked type with EVERY object in the
#        Targets list as a target (like selecting several drivers + one driven in Maya).
#        Off keeps the old pairing (one target = broadcast, otherwise row to row).
#        Disabled in Matrix Constraint mode.

# 01.67  Connect > Connect : "Force (replace existing connections)" checkbox, OFF by default.
#        Off, a driven attribute that already has an incoming connection is left untouched
#        (nothing is disconnected) and listed in the log with what drives it; on, the old
#        connection is broken and replaced (connectAttr -force, the previous behaviour).
#        Applies to both Source -> Destination and Destination -> Source. Only the driven
#        side is checked - a driver already feeding other attributes still connects.

VERSION = "01.67"
LAST_UPDATE = "2026-10-26"
