---
name: harvest-docs
description: Use when periodically auditing the whole .harness/docs/ wiki ("위키 감사", "위키 정리", "docs 정리") — fix contract violations, converge SSOT duplicates, split accumulated domains, tidy frontmatter.
---

Periodic corpus sweep of `.harness/docs/`. Goal: a consuming agent reads only its domain slice — that lean-wiki goal is the tie-breaker for keep/split/delete calls. Unlike writing-docs (per-branch increment), this audits the existing corpus; user-invoked, workspace-independent.

Read `${CLAUDE_PLUGIN_ROOT}/references/wiki-rules.md` first — the contract for record/exclude criteria, folder shapes, frontmatter, and style. It is not auto-loaded.

## Contract

- Run on the integration branch (develop/main/master) — the wiki SSOT lives there. No base-branch refusal.
- `.harness/docs/` is a permanent shared asset. No writes before user approval.
- Never lose a fact. Delete only what matches the wiki-rules Exclude list; a valuable fact moves (to its owning doc or an ADR), never drops.
- Never whole-file-merge scattered fragments (reversal + reference-cascade risk). Converge by dedup, relocation, and SSOT demotion only; intentional domain/page/external splits stay.
- One pass need not clean everything — only user-selected docs. SSOT convergence applies within the selected set; overlap with an unselected doc waits until that doc is selected.

## Steps

1. Run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/wiki_index.py"` once; cache. Candidates: `harvested` blank (never cleaned) or `harvested < updated` (changed since last clean). Rank by index-only signals — description bloat (>150 chars), high LINES, blank/stale `harvested`. Open no bodies yet.
2. Present the ranked candidates; the user multi-selects which to diagnose. Zero candidates → report, exit.
3. Open selected bodies only. Diagnose against wiki-rules — shape split, domain split (one file = one domain; split slices self-contained, foreign-owned SSOT short-cited, no leftover internal `see §X` navigation), Exclude-list body content, SSOT boundary (one owner, others demoted to short cites), style, frontmatter. Zero violations for a doc → refresh `harvested` only.
4. Present the `(doc, violation, action)` table. Splits, ADR creation, and deletions are costly to reverse — list each explicitly. Only approved actions proceed.
5. Apply. An ADR split leaves only the adopted rule in the flat doc; the rationale moves to the ADR. Fix cross-references broken by splits/deletes/convergence; every `§` anchor must still resolve (cited headings frozen). Set `harvested` = today on every processed doc.
6. Re-scan processed docs clean (contract + frontmatter). Report the changed-file list. Commit only on user instruction.
