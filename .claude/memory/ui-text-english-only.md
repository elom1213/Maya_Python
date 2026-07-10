---
name: ui-text-english-only
description: All UI-facing text in tools must be English; Korean only in comments/docstrings
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 23584ac7-20a8-416e-93f6-f129a72e85d6
---

When writing scripts/tools for this repo, every UI-facing string must be in **English** — button labels, log/console messages shown to the user, in-view messages, window titles, placeholders, dialog text. Korean is fine only in code comments and docstrings ("설명을 위한 인용문에는 한글을 써도 좋아").

**Why:** The user wants the tool UIs in English while keeping explanatory comments readable in Korean.

**How to apply:** Put any string that reaches a widget or a log panel (e.g. `QPushButton(...)`, `self.log(...)`, manager return messages displayed in the UI, `cmds.inViewMessage`) in English. This includes return-value messages from `app/core` managers when they get appended to a UI log. Keep `# 주석` and docstrings in Korean as before. Applies to A00110_animTool and all future tools.
