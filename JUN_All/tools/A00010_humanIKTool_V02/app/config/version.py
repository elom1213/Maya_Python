# 02.06  Mirror : the definition mirror is no longer joints-only. A character whose HIK
#        slots hold CONTROLLERS (+X side) now gets the -X controllers, not joints : the
#        opposite node is looked for among nodes of the SAME type as the source
#        (joint -> joint, transform -> non-joint transform), "Mirror in same root" takes
#        the top of a controller's hierarchy as its root, and the side tokens come from
#        the shared Framework/rules/mirror_tokens.json (same file as A00110 / A00145)
#        instead of a private token table. Buttons renamed Preview / Mirror Definition.

VERSION = "02.06"
LAST_UPDATE = "2026-10-12"
