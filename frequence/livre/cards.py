#!/usr/bin/env python3
"""Load and validate card JSON.

A card declares CONTENT ONLY. Layout belongs to render.py — a card file never
says where anything goes on the paper.
"""
import glob
import json
import os

REQUIRED = ("id", "tier", "order", "title_fr", "title_el", "accent", "items")
ITEM_REQUIRED = ("fr", "key")


class CardError(Exception):
    pass


def load_card(path):
    """Read one card JSON file, validate it, return the dict."""
    try:
        card = json.load(open(path, encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise CardError(f"{path}: invalid JSON: {e}") from e

    for field in REQUIRED:
        if field not in card:
            raise CardError(f"{path}: missing required field {field!r}")

    if card["tier"] not in (1, 2, 3):
        raise CardError(f"{path}: tier must be 1, 2 or 3, got {card['tier']!r}")

    if not isinstance(card["items"], list) or not card["items"]:
        raise CardError(f"{path}: items must be a non-empty list")

    for i, item in enumerate(card["items"]):
        for field in ITEM_REQUIRED:
            if field not in item:
                raise CardError(f"{path}: item {i} missing {field!r}")
        item.setdefault("el", None)
        item.setdefault("icon", None)

    card.setdefault("example", None)
    return card


def load_all(dirpath):
    """Every card in a directory, sorted by tier then order."""
    out = [load_card(p) for p in sorted(glob.glob(os.path.join(dirpath, "*.json")))]
    return sorted(out, key=lambda c: (c["tier"], c["order"]))
