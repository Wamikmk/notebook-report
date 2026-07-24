# notebook-report

Turns a messy Jupyter notebook into a locked, stakeholder-ready report. Stale outputs get flagged deterministically. Cell classification stays advisory until a human confirms it.

## What it does
Data scientists hand stakeholders notebooks with dead cells, out-of-order execution, and exploration mixed into results. notebook-report parses the notebook, orders cells by execution count, strips empty cells, and flags any cell whose current source no longer matches the source that produced its attached output. This runs off a local hash-cache, so no re-execution is needed. An LLM proposes a SETUP/EXPLORATION/RESULT/ABANDONED label and a one-line gloss for each cell, but only as a suggestion in an editable `review.yaml`. A human reviews it and corrects any label before the final report locks. The model never silently demotes or hides a cell on its own.

## Demo
[Screenshot: a messy fixture notebook next to its rendered report, gap box visible on a stale chart]

## Stack
Python, `nbformat` for notebook parsing, Anthropic Claude API plus Pydantic for structured, schema-validated cell classification, Click for the CLI, Jinja2 for the locked report template, PyYAML for `review.yaml`. See CONTEXT.md for why each was picked over the alternatives considered.

## How it works
`notebook-report analyze notebook.ipynb` parses and annotates the notebook (deterministic staleness first, LLM proposals second) and writes `review.yaml`. Open that file and fix anything the model got wrong. `notebook-report render review.yaml` produces the final HTML report, grouped into sections by the (possibly corrected) label, with a gap box wherever the hash-cache caught a stale output. Read CONTEXT.md for the decision that matters most here: classification is advisory by design, not because it wasn't good enough to trust. One wrong autonomous demotion would have ended a data scientist's trust in the tool for good.

## Results
Tested across [N] notebooks. [X]% of proposed cell labels required no manual correction. Stale-output detection verified against [N] notebooks with injected post-execution edits, zero false negatives.

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
