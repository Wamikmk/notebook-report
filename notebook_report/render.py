from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from notebook_report.parser import Cell

TEMPLATE_DIR = Path(__file__).parent / "templates"


def _output_text(outputs: list) -> str:
    parts = []
    for output in outputs:
        text = output.get("text")
        if text is not None:
            parts.append("".join(text) if isinstance(text, list) else text)
            continue

        data = output.get("data", {})
        plain = data.get("text/plain")
        if plain is not None:
            parts.append("".join(plain) if isinstance(plain, list) else plain)
            continue

        traceback = output.get("traceback")
        if traceback is not None:
            parts.append("\n".join(traceback))

    return "\n".join(parts)


def render_report(cells: list[Cell]) -> str:
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        autoescape=select_autoescape(["html", "jinja"]),
    )
    env.filters["output_text"] = _output_text
    template = env.get_template("report.html.jinja")
    return template.render(cells=cells)
