import re
from pathlib import Path

from click.testing import CliRunner

from notebook_report.cli import main

FIXTURE = Path(__file__).parent / "fixtures" / "out_of_order.ipynb"


def test_render_produces_ordered_html_with_source_and_output():
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(main, ["render", str(FIXTURE)])
        assert result.exit_code == 0, result.output

        html = Path("report.html").read_text()
        blocks = re.findall(r'<pre class="(source|output)">(.*?)</pre>', html, re.DOTALL)

        assert blocks == [
            ("source", "x = 1\nprint(x)"),
            ("output", "1\n"),
            ("source", "x = 2\nprint(x)"),
            ("output", "2\n"),
        ]
