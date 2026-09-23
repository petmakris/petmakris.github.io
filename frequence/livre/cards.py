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

    if card["tier"] not in (0, 1, 2, 3, 4):
        raise CardError(
            f"{path}: tier must be 0, 1, 2, 3 or 4, got {card['tier']!r}")

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
    _assert_unique_ids(out, dirpath)
    return sorted(out, key=lambda c: (c["tier"], c["order"]))


def _assert_unique_ids(loaded, where):
    """Two cards sharing an id make a load error untraceable to its file."""
    seen = {}
    for card in loaded:
        if card["id"] in seen:
            raise CardError(f"{where}: duplicate card id {card['id']!r}")
        seen[card["id"]] = True
