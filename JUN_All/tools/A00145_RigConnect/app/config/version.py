# -*- coding: utf-8 -*-
# A00145_RigConnect - version info

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

# 01.55  Default window height 900 -> 980 so the whole Match tab fits without a
#        scroll bar.
# 01.54  (Null) placeholder rows are drawn in RED in every list (the shared
#        TSL paints them; Connect > Match calls the same helper). It used to
#        be grey in one list only, and plain text in the Pair tab.

VERSION = "01.55"
LAST_UPDATE = "2026-09-23"
