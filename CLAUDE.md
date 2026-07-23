# notebook-report

Converts a messy Jupyter notebook into a locked, human-reviewed stakeholder report. Stack: Python, nbformat, Anthropic SDK, Pydantic, Click, Jinja2, PyYAML. Mode: normal.

## Commands
- Env: source .venv/bin/activate  (always use .venv/bin/python)
- Test all: pytest
- Test one: pytest tests/test_[x].py -k [name]  (prefer this while iterating)
- Run: notebook-report analyze notebook.ipynb   /   notebook-report render review.yaml

## Conventions
- Python 3.11+, package layout under notebook_report/, one module per PLAN.md module.
- Simplest approach that passes acceptance. No abstractions with one
  caller. No features beyond the current module.
- New dependency: flag it and wait for approval. Never install first.
- Never read, write, or echo .env or its contents.
- Model output is untrusted input. Schema-check it (every required
  field, only allowed values) before any code consumes it. Violations
  route to one retry, then the safe fallback (UNCLASSIFIED / no gloss).
  Never branch on unvalidated model JSON.
- Cell classification is always advisory. Never let the render path skip,
  hide, or reorder a cell based on the model's proposed label alone —
  only review.yaml (after a human has had the chance to edit it) drives
  what the locked report shows.
- Each acceptance test lands as a committed pytest test before the module is done.

## Workflow
- Build in PLAN.md module order, slice-first. One module per prompt
  packet. Never start module N+1.
- Multi-file change: present the plan before editing.
- Blocked: reduce to the smallest repro, report, stop. No speculative fixes.
- Acceptance passes: append the PROGRESS.md entry, emit the report
  packet (below), stop. The human commits; never commit or push.
- Non-obvious choice made mid-build: append a dated line to
  STATE.md ## Decisions. A gotcha that cost time: dated line to ## Gotchas.
- Git output is ground truth over your own narration.

## Report packet (emit at every stop)
## Report: [module ID]
Status: passed / blocked
Test command: [exact command]
Output tail: [last 5-10 lines, verbatim]
Git: [git log -1 --oneline] + [git status --short]
Files changed: [list]
Decisions made: [dated, or "none"]
Deviations: [anything outside the prompt, or "none"]
Blockers: [smallest reproduction, if blocked]

## Where to look
- PLAN.md: scope, module order, acceptance tests
- CONTEXT.md: founding decisions (frozen at birth)
- STATE.md: live status and decision log
