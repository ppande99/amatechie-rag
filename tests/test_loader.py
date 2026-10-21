from app.ingestion.loader import RawDoc, load_directory, parse_front_matter


def test_front_matter_groups():
    groups, body = parse_front_matter("---\ngroups: sre, platform\n---\n\n# Title\ntext")
    assert groups == ["sre", "platform"]
    assert body.startswith("# Title")


def test_no_front_matter():
    assert parse_front_matter("# Title") == ([], "# Title")


def test_unterminated_front_matter_is_plain_text():
    assert parse_front_matter("---\ngroups: sre\nno end")[0] == []


def test_load_directory(tmp_path):
    (tmp_path / "a").mkdir()
    (tmp_path / "a" / "one.md").write_text("---\ngroups: sre\n---\nhello")
    (tmp_path / "two.txt").write_text("world")
    (tmp_path / "skip.pdf").write_text("ignored")
    (tmp_path / "empty.md").write_text("   ")
    docs = load_directory(tmp_path)
    assert [(d.source, d.allowed_groups) for d in docs] == [("a/one.md", ["sre"]), ("two.txt", [])]


def test_hash_changes_when_groups_change():
    assert RawDoc("a", "t", ["x"]).content_hash != RawDoc("a", "t", ["y"]).content_hash
