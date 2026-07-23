# notebook-report Plan

## Verdict
Weak but fixable, fix taken. Original framing duplicated Hindsight's shape (LLM judges a DS artifact + deterministic guardrail + structured output, applied to notebooks instead of backtest code). Fix: cell classification is advisory only, gated behind a human review step the author must confirm before the report locks — this is a genuinely distinct signal (human-in-the-loop calibration for LLM-assisted document generation) and it also defuses the originally-named failure mode (a wrong guess is a one-click fix in review, not a silent demotion that burns trust).

## Signal
Human-in-the-loop calibration for LLM-assisted document generation: a deterministic-first pipeline where structural signals (execution order, a stale-hash cache, empty-cell stripping) decide what's possible to show, and the model's SETUP/EXPLORATION/RESULT/ABANDONED label + figure gloss are advisory only — surfaced in an editable review artifact the author confirms before the report locks. Distinct from Hindsight (autonomous LLM judge + labeled benchmark, applied to backtest code) and from Karat (data pipeline + fair-value model). Target role: data science — leads with reproducibility/comms hygiene and honest handling of an unreliable model judgment, not raw modeling.

## MVP scope
CLI, two-step flow:
1. `notebook-report analyze notebook.ipynb` — parses the notebook via nbformat, orders cells by execution_count, strips empty cells, computes/compares a local stale-hash cache, calls Claude once per non-empty cell for a proposed label + figure gloss (Pydantic-validated), writes everything to an editable `review.yaml`.
2. Human opens `review.yaml`, corrects any label/gloss they disagree with.
3. `notebook-report render review.yaml` — renders the locked HTML report template, grouped by (possibly human-corrected) label, with a gap box wherever the stale-hash cache flagged a mismatch.

## Not building
- Live re-execution of the notebook via a kernel, never — staleness works off saved outputs + hash cache only.
- Web UI / upload flow, later — v1 is CLI only.
- A labeled benchmark measuring classification precision/recall, never, deliberately — Hindsight already banks that exact signal (eval harness + benchmark); repeating it here would re-duplicate rather than differentiate. The trust mechanism here is the human review step, not a measured accuracy number.
- Git-history-based staleness detection, later — v1 uses the local hash-cache sidecar; git integration is a real v2 upgrade.
- Multi-notebook / project-level aggregate reports, later.
- R/Julia or other non-Python kernels, never.
- PDF export, later — HTML only for v1.
- Any auth, hosting, or multi-user concerns, never — local single-user CLI.

## Stack
- Python + `nbformat` — official Jupyter library, handles cell-schema version differences instead of hand-parsing raw JSON.
- Anthropic SDK + Pydantic tool-forced structured output — reuses the reliability pattern already proven in Hindsight, over free-form prompt + regex parsing.
- Click — subcommand ergonomics for `analyze`/`render` with less magic than Typer, less boilerplate than argparse.
- Jinja2 — the locked report template lives in one file, separate from render logic.
- PyYAML for `review.yaml` — the file is meant to be hand-edited by a human; YAML is more legible than JSON for that purpose.
- Local hash-cache sidecar file for staleness — no git dependency, works even outside a repo.

## Trust boundaries
1. User-supplied `.ipynb` (untrusted, arbitrary file): `nbformat.read()` raises on malformed JSON/schema; caught and surfaced as a clean CLI error (Module 7), never a raw stack trace.
2. Model output (label + gloss): untrusted, feeds what the report displays. Pydantic schema-validated (every field present, label in the fixed enum). One retry on violation, then fallback to `UNCLASSIFIED`/no gloss. Never branch on unvalidated model JSON.
3. Hand-edited `review.yaml`: a human can introduce a typo or invalid label. `render` validates every entry against the same label enum before rendering; a violation fails render with a clear "line X, unknown label Y" message rather than rendering garbage silently.

No Case A/B/C file applies: no frozen runtime parameters (not a backtest/scoring engine), no API service contract, no hackathon submission schema. `review.yaml` is per-run editable content, not a frozen spec.

## Modules (slice-first order, Module 0 always first)

### Module 0: Bootstrap
Does: turns the bare repo into a runnable, tested skeleton.
Inputs: forge files committed by hand. Output: an environment every later module can trust.

Steps:
1. Verify: repo path is under ~ not /mnt/c (WSL: venvs on the Windows
   filesystem are slow and flaky), python --version matches CLAUDE.md,
   git status clean.
2. Create the tree:
   ```
   notebook-report/
     notebook_report/
       __init__.py
       parser.py       # M1
       staleness.py     # M3
       classifier.py    # M5
       review.py        # M6
       render.py        # M2, M4, M7
       cli.py            # click entrypoint
       templates/report.html.jinja
     tests/
       fixtures/*.ipynb
       test_parser.py test_staleness.py test_classifier.py test_review.py test_render.py test_smoke.py
     pyproject.toml requirements.txt .env.example .gitignore README.md
   ```
3. python -m venv .venv. Every later command uses .venv/bin/python.
4. Install nbformat, anthropic, pydantic, click, jinja2, pyyaml, pytest (dev). Write requirements.txt.
5. Write .gitignore: .venv/, .env, __pycache__/, *.egg-info/, .pytest_cache/, stray report.html/review.yaml at repo root.
6. Write .env.example with key names only: ANTHROPIC_API_KEY. Never values.
7. Scaffold: package __init__, entrypoint stub (cli.py), tests/test_smoke.py
   that imports the package.
8. One cheapest-possible live call to the Anthropic API using .env, to confirm the key works.

Acceptance: pytest exits 0 with at least 1 test collected, the
entrypoint runs, the report packet shows the tree output and dep count.
Estimate: 10-15 min.
Stop: append the PROGRESS entry, emit the report packet, human commits.

### Module: Notebook Parser
- Purpose: Parse a .ipynb into an ordered, cleaned internal cell list.
- Inputs: path to .ipynb.
- Outputs: Cell objects (id, source, cell_type, outputs, execution_count), ordered by execution_count, empty cells stripped.
- Depends on: Module 0.
- Acceptance test: fixture notebook with out-of-order execution_counts and one truly empty cell — parser returns correctly ordered list with the empty cell absent (pytest assertion).
- Slice: 1, first.

### Module: Report Renderer (bare)
- Purpose: Render the locked HTML template from the ordered cells, no classification/staleness yet.
- Inputs: ordered Cell list.
- Outputs: report.html.
- Depends on: Notebook Parser.
- Acceptance test: `notebook-report render fixture.ipynb` produces HTML containing every non-empty cell's source/output in correct order (parsed and checked in the test).
- Slice: 1, completes it — first real end-to-end command.

### Module: Stale-Hash Cache
- Purpose: Deterministically detect when a cell's current source no longer matches the source that produced its attached output, via a local hash-cache sidecar file.
- Inputs: ordered Cell list, path to cache file (created if absent).
- Outputs: Cell list annotated with stale: bool + reason; updated cache file.
- Depends on: Notebook Parser.
- Acceptance test: first run creates the cache with zero stale cells; editing one cell's source without changing execution_count, second run flags exactly that cell.
- Slice: 2.

### Module: Gap Boxes in Render
- Purpose: Surface the Stale-Hash Cache's flags in the rendered report.
- Inputs: annotated Cell list.
- Outputs: report.html with a gap box next to each stale cell's output.
- Depends on: Report Renderer, Stale-Hash Cache.
- Acceptance test: rendering the post-edit fixture produces HTML with exactly one gap-box element, referencing the correct cell id.
- Slice: 2, completes it.

### Module: LLM Cell Classifier + Gloss (advisory)
- Purpose: Propose a label (SETUP/EXPLORATION/RESULT/ABANDONED) and a one-line gloss per cell via Claude, schema-validated.
- Inputs: annotated Cell list.
- Outputs: Cell list with proposed_label, proposed_gloss (advisory, unconfirmed).
- Depends on: Stale-Hash Cache.
- Acceptance test: fixture with an unambiguous setup cell (imports only) and an unambiguous abandoned cell (commented-out, no output) get the expected labels in a scripted test against a mocked/fixed model response, schema-validated; a malformed model response triggers one retry then falls back to UNCLASSIFIED without crashing.
- Slice: 3.

### Module: Review Artifact
- Purpose: Serialize proposals + deterministic flags into human-editable review.yaml; split the CLI into `analyze` (writes review.yaml) and `render` (reads review.yaml, possibly hand-edited).
- Inputs: fully annotated Cell list.
- Outputs: review.yaml; render now reads from it instead of re-deriving from the notebook.
- Depends on: LLM Cell Classifier + Gloss.
- Acceptance test: `analyze` writes review.yaml; hand-editing one label in the file then running `render review.yaml` produces a report reflecting the edited label, not the model's original proposal.
- Slice: 3, completes it. This is the money module — the human-in-the-loop mechanism that is the whole point of the vetting fix.

### Module: Locked Sections + Polish
- Purpose: Group final render into Setup/Exploration/Result/Abandoned sections; handle malformed notebooks cleanly.
- Inputs: reviewed Cell list.
- Outputs: final report.html grouped by section; clean CLI errors on bad input.
- Depends on: Review Artifact.
- Acceptance test: 2-3 varied fixtures (including one corrupt .ipynb) produce correctly grouped sections for good input and a non-crashing clear error for the corrupt one.
- Slice: 4, final.

## Resume bullets
- Built a CLI tool that converts messy Jupyter notebooks into locked stakeholder reports, using deterministic source-hash caching to flag stale outputs across [N] real notebooks — catching hand-off errors that out-of-order execution and dead cells create, without re-executing any code.
- Designed a human-in-the-loop review step for LLM-proposed cell classification (SETUP/EXPLORATION/RESULT/ABANDONED + figure glosses, Pydantic-validated structured output via the Claude API), keeping a human as the final gate before any label reaches a stakeholder — [X]% of proposed labels required no correction across [N] test notebooks.
- Implemented schema-validated, retry-then-fallback handling for LLM output so a malformed model response degrades to an "unclassified" label instead of corrupting a generated report, tested across [N] notebooks with [Z] injected malformed responses and zero silent failures.

## Ignition (first prompt for Claude Code)
Read CLAUDE.md, CONTEXT.md, PLAN.md. Execute Module 0 only.
Stop when its acceptance passes and produce the report packet.
