import pytest

from app.ingestion.chunker import chunk_text


def test_short_text_is_one_chunk():
    assert chunk_text("hello\n\nworld") == ["hello\n\nworld"]


def test_paragraphs_are_packed_up_to_limit():
    paras = ["a" * 40] * 5
    chunks = chunk_text("\n\n".join(paras), max_chars=100, overlap=10)
    assert all(len(c) <= 100 for c in chunks)
    assert len(chunks) == 3  # 2 + 2 + 1 paragraphs


def test_oversized_paragraph_is_split_with_overlap():
    text = "x" * 250
    chunks = chunk_text(text, max_chars=100, overlap=20)
    assert [len(c) for c in chunks] == [100, 100, 90, 10]
    assert chunks[0][-20:] == chunks[1][:20]


def test_empty_text():
    assert chunk_text("  \n\n  ") == []


def test_overlap_must_be_smaller():
    with pytest.raises(ValueError):
        chunk_text("x", max_chars=10, overlap=10)
