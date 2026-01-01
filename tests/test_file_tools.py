"""
Tests for FileTools path safety.
"""


def test_file_tools_blocks_outside_root(tmp_path):
    from council.tools.file_system import FileTools

    root = tmp_path / "root"
    root.mkdir()
    tools = FileTools(str(root))

    outside = tmp_path / "root_evil" / "secret.txt"
    message = tools.read_file(str(outside))

    assert "Access denied" in message


def test_file_tools_allows_inside_root(tmp_path):
    from council.tools.file_system import FileTools

    root = tmp_path / "root"
    root.mkdir()
    target = root / "ok.txt"
    target.write_text("hello", encoding="utf-8")

    tools = FileTools(str(root))

    assert tools.read_file("ok.txt") == "hello"
