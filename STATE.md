# STATE: notebook-report
Updated: 2026-07-24 | Commit: 0f065f0 (nothing new committed yet — see Next step) | Source: Claude Code session executing Module: Report Renderer (bare)

## Mission
Turn a messy Jupyter notebook into a locked, section-grouped stakeholder report with deterministic stale-output detection and human-confirmed (not autonomous) cell classification.
Out of scope: live re-execution, web UI, a classification benchmark, git-based staleness, multi-notebook reports, non-Python kernels, PDF export, auth/hosting (see PLAN.md Not building).

## Current status
Module 0 (Bootstrap), Module: Notebook Parser (M1), and Module: Report Renderer bare (M2) all have passing acceptance, but nothing is committed yet — human commits by hand per CLAUDE.md. A commit covering module 0 + M1 was attempted this session and denied by the user (permission denial on the `git commit` tool call, not a stated objection to content); M2 was built on top per explicit user instruction ("lets do module 2 and then commit"), so all three are now bundled pending one commit.

M1: `notebook_report/parser.py` defines a `Cell` dataclass (id, source, cell_type, outputs, execution_count) and `parse_notebook(path) -> list[Cell]`, which reads via `nbformat.read(path, as_version=4)`, strips cells whose source is empty/whitespace-only, and sorts by `(execution_count is None, execution_count, original_index)` — executed cells ordered by execution_count, unexecuted/markdown cells pushed to the end in original relative order (not itself acceptance-tested; see Decisions).

M2: `notebook_report/render.py` adds `render_report(cells) -> str`, a Jinja2 `Environment` (autoescape on) loading `templates/report.html.jinja`, with a custom `output_text` filter that extracts display text from a cell's `outputs` list (stream text, `data["text/plain"]`, or error traceback, in that priority order). The template emits one `<section class="cell">` per cell with a `<pre class="source">` and, only if output text is non-empty, a `<pre class="output">`. `cli.py`'s `render` command now works end-to-end: parses the notebook, renders, writes `report.html` to cwd. `analyze` is still a stub. The `render` command's Click argument was renamed from `review_path` to `notebook_path` — it takes the `.ipynb` directly for now since Module: Review Artifact (M6, which introduces `review.yaml` and the analyze/render split) hasn't been built yet; expect this argument to change again at M6.

Verified directly against the repo this pass:
- `git log -1 --oneline` → `0f065f0 Forge birth: notebook-report plan and working memory` (no new commits)
- `.venv/bin/python -m pytest -q` → 3 passed (`test_smoke.py::test_import`, `test_parser.py::test_parse_orders_by_execution_count_and_strips_empty_cells`, `test_render.py::test_render_produces_ordered_html_with_source_and_output`)
- Manual end-to-end check: `notebook-report render tests/fixtures/out_of_order.ipynb` in a scratch dir → `report.html` has two `<section class="cell">` blocks in execution-count order (1 then 2), each with correct source and stream output text.

## Next step
1. Human reviews and commits Module 0 + Module: Notebook Parser (M1) + Module: Report Renderer bare (M2) — this session does not commit.
2. Once ready, start Module: Stale-Hash Cache per PLAN.md — deterministic staleness detection via a local hash-cache sidecar file. Never module N+1 before N is committed.
3. Before M5 (LLM Classifier) can be exercised against the real API, the Anthropic account needs credits topped up — the smoke call confirms the integration works, not that it's currently billable.

## Architecture
Stack: Python 3.11, nbformat, Anthropic SDK, Pydantic, Click, Jinja2, PyYAML; pytest for tests.
Files:
- `notebook_report/__init__.py` — empty package marker.
- `notebook_report/cli.py` — Click group; `render` implemented (M2, takes `notebook_path`, writes `report.html`), `analyze` still `raise NotImplementedError`. Entrypoint registered via pyproject.toml `[project.scripts]`.
- `notebook_report/parser.py` — implemented (M1): `Cell` dataclass + `parse_notebook`.
- `notebook_report/render.py` — implemented (M2): `render_report(cells)` + `_output_text` Jinja filter.
- `notebook_report/templates/report.html.jinja` — implemented (M2): one `<section class="cell">` per cell, source + optional output `<pre>`.
- `notebook_report/staleness.py`, `classifier.py`, `review.py` — empty stub files awaiting their respective modules (M3, M5, M6).
- `tests/test_smoke.py` — imports the package. `tests/test_parser.py` — M1 acceptance test. `tests/test_render.py` — M2 acceptance test (reuses the M1 fixture). `tests/fixtures/out_of_order.ipynb` — out-of-order execution_counts + one whitespace-only cell.
- `pyproject.toml`, `requirements.txt` (pip freeze, 35 lines), `.gitignore`, `.env.example` — all new from module 0.
- `.env` — created at module 0, gitignored, key value not yet confirmed working (see Gotchas).
Flow: `.ipynb` → parser → staleness → classifier (LLM, advisory) → review.yaml (human-edited) → render → report.html. Parser (M1) and bare render (M2) implemented; staleness/classifier/review not yet implemented, and render doesn't yet read review.yaml (that's M6).

## Decisions (append-only)
- [2026-07-24] Used uv's cached CPython 3.11.11 (`~/.local/share/uv/python/cpython-3.11.11-linux-x86_64-gnu/bin/python3.11`) to create `.venv`, instead of the system `python3` (3.10.12, which doesn't meet CLAUDE.md's 3.11+ requirement). Reason: uv already had 3.11.11 installed locally from prior use; no system/apt package install needed, so this doesn't trip the "new dependency needs approval" rule. SETTLED.
- [2026-07-24] `parse_notebook` sorts cells without an `execution_count` (markdown cells, or code cells never run) to the end of the list, in their original relative order, rather than interleaving them by position. Reason: PLAN.md's acceptance test only specifies ordering for executed code cells; this is the simplest rule that doesn't require guessing where an unexecuted cell "belongs" relative to executed ones. Not acceptance-tested (fixture is all-code-cells) — revisit if a later module's fixture shows this is wrong for markdown-heavy notebooks. SETTLED for M1.
- [2026-07-24] "Truly empty" cell = `source.strip() == ""` (whitespace-only or zero-length), independent of `execution_count`. Reason: matches PLAN.md's fixture description ("one truly empty cell") and CONTEXT.md's open question about whitespace-only edits not counting as stale (M3 concern) — kept the empty-cell-stripping rule in M1 orthogonal to that. SETTLED for M1.
- [2026-07-24] M2's `render` CLI command takes the notebook path directly (`notebook-report render fixture.ipynb`), not a `review.yaml` — the Click argument was renamed from the module-0 stub's `review_path` to `notebook_path`. Reason: PLAN.md's own acceptance test for this module calls it that way; the review.yaml split is a later module (M6, Review Artifact). Expect another rename at M6. SETTLED for M2.
- [2026-07-24] Output text extraction priority in `render.py`'s `_output_text`: stream `text` first, then `data["text/plain"]` (execute_result/display_data), then `traceback` (error), first match wins per output entry, joined with newlines across multiple outputs. Reason: simplest deterministic precedence that covers the three common nbformat output_types without needing to branch on `output_type` explicitly. Not stress-tested against rich outputs (images, HTML tables) — those fall through to nothing shown, acceptable for the bare renderer. SETTLED for M2.

## Constraints and hard rules
- No auto-commit, ever — human commits Module 0 (and every module) by hand.
- `.env` is never read, written-to-content, or echoed by the agent; only loaded by a script via env vars for the smoke call.
- Never module N+1 before module N's acceptance passes and is committed.
- No external deadline (normal mode). Local CLI only, no hosting.

## Gotchas (append-only)
- [2026-07-24] System `python3` is 3.10.12, but CLAUDE.md requires 3.11+; no python3.11 was installed system-wide (apt candidate existed but wasn't installed). Instead: create `.venv` with the uv-cached 3.11.11 interpreter directly (see Decisions above), don't apt-install a new system Python.
- [2026-07-24] Module 0 step 8 (live API smoke call) got blocked twice: first, no `ANTHROPIC_API_KEY` was set in the shell env or in any `.env` file (none existed yet); second, once asked, the user reported their existing key's credits had expired. Confirmed: the smoke call (`claude-haiku-4-5-20251001`, `max_tokens=1`) returned `400 invalid_request_error: Your credit balance is too low` — not a `401 authentication_error`, so the key itself is valid and the SDK/env-loading path works; the account just has no credits. Instead: treat this as "key mechanism confirmed, account needs credits," not a broken integration — re-run the same smoke call once credits are topped up to get an actual successful response.

## Open questions
- Whitespace/formatting-only edits to a cell's source: does the stale-hash comparison need to normalize (ignore) these, or should any source diff count as stale? Needs an answer before Module: Stale-Hash Cache is called done — see CONTEXT.md Risks. (Untouched this pass — M3 hasn't started.)

## Run and verify
```
.venv/bin/python -m pytest -q          # 3 passed
.venv/bin/notebook-report --help       # lists analyze, render
.venv/bin/notebook-report render tests/fixtures/out_of_order.ipynb   # writes report.html to cwd
git log -1 --oneline                   # 0f065f0, nothing new committed
git status --short                     # module 0 + M1 + M2 files all pending, one commit not yet made
```
