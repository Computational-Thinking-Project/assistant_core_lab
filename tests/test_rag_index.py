"""Offline checks for Trung Anh's Lab 06 chunking and retrieval module.

KB fixtures are unchanged lecturer samples from sources/lab6 at 839efd2.
They are teaching data, not verified university policy.
"""

from pathlib import Path

import pytest

from assistant_core.rag.chunker import Chunk, chunk_markdown, load_folder
from assistant_core.rag.index import BM25Index, Hit, make_index, tokenize

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


def test_bm25_finds_thesis_rule(chunks):
    hits = make_index("bm25", chunks).search("can I register my thesis with 118 credits")
    assert hits[0].chunk.id == "H26#5.3"
    assert hits[0].score >= 2.0
    assert all(isinstance(hit, Hit) and hit.score > 0 for hit in hits)
    assert [hit.score for hit in hits] == sorted((hit.score for hit in hits), reverse=True)


@pytest.mark.parametrize("k", [1, 2, 3, 100])
def test_bm25_top_k_is_prefix_of_full_ranking(chunks, k):
    index = make_index("bm25", chunks)
    full = index.search("students credits registration exam", k=len(chunks))
    assert full
    assert index.search("students credits registration exam", k=k) == full[:k]


@pytest.mark.parametrize("query", ["", "the and is", "what is the capital of France"])
def test_bm25_no_match_returns_empty(chunks, query):
    assert make_index("bm25", chunks).search(query) == []


@pytest.mark.parametrize("k", [0, -1])
def test_bm25_nonpositive_limit_returns_empty(chunks, k):
    assert make_index("bm25", chunks).search("thesis", k=k) == []


def test_bm25_empty_corpus_returns_empty():
    assert BM25Index([]).search("thesis") == []


def test_bm25_corpus_without_searchable_tokens_returns_empty():
    chunk = Chunk("X#1", "X", "the", "and is", "v1", "Test")
    assert BM25Index([chunk]).search("thesis") == []


def test_bm25_equal_scores_retain_input_order():
    chunks = [Chunk(cid, "X", "Card", "replacement", "v1", "Test") for cid in ["X#2", "X#1"]]
    hits = BM25Index(chunks).search("card")
    assert hits[0].score == hits[1].score
    assert [hit.chunk.id for hit in hits] == ["X#2", "X#1"]


def test_bm25_prefers_document_matching_both_query_terms():
    chunks = [
        Chunk("X#1", "X", "", "thesis apple", "v1", "Test"),
        Chunk("X#2", "X", "", "thesis registration", "v1", "Test"),
        Chunk("X#3", "X", "", "pear orange", "v1", "Test"),
    ]
    hits = BM25Index(chunks).search("thesis registration")
    assert [hit.chunk.id for hit in hits] == ["X#2", "X#1"]
    assert hits[0].score > hits[1].score


def test_tokenize_keeps_lecturer_rules_without_stemming():
    assert tokenize("Can I register my THESIS, with 118 credits?") == ["register", "thesis", "118", "credits"]
    assert tokenize("credits credit") == ["credits", "credit"]


def test_make_index_rejects_unsupported_kind(chunks):
    with pytest.raises(ValueError, match="Unsupported retrieval kind"):
        make_index("tfidf", chunks)
