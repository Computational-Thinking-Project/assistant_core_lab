"""Knowledge sources: Office directory and Handbook.

Phụ trách: Thành viên 4 (Bội Anh @htbaax)
Phạm vi: Office, OfficeDirectory, Rule, Handbook
"""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    from assistant_core.errors import DataError
except (ImportError, AttributeError):
    try:
        from assistant_core.errors import AssistantError
    except (ImportError, AttributeError):

        class AssistantError(Exception):
            """Base exception for assistant_core."""

    class DataError(AssistantError):
        """A knowledge file is missing or malformed."""


__all__ = [
    "DataError",
    "Handbook",
    "Office",
    "OfficeDirectory",
    "Rule",
]


@dataclass(frozen=True)
class Office:
    """Office information containing location and working hours."""

    name: str
    room: str
    hours: str

    def get(self, key: str, default: Any = None) -> Any:
        """Allow dict-like attribute access for backwards compatibility."""
        return getattr(self, key, default)

    def __getitem__(self, key: str) -> Any:
        """Allow dict-like indexing access for backwards compatibility."""
        if hasattr(self, key):
            return getattr(self, key)
        raise KeyError(key)


class OfficeDirectory:
    """Directory for looking up office rooms and operating hours."""

    def __init__(self, offices: dict[str, Office]) -> None:
        self._offices = offices

    @classmethod
    def from_csv(cls, path: Path | str) -> OfficeDirectory:
        """Load office directory from a CSV file.

        Raises:
            DataError: If the file is missing or cannot be parsed.
        """
        csv_path = Path(path)
        try:
            with csv_path.open(encoding="utf-8", newline="") as f:
                rows = list(csv.DictReader(f))
        except FileNotFoundError as exc:
            raise DataError(f"office file not found: {csv_path}") from exc
        except (csv.Error, UnicodeDecodeError, OSError) as exc:
            raise DataError(f"failed to read office file {csv_path}: {exc}") from exc

        offices: dict[str, Office] = {}
        for row in rows:
            try:
                name = row["name"].strip()
                room = row["room"].strip()
                hours = row["hours"].strip()
                offices[name.lower()] = Office(name=name, room=room, hours=hours)
            except (KeyError, AttributeError) as exc:
                raise DataError(f"invalid office row in {csv_path}: missing field {exc}") from exc

        return cls(offices)

    @classmethod
    def load(cls, path: Path | str) -> OfficeDirectory:
        """Alias for from_csv to maintain compatibility across caller modules."""
        return cls.from_csv(path)

    @property
    def names(self) -> set[str]:
        """Return the set of lowercased office names for intent routing."""
        return set(self._offices.keys())

    @property
    def offices(self) -> dict[str, Office]:
        """Return a mapping copy of office name to Office object."""
        return dict(self._offices)

    def get_names(self) -> set[str]:
        """Convenience method returning names set."""
        return self.names

    def find(self, text: str) -> Office | None:
        """Find an office whose name appears as a substring in the input text."""
        t = text.lower()
        return next((office for name, office in self._offices.items() if name in t), None)

    def all(self) -> list[Office]:
        """Return all offices sorted by name."""
        return sorted(self._offices.values(), key=lambda office: office.name)


@dataclass(frozen=True)
class Rule:
    """Academic rule or regulation with identifier, title, and text content."""

    id: str
    title: str
    text: str

    def get(self, key: str, default: Any = None) -> Any:
        """Allow dict-like attribute access for backwards compatibility."""
        return getattr(self, key, default)

    def __getitem__(self, key: str) -> Any:
        """Allow dict-like indexing access for backwards compatibility."""
        if hasattr(self, key):
            return getattr(self, key)
        raise KeyError(key)


class Handbook:
    """Academic handbook repository providing rule retrieval."""

    def __init__(self, rules: list[Rule]) -> None:
        self._rules = list(rules)

    @classmethod
    def from_json(cls, path: Path | str) -> Handbook:
        """Load rules handbook from a JSON file.

        Raises:
            DataError: If the file is missing, invalid JSON, or missing required keys.
        """
        json_path = Path(path)
        try:
            with json_path.open(encoding="utf-8") as f:
                data = json.load(f)
        except FileNotFoundError as exc:
            raise DataError(f"handbook file not found: {json_path}") from exc
        except (json.JSONDecodeError, UnicodeDecodeError, OSError) as exc:
            raise DataError(f"invalid handbook JSON in {json_path}: {exc}") from exc

        if not isinstance(data, list):
            raise DataError(f"invalid handbook structure in {json_path}: expected JSON list")

        rules: list[Rule] = []
        for item in data:
            if not isinstance(item, dict):
                raise DataError(f"invalid rule item in {json_path}: expected JSON object")
            try:
                rule_id = str(item["id"]).strip()
                title = str(item["title"]).strip()
                text = str(item["text"]).strip()
                rules.append(Rule(id=rule_id, title=title, text=text))
            except KeyError as exc:
                raise DataError(f"invalid rule format in {json_path}: missing field {exc}") from exc

        return cls(rules)

    @classmethod
    def load(cls, path: Path | str) -> Handbook:
        """Alias for from_json to maintain compatibility across caller modules."""
        return cls.from_json(path)

    @property
    def rules(self) -> list[Rule]:
        """Return a copy of the list of loaded rules."""
        return list(self._rules)

    def search(self, query: str) -> Rule | None:
        """Find matching rule via keyword overlap for tokens longer than 3 characters."""
        words = query.lower().split()
        best: Rule | None = None
        best_score = 0

        for rule in self._rules:
            rule_text = rule.text.lower()
            score = sum(1 for w in words if len(w) > 3 and w in rule_text)
            if score > best_score:
                best_score = score
                best = rule

        if best is not None and best_score >= 1:
            return best
        return None

    def find_rule(self, query: str) -> Rule | None:
        """Alias for search method."""
        return self.search(query)
