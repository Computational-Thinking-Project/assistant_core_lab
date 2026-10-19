"""Unit tests for knowledge sources: OfficeDirectory and Handbook (Step 5)."""

from __future__ import annotations

import json
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

try:
    from assistant_core.errors import DataError
except ImportError:
    from assistant_core.knowledge import DataError
from assistant_core.knowledge import (
    Handbook,
    Office,
    OfficeDirectory,
    Rule,
)

DATA_DIR = Path(__file__).parent.parent / "data"


# ===========================================================================
# Office & OfficeDirectory Tests
# ===========================================================================


def test_office_dataclass_immutable() -> None:
    """Office instances must be frozen and immutable."""
    office = Office(name="Library", room="B.201", hours="Mon-Sat 07:00-20:00")
    assert office.name == "Library"
    assert office.room == "B.201"
    assert office.hours == "Mon-Sat 07:00-20:00"

    with pytest.raises(FrozenInstanceError):
        office.room = "A.101"  # type: ignore[misc]


def test_office_directory_from_csv_success() -> None:
    """OfficeDirectory.from_csv loads the official data/offices.csv accurately."""
    csv_path = DATA_DIR / "offices.csv"
    directory = OfficeDirectory.from_csv(csv_path)

    expected_offices = {"training office", "student affairs", "library", "it helpdesk"}
    assert directory.names == expected_offices
    assert directory.get_names() == expected_offices
    assert len(directory.offices) == 4

    lib = directory.find("library")
    assert lib is not None
    assert lib.name == "Library"
    assert lib.room == "B.201"
    assert lib.hours == "Mon-Sat 07:00-20:00"


def test_office_directory_find_queries() -> None:
    """OfficeDirectory.find matches office names substring within query text."""
    csv_path = DATA_DIR / "offices.csv"
    directory = OfficeDirectory.from_csv(csv_path)

    # Partial substring query
    assert directory.find("where is the training office?") is not None
    assert directory.find("WHERE IS STUDENT AFFAIRS") is not None
    assert directory.find("Need it helpdesk support") is not None

    # Unrelated queries
    assert directory.find("what is the weather?") is None
    assert directory.find("tuition fee calculation") is None
    assert directory.find("") is None


def test_office_directory_missing_file_raises_data_error(tmp_path: Path) -> None:
    """Missing CSV file must raise DataError instead of raw FileNotFoundError."""
    missing_path = tmp_path / "non_existent.csv"
    with pytest.raises(DataError, match=r"office file not found"):
        OfficeDirectory.from_csv(missing_path)


def test_office_directory_malformed_csv_raises_data_error(tmp_path: Path) -> None:
    """Malformed CSV missing required columns must raise DataError."""
    bad_csv = tmp_path / "bad_offices.csv"
    bad_csv.write_text("name,room\nLibrary,B.201\n", encoding="utf-8")

    with pytest.raises(DataError, match=r"missing field"):
        OfficeDirectory.from_csv(bad_csv)


def test_office_directory_load_alias() -> None:
    """OfficeDirectory.load must function identically to from_csv."""
    csv_path = DATA_DIR / "offices.csv"
    dir1 = OfficeDirectory.from_csv(csv_path)
    dir2 = OfficeDirectory.load(csv_path)
    assert dir1.names == dir2.names


# ===========================================================================
# Rule & Handbook Tests
# ===========================================================================


def test_rule_dataclass_immutable() -> None:
    """Rule instances must be frozen and immutable."""
    rule = Rule(id="H26-5.3", title="Thesis registration", text="Students may register a thesis...")
    assert rule.id == "H26-5.3"
    assert rule.title == "Thesis registration"

    with pytest.raises(FrozenInstanceError):
        rule.title = "New title"  # type: ignore[misc]


def test_handbook_from_json_success() -> None:
    """Handbook.from_json loads the official data/handbook.json accurately."""
    json_path = DATA_DIR / "handbook.json"
    handbook = Handbook.from_json(json_path)

    assert len(handbook.rules) == 5
    rule_ids = {r.id for r in handbook.rules}
    assert "H26-4.2" in rule_ids
    assert "H26-5.3" in rule_ids
    assert "H26-5.4" in rule_ids
    assert "H26-6.1" in rule_ids
    assert "H26-7.2" in rule_ids


def test_handbook_search_hits() -> None:
    """Handbook.search accurately retrieves rule matching keyword overlap."""
    json_path = DATA_DIR / "handbook.json"
    handbook = Handbook.from_json(json_path)

    # Thesis question
    res_thesis = handbook.search("can I register my thesis with 118 credits")
    assert res_thesis is not None
    assert res_thesis.id == "H26-5.3"
    assert "thesis" in res_thesis.title.lower()

    # Retake question
    res_retake = handbook.search("policy on retaking a course")
    assert res_retake is not None
    assert res_retake.id == "H26-4.2"

    # Exam absence question
    res_exam = handbook.search("absence from final exam due to medical reasons")
    assert res_exam is not None
    assert res_exam.id == "H26-7.2"


def test_handbook_search_short_tokens_ignored() -> None:
    """Tokens with length <= 3 must not contribute to keyword overlap score."""
    rules = [Rule(id="R1", title="Short word test", text="The cat sat on the mat and had tea with fee.")]
    hb = Handbook(rules)
    # Query words "cat", "sat", "tea", "fee", "mat" are all <= 3 chars
    assert hb.search("cat sat tea fee") is None


def test_handbook_search_misses() -> None:
    """Handbook.search returns None when no keyword overlaps."""
    json_path = DATA_DIR / "handbook.json"
    handbook = Handbook.from_json(json_path)

    assert handbook.search("how is the cafeteria food?") is None
    assert handbook.search("") is None
    assert handbook.search("random unknown words that do not exist") is None


def test_handbook_missing_file_raises_data_error(tmp_path: Path) -> None:
    """Missing JSON file must raise DataError instead of raw FileNotFoundError."""
    missing_path = tmp_path / "non_existent.json"
    with pytest.raises(DataError, match=r"handbook file not found"):
        Handbook.from_json(missing_path)


def test_handbook_malformed_json_raises_data_error(tmp_path: Path) -> None:
    """Malformed JSON syntax must raise DataError."""
    bad_json = tmp_path / "bad_syntax.json"
    bad_json.write_text("{not a valid json}", encoding="utf-8")

    with pytest.raises(DataError, match=r"invalid handbook JSON"):
        Handbook.from_json(bad_json)


def test_handbook_invalid_structure_raises_data_error(tmp_path: Path) -> None:
    """JSON structure that is not a list must raise DataError."""
    dict_json = tmp_path / "not_list.json"
    dict_json.write_text('{"rules": []}', encoding="utf-8")

    with pytest.raises(DataError, match=r"expected JSON list"):
        Handbook.from_json(dict_json)


def test_handbook_missing_fields_raises_data_error(tmp_path: Path) -> None:
    """JSON rule item missing required keys must raise DataError."""
    bad_rule_json = tmp_path / "bad_rule.json"
    bad_rule_json.write_text(json.dumps([{"id": "R1", "title": "Incomplete"}]), encoding="utf-8")

    with pytest.raises(DataError, match=r"missing field"):
        Handbook.from_json(bad_rule_json)


def test_handbook_aliases() -> None:
    """Handbook.load and find_rule must function as aliases."""
    json_path = DATA_DIR / "handbook.json"
    hb1 = Handbook.from_json(json_path)
    hb2 = Handbook.load(json_path)
    assert len(hb1.rules) == len(hb2.rules)

    query = "register thesis"
    assert hb1.search(query) == hb1.find_rule(query)
