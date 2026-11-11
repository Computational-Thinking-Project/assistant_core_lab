"""Offline BM25 retrieval adapted from the Lab 06 lecturer starter."""

from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass
from typing import Protocol

from assistant_core.rag.chunker import Chunk

STOP = frozenset(
    "a an and are at be by can do for from how i in is it my of on or the to what when where who with".split()
)


def tokenize(text: str) -> list[str]:
    """Lowercase words and remove the lecturer's stop words; no stemming."""
    return [token for token in re.findall(r"\w+", text.lower()) if token not in STOP]


@dataclass(frozen=True)
class Hit:
    chunk: Chunk
    score: float


class Index(Protocol):
    def search(self, query: str, k: int = 3) -> list[Hit]: ...


class BM25Index:
    def __init__(self, chunks: list[Chunk], k1: float = 1.5, b: float = 0.75):
        self.chunks = list(chunks)
        self.k1, self.b = k1, b
        self.docs = [tokenize(chunk.title + " " + chunk.text) for chunk in self.chunks]
        self.avgdl = sum(map(len, self.docs)) / max(len(self.docs), 1)
        document_frequency = Counter(token for document in self.docs for token in set(document))
        count = len(self.docs)
        self.idf = {
            token: math.log(1 + (count - frequency + 0.5) / (frequency + 0.5))
            for token, frequency in document_frequency.items()
        }
        self.tf = [Counter(document) for document in self.docs]

    def search(self, query: str, k: int = 3) -> list[Hit]:
        """Return positive-score top-k hits; equal scores retain chunk order."""
        if k <= 0 or not self.avgdl:
            return []
        tokens = tokenize(query)
        if not tokens:
            return []
        scores = []
        for document, frequencies in zip(self.docs, self.tf, strict=True):
            length = len(document)
            score = sum(
                self.idf.get(token, 0)
                * frequencies[token]
                * (self.k1 + 1)
                / (frequencies[token] + self.k1 * (1 - self.b + self.b * length / self.avgdl))
                for token in tokens
                if token in frequencies
            )
            scores.append(score)
        ranked = sorted(range(len(scores)), key=lambda position: -scores[position])[:k]
        return [Hit(self.chunks[position], round(scores[position], 3)) for position in ranked if scores[position] > 0]


def make_index(kind: str, chunks: list[Chunk]) -> Index:
    """Build the BM25 baseline; other retrieval kinds are outside this module."""
    if kind != "bm25":
        raise ValueError(f"Unsupported retrieval kind: {kind!r}; expected 'bm25'")
    return BM25Index(chunks)
