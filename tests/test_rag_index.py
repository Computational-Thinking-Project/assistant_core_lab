"""Offline checks for Trung Anh's Lab 06 chunking and retrieval module.

KB fixtures are unchanged lecturer samples from sources/lab6 at 839efd2.
They are teaching data, not verified university policy.
"""

from pathlib import Path

import pytest

from assistant_core.rag.chunker import chunk_markdown, load_folder

KB = Path(__file__).parent / "fixtures" / "lab06" / "kb"


@pytest.fixture
def chunks():
    return load_folder(KB)


def test_sample_chunks_preserve_source_ids_and_metadata(chunks):
    assert len(chunks) == 14
    assert len({chunk.id for chunk in chunks}) == 14
    assert {"H26#5.3", "F26#2", "S26#3"} <= {chunk.id for chunk in chunks}
    assert all(chunk.version == "2026.1" for chunk in chunks)
    owners = {"H26": "Training Office", "F26": "Finance Office", "S26": "Student Affairs"}
    assert all(chunk.owner == owners[chunk.doc_id] for chunk in chunks)
    thesis = next(chunk for chunk in chunks if chunk.id == "H26#5.3")
    assert thesis.title == "5.3 Thesis registration"
    assert "120 accumulated credits" in thesis.text
    assert "Late thesis registration" not in thesis.text


def test_load_folder_orders_files_then_sections(tmp_path):
    (tmp_path / "z.md").write_text("# 2 Last\nZ", encoding="utf-8")
    (tmp_path / "a.md").write_text("# 3 First\nA\n# 1 Second\nB", encoding="utf-8")
    (tmp_path / "ignored.txt").write_text("# 1 Ignore", encoding="utf-8")
    assert [chunk.id for chunk in load_folder(tmp_path)] == ["a#3", "a#1", "z#2"]


def test_chunk_markdown_defaults_and_collapses_whitespace(tmp_path):
    path = tmp_path / "sample.md"
    path.write_text("Introduction\n# 1 Title\nLine one.\n\n  Line two.\n", encoding="utf-8")
    (chunk,) = chunk_markdown(path)
    assert (chunk.id, chunk.doc_id, chunk.version, chunk.owner) == ("sample#1", "sample", "?", "?")
    assert chunk.text == "Line one. Line two."


def test_frontmatter_handles_windows_newlines_and_colon_in_value(tmp_path):
    path = tmp_path / "sample.md"
    path.write_bytes(b"---\r\ndoc_id: X\r\nowner: Team: Office\r\nversion: v1\r\n---\r\n# 1 Title\r\nBody\r\n")
    (chunk,) = chunk_markdown(path)
    assert (chunk.id, chunk.owner, chunk.version) == ("X#1", "Team: Office", "v1")
    assert chunk.text == "Body"


def test_empty_folder_returns_no_chunks(tmp_path):
    assert load_folder(tmp_path) == []


@pytest.mark.parametrize("text", ["", "A document without section headings."])
def test_no_sections_returns_no_chunks(tmp_path, text):
    path = tmp_path / "sample.md"
    path.write_text(text, encoding="utf-8")
    assert chunk_markdown(path) == []
