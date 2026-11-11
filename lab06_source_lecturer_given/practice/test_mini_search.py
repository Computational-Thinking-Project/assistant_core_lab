from mini_search import DOCS, build_index, search, tokenize


def test_tokenize_given():
    assert tokenize("I lost my student card!") == ["lost", "student", "card"]


def test_s1_index():
    idx = build_index(DOCS)
    assert idx["credits"] == {"D1", "D2"}
    assert idx["card"] == {"D3"}


def test_s2_s3_search():
    idx = build_index(DOCS)
    assert search(idx, "I lost my student card")[0] == ("D3", 3)
    assert search(idx, "how many credits for a thesis")[0] == ("D1", 2)


def test_no_match_returns_empty():
    assert search(build_index(DOCS), "what is the capital of France") == []


def test_nonpositive_limit_returns_empty_for_matching_documents():
    index = build_index(DOCS)
    assert search(index, "credits", k=0) == []
    assert search(index, "credits", k=-1) == []
