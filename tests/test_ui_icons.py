"""Lab 08 Homework H1 (Tam): prove or replace the AI-written UI icon helpers.

`svg_data_uri()` and `avatar_for()` were written with AI help in Lab 07 (see docs/ai-use-log.md,
2026-11-18). These tests cover normal use plus edge cases: empty input, zero-byte files, very large
files, Vietnamese file names, wrong types and paths outside the assets folder.
"""

from __future__ import annotations

import base64
from pathlib import Path

import pytest

from ui.icons import ASSETS_DIR, ASSISTANT_AVATAR, USER_AVATAR, avatar_for, svg_data_uri

SVG = b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M0 0h24v24H0z"/></svg>'
PREFIX = "data:image/svg+xml;base64,"


def _decode(uri: str) -> bytes:
    assert uri.startswith(PREFIX)
    return base64.b64decode(uri[len(PREFIX) :], validate=True)


@pytest.mark.parametrize("name", ["thumbs-up.svg", "thumbs-down.svg"])
def test_shipped_assets_round_trip(name: str) -> None:
    assert _decode(svg_data_uri(name)) == (ASSETS_DIR / name).read_bytes()


def test_vietnamese_file_name(tmp_path: Path) -> None:
    (tmp_path / "biểu-tượng-thích.svg").write_bytes(SVG)
    assert _decode(svg_data_uri("biểu-tượng-thích.svg", assets_dir=tmp_path)) == SVG


def test_very_large_svg_is_encoded_completely(tmp_path: Path) -> None:
    big = SVG[:-6] + b"<!--" + b"x" * 1_000_000 + b"-->" + b"</svg>"
    (tmp_path / "big.svg").write_bytes(big)
    assert _decode(svg_data_uri("big.svg", assets_dir=tmp_path)) == big


@pytest.mark.parametrize("name", ["", "   "])
def test_empty_file_name_is_rejected(name: str) -> None:
    with pytest.raises(ValueError):
        svg_data_uri(name)


def test_zero_byte_svg_is_rejected(tmp_path: Path) -> None:
    (tmp_path / "empty.svg").write_bytes(b"")
    with pytest.raises(ValueError):
        svg_data_uri("empty.svg", assets_dir=tmp_path)


@pytest.mark.parametrize("name", ["../app.py", "../../README.md", "sub/../../app.py"])
def test_path_outside_assets_is_rejected(name: str) -> None:
    with pytest.raises(ValueError):
        svg_data_uri(name)


def test_absolute_path_is_rejected(tmp_path: Path) -> None:
    secret = tmp_path / "secret.svg"
    secret.write_bytes(SVG)
    with pytest.raises(ValueError):
        svg_data_uri(str(secret))


def test_non_svg_file_is_rejected(tmp_path: Path) -> None:
    (tmp_path / "notes.txt").write_bytes(b"not an icon")
    with pytest.raises(ValueError):
        svg_data_uri("notes.txt", assets_dir=tmp_path)


def test_missing_asset_raises_file_not_found() -> None:
    with pytest.raises(FileNotFoundError):
        svg_data_uri("does-not-exist.svg")


@pytest.mark.parametrize("name", [None, 0, 42, b"thumbs-up.svg"])
def test_wrong_type_is_rejected(name: object) -> None:
    with pytest.raises(TypeError):
        svg_data_uri(name)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("role", "expected"),
    [
        ("user", USER_AVATAR),
        ("assistant", ASSISTANT_AVATAR),
        ("", ASSISTANT_AVATAR),
        ("người dùng", ASSISTANT_AVATAR),
        (None, ASSISTANT_AVATAR),
        (0, ASSISTANT_AVATAR),
    ],
)
def test_avatar_for_roles(role: object, expected: str) -> None:
    assert avatar_for(role) == expected  # type: ignore[arg-type]
