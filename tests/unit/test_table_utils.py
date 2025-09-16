from bpm.utils.table import kv_aligned, simple_table


def test_kv_aligned_simple():
    lines = kv_aligned([("Project", "Demo"), ("Status", "init")], width=7)
    assert lines[0] == "Project: Demo"
    assert lines[1] == "Status : init"


def test_simple_table_renders_headers_and_rows():
    headers = ["A", "B"]
    rows = [["x", "y"], ["longer", "z"]]
    out = simple_table(headers, rows)
    # header line appears with padded spacing
    line0 = out.splitlines()[0]
    assert line0.startswith("A")
    assert line0.rstrip().endswith("B")
    assert "  " in line0  # two-space column separator
    # separator line with dashes present
    assert set(out.splitlines()[1].replace(" ", "")) == {"-"}
    # includes data cell content
    assert "longer" in out
