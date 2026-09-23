#!/usr/bin/env python3
"""Fetch the OpenMoji colour set and ship only the codepoints the book names.

Why a script and not a one-off: the book shipped 321 SVGs picked by hand, and
every card key that did not happen to match one of them rendered an empty
gutter — 345 of 635 word rows, which is how a numbers card ended up with no
numbers and a transport card with no bus. Icons are now assigned explicitly in
the card JSON, so the shipped set is derivable: it is exactly the set of
`icon` values in data/, and this script is what derives it.

The full upstream set is 4495 files and 23MB. Shipping all of it would also
re-arm the keyword matcher against 3620 tag strings, which is how `rouge` once
matched a smiling cat and `blanc` a zebra. Ship what is referenced, nothing
more.

  python3 scripts/sync-openmoji.py            # report what is missing/unused
  python3 scripts/sync-openmoji.py --write    # download and sync

Upstream: https://openmoji.org — CC BY-SA 4.0, via the `openmoji` npm package.
"""
import argparse
import glob
import io
import json
import os
import sys
import tarfile
import urllib.request

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHIPPED = os.path.join(HERE, "assets", "openmoji")
VERSION = "17.0.0"
TARBALL = f"https://registry.npmjs.org/openmoji/-/openmoji-{VERSION}.tgz"


def referenced():
    """Every `icon` codepoint named by a card."""
    out = set()
    for path in glob.glob(os.path.join(HERE, "data", "*", "*.json")):
        with open(path, encoding="utf-8") as f:
            for item in json.load(f)["items"]:
                if item.get("icon"):
                    out.add(item["icon"])
    return out


def shipped():
    return {f[:-4] for f in os.listdir(SHIPPED) if f.endswith(".svg")}


def fetch(codepoints):
    """Pull just the wanted members out of the upstream tarball, in one pass."""
    print(f"downloading {TARBALL} ...", file=sys.stderr)
    with urllib.request.urlopen(TARBALL, timeout=300) as r:
        blob = r.read()
    want = {f"package/color/svg/{c}.svg": c for c in codepoints}
    got = {}
    with tarfile.open(fileobj=io.BytesIO(blob), mode="r:gz") as tar:
        for member in tar:
            if member.name in want:
                got[want[member.name]] = tar.extractfile(member).read()
    return got


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true",
                    help="download the missing SVGs (does not delete unused)")
    args = ap.parse_args()

    want, have = referenced(), shipped()
    missing, unused = sorted(want - have), sorted(have - want)
    print(f"referenced {len(want)}, shipped {len(have)}, "
          f"missing {len(missing)}, unused {len(unused)}")

    # Unused files are reported, never deleted: the keyword index in
    # assets/openmoji-index.json resolves rows that carry no explicit `icon`,
    # so a codepoint can be in use without appearing in any card JSON.
    if unused:
        print("  unused (kept — may be reached through the keyword index):",
              " ".join(unused[:12]), "..." if len(unused) > 12 else "")
    if not missing:
        return 0
    print("  missing:", " ".join(missing))
    if not args.write:
        print("  re-run with --write to download them")
        return 1
    got = fetch(missing)
    for code, data in got.items():
        with open(os.path.join(SHIPPED, f"{code}.svg"), "wb") as f:
            f.write(data)
    print(f"  wrote {len(got)}")
    absent = [c for c in missing if c not in got]
    if absent:
        print("  NOT IN UPSTREAM:", " ".join(absent))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
