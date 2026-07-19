---
name: planning
description: Use when user requirements are unclear or you are planning a non-trivial feature in plan mode ("계획 세워줘", "플랜 모드", "기능 설계") — question coverage map, question quality bar, plan self-containment, approval snapshot commit.
---

A checklist layered on plan mode's native explore → ask → plan → approve flow. It adds no process of its own.

## Ownership

You are the owner of the code being planned. Treat user requests as intent-bearing opinions, not literal specs — users often ask intuitively without weighing the design. Critically review each request; when a better design exists, present it as the recommendation with evidence and trade-offs, and decide acceptance yourself. The user holds the final call once the trade-offs are on the table.

## Question coverage

Before finalizing a plan, requirements must be settled on every axis below. Skip an axis only when the answer is already in the request, code, or wiki.

- **Background & goal** — the problem being solved; the outcome in one sentence.
- **Scope** — explicit includes AND excludes.
- **Terminology** — user terms colliding with existing code/wiki vocabulary: surface the collision, agree on the canonical term.
- **Domain model** — key objects, their states and allowed values. Enumerable details (payload/DTO fields, user-facing copy, config keys) are requirements: elicit the full list or confirm each member — never invent members of a list the user can enumerate.
- **Business rules & constraints** — condition → outcome rules and state transitions; non-functional needs (performance, security, compatibility); expected behavior on error/failure; edge cases (concurrency, data limits).
- **Cross-system contracts** — names, keys, and codes that external systems reference (backend-deployed rules, API consumers): confirm the freeze/rename policy before planning any rename or restructuring that touches them.
- **Reuse vs extend vs new** — for each affected area, decide with evidence paths; verify fit with architecture/layer/naming conventions.
- **External systems** — integrations touched; reference URLs or docs.
- **Verification** — per task: command + expected output + pass condition. Pick the method by the task's nature (unit test / build / type check / lint / manual / integration). No blanket TDD; no vague "동작 확인".

## Question quality

- Search code and wiki before asking — never ask what is derivable. Delegate broad lookup to an Explore subagent and treat its output as evidence.
- Every question carries: recommendation + source + alternatives + trade-off. Check the recommendation itself against wiki and recorded team decisions — if it contradicts one, surface the conflict instead of recommending past it.
- Surface assumptions. Never silently pick among multiple interpretations — stop and ask.
- If the user insists on a non-recommended option, append the rationale to `feedback.md`.

## Answer loop

One round of questions is rarely enough for feature-sized work.

- Treat every answer as new evidence: re-check each coverage axis against it. A correction, a scope cut, or a new term in an answer usually spawns the next round — do not finalize in the same round an answer changed scope or a contract.
- A hedged enumeration ("일단 그 정도?", "그 정도면 될 듯") marks the list incomplete — probe the remainder with concrete candidates.
- Before finalizing, diff the plan against every user-confirmed decision: each one appears in the plan verbatim, or the deviation is recorded with a reason.

## Plan self-containment

The snapshot is executed by a fresh agent with zero conversation context. The plan must carry:

- **Required-reading list** — wiki doc paths the executor must read before coding, with one-line reasons. Always include docs whose scope matches the files being touched.
- Every externally-verified contract inline (component/API behavior confirmed during exploration) — never "as discussed" or references to the conversation.
- File-by-file work table, design decisions with rationale, commit breakdown with per-commit verification commands, and every user-confirmed decision verbatim.

## Handoff

Before the snapshot commit:

- Verify the plan references nothing from this conversation ("as discussed", "위에서 말한") — it must execute under zero context.
- If `progress/{slug}/plan.md` already exists and is not this branch's snapshot → stop and report a slug collision (`feature/x` and `feature-x` map to the same folder); never overwrite.

On approval: snapshot to `.harness/workspace/progress/{slug}/plan.md`, commit it (first commit of the branch), then stop — tell the user to start implementation in a fresh session with the `/dev-harness:executing-plan` skill. Do not begin implementation.
