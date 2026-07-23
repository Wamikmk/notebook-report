# notebook-report

Turns a messy Jupyter notebook into a locked, stakeholder-ready report — with stale outputs flagged deterministically and cell classification kept advisory until a human confirms it.

## What it does
Data scientists hand stakeholders notebooks with dead cells, out-of-order execution, and exploration mixed into results. notebook-report parses the notebook, orders cells by execution count, strips empty cells, and deterministically flags any cell whose current source no longer matches the source that produced its attached output (a local hash-cache, no re-execution required). An LLM proposes a SETUP/EXPLORATION/RESULT/ABANDONED label and a one-line gloss for each cell — but only as a suggestion in an editable `review.yaml`. A human reviews and can correct any label before the final report locks. The model never silently demotes or hides a cell on its own.

## Demo
[Screenshot: a messy fixture notebook next to its rendered report, gap box visible on a stale chart]

## Stack
Python, `nbformat` (notebook parsing), Anthropic Claude API + Pydantic (structured, schema-validated cell classification), Click (CLI), Jinja2 (locked report template), PyYAML (`review.yaml`) — see CONTEXT.md for why each was chosen over the alternatives considered.

## How it works
`notebook-report analyze notebook.ipynb` parses and annotates the notebook (deterministic staleness first, LLM proposals second) and writes `review.yaml`. You open that file and fix anything the model got wrong. `notebook-report render review.yaml` then produces the final HTML report, grouped into sections by the (possibly corrected) label, with a gap box wherever the hash-cache caught a stale output. The one decision worth reading CONTEXT.md for: classification is advisory by design, not because it wasn't good enough to trust — a single wrong autonomous demotion would have been enough to end a data scientist's trust in the tool for good.

## Results
Tested across [N] notebooks; [X]% of proposed cell labels required no manual correction. Stale-output detection verified against [N] notebooks with injected post-execution edits, zero false negatives.

## Run it locally
```
git clone <repo>
cd notebook-report
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in ANTHROPIC_API_KEY
notebook-report analyze path/to/notebook.ipynb
# edit review.yaml
notebook-report render review.yaml
```
