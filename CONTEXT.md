# notebook-report Context

Mode: normal

## Problem
Data scientists hand stakeholders notebooks with dead cells, out-of-order execution, and exploration mixed into results, and the stakeholder, reviewer, or the author's own future self has no reliable way to tell what's live, what's stale, and what actually matters. notebook-report parses a notebook, deterministically flags stale outputs and strips empty cells, then produces a locked, section-grouped stakeholder report where an LLM's cell classification is advisory only — a human confirms it before anything reaches a stakeholder.

## Data and schema
Input: a single `.ipynb` file (nbformat v4). Internal representation: a Cell object per notebook cell (id, source, cell_type, outputs, execution_count), annotated first with a `stale: bool` + reason (deterministic), then with `proposed_label`/`proposed_gloss` (LLM, advisory). Intermediate artifact: `review.yaml`, a human-editable serialization of that annotated list. No external data sources; no database.

## Founding decisions
- Decision: cell classification (SETUP/EXPLORATION/RESULT/ABANDONED) is advisory only, surfaced in an editable review.yaml the human must pass through before render | Why: the original framing let the model autonomously demote cells, and one wrong demotion (e.g. burying the money chart) would end the data scientist's trust in the tool permanently. Making it advisory turns a silent trust-destroying failure into a one-click fix in review. | Rejected: autonomous model-driven classification with no human gate — scores as a duplicate of Hindsight's autonomous-judge shape and carries the un-fixed trust risk named at vetting.
- Decision: staleness is detected via a local hash-cache sidecar file (hash of cell source, compared run to run) | Why: nbformat does not store which code version produced a given output, so some mechanism is required; a local cache avoids a git dependency and works even if the notebook isn't in a repo. | Rejected: git-history diffing — real v2 upgrade, not required for v1 and adds a hard dependency on the notebook being version-controlled.
- Decision: no labeled benchmark measuring classification precision/recall in this project | Why: Hindsight already demonstrates that exact signal (eval harness + benchmark for LLM judgments); repeating it here would duplicate rather than add a new resume signal. The trust mechanism here is the human review step, not a measured accuracy number. | Rejected: building a small labeled notebook-classification benchmark alongside this project.
- Decision: CLI only for v1, not a web app | Why: smaller, faster-to-finish scope; the human review step works fine as "open review.yaml in a text editor." | Rejected: a browser-based review UI — real v2, not required to show the signal.
- Decision: Anthropic Claude API + Pydantic tool-forced structured output for the classifier | Why: reuses a reliability pattern already proven working in the Hindsight project rather than inventing new prompt-parsing machinery. | Rejected: free-form prompting with regex/string parsing of the model's response.

## Risks and unknowns at birth
- The hash-cache mechanism (Module: Stale-Hash Cache) is the one genuinely novel piece of engineering here and hasn't been prototyped yet — if cell-source hashing produces false positives on trivial reformatting (e.g. whitespace-only edits), that needs a normalization decision before Module 3 is called done. Handle by testing against a fixture that includes a whitespace-only edit as an explicit non-stale case.
- Model classification quality for ambiguous cells (a cell that's part exploration, part result) is unknown until real notebooks are run through Module 5 — this is exactly why classification stays advisory rather than authoritative.
- No labeled benchmark means classification quality is judged qualitatively (does the human need to correct it often?) rather than a hard measured number — acceptable given the founding decision above, but worth being upfront about in the README so it doesn't read as an oversight.
