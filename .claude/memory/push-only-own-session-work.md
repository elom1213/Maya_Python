---
name: push-only-own-session-work
description: "Push ONLY what this session produced — never carry another session's working-tree changes out to the remote, even when the user just says \"푸시해\""
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 5daa567a-aa4a-4115-99c6-ec8bdb8c00eb
  modified: 2026-08-19T01:14:33.391Z
---

A push must contain **only the work this session did**. Changes that were already in the working
tree when this session started, or that appeared from another session / another PC, must **not** go
to the remote — not even when the user says something as simple as "푸시해".

"푸시해" means *push my work*, not *push whatever the working tree happens to hold*.

**Why:** The user stated this after a violation on **2026-08-19**: "넌 지금 다른 세션에서 한 작업
또한 푸시했다. 앞으로 절대로 그렇게 푸시하지 말도록 해. 네가 작업한 세션 외의 작업물은 '푸시해'
처럼 단순한 요청이 들어와도 푸시하지 말고 네가 작업한 작업물만 푸시하도록 해."

What happened: another session's `A00390_WindTool_V02` v02.02 work sat uncommitted in the tree.
I flagged it, the user said "푸시해", and I read that as approval to push everything — committing
that work (`fed0206`) alongside my own fix and sending both out. Flagging it beforehand did **not**
make it authorized; the correct move was to push my commit only and leave theirs untouched.

**How to apply:**

1. Before staging, run `git status` and separate the paths **I** touched this session from
   everything else. If I cannot say from this session's own history that I edited a file, it is
   not mine.
2. Stage **by explicit path** — `git add <my paths>`. Never `git add -A` / `git add .` when the
   tree holds anything I did not write; that is exactly how the foreign work got swept in.
3. Push only after confirming the outgoing commits contain nothing else:
   `git diff --stat <remote>/<branch>..HEAD` and read the file list.
4. Leave the other session's changes uncommitted and untouched. Say plainly in the report what was
   left behind and why.
5. **Shared journal files** (`docs/WORKLOG.md`, `docs/portfolio/*`, `.claude/memory/MEMORY.md`)
   can hold both sessions' entries in one file, so path-level staging cannot split them. Do not
   push the mixed file on a bare "푸시해" — say the file is mixed, name the other session's entry,
   and ask how they want it handled. Do not decide this alone.

Related: [[push-only-when-asked]] (*when* a push is allowed — this memory is about *what* goes in
one), [[push-target-dnable-dev]], [[push-includes-tool-guide-docs]].
