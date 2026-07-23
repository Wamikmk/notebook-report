# notebook-report STATE

Updated: 2026-07-23 | Commit: none yet | Source: forge (birth)

## Mission
Turn a messy Jupyter notebook into a locked, section-grouped stakeholder report with deterministic stale-output detection and human-confirmed (not autonomous) cell classification. Out of scope: live re-execution, web UI, a classification benchmark, git-based staleness, multi-notebook reports, non-Python kernels, PDF export, auth/hosting (see PLAN.md Not building).

## Current status
Pre-build. No code exists.

## Next step
1. Module 0 (Bootstrap): see PLAN.md. Executable cold via the ignition block.

## Decisions
[Append-only, dated. Founding decisions live in CONTEXT.md; this section
starts empty and takes everything decided after birth.]

## Gotchas
[Append-only, dated. Empty at birth.]

## Open questions
- Whitespace/formatting-only edits to a cell's source: does the stale-hash comparison need to normalize (ignore) these, or should any source diff count as stale? Needs an answer before Module: Stale-Hash Cache is called done — see CONTEXT.md Risks.

## Constraints
- No external deadline (normal mode).
- Local CLI only, no hosting.

## Run commands
[Populated by Module 0's report.]
