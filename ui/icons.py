"""Icon helpers for the Streamlit UI, kept free of Streamlit so they can be unit-tested."""

from __future__ import annotations

import base64
from pathlib import Path

ASSETS_DIR = Path(__file__).resolve().parent / "assets"
ASSISTANT_AVATAR = ":material/account_balance:"
USER_AVATAR = ":material/person:"


def svg_data_uri(filename: str, assets_dir: Path = ASSETS_DIR) -> str:
    """Encode a static SVG asset from ``assets_dir`` as a data URI for CSS icon buttons.

    Only a plain, non-empty ``.svg`` file name inside ``assets_dir`` is accepted, so a typo or a
    crafted name cannot embed another file of the repository into the page.
    """
    if not isinstance(filename, str):
        raise TypeError(f"filename must be str, not {type(filename).__name__}")
    name = filename.strip()
    if not name:
        raise ValueError("filename must not be empty")
    if Path(name).suffix.lower() != ".svg":
        raise ValueError(f"not an SVG asset: {filename!r}")
    base = Path(assets_dir).resolve()
    path = (base / name).resolve()
    if path.parent != base:
        raise ValueError(f"asset must be a file directly inside {base}: {filename!r}")
    data = path.read_bytes()
    if not data:
        raise ValueError(f"SVG asset is empty: {filename!r}")
    return "data:image/svg+xml;base64," + base64.b64encode(data).decode("ascii")


def avatar_for(role: str) -> str:
    """Return the Material Symbol icon identifier for a chat role."""
    return USER_AVATAR if role == "user" else ASSISTANT_AVATAR
