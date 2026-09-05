#!/usr/bin/env python3
"""Bake the transaction playground into one self-contained index.html.

Concatenates src/ in SRC_ORDER into the template's __SCRIPTS__ slot, stamps a
content hash into __BUILD__, and refuses to write if node reports a JS syntax
error. Same shape as frequence/build_game.py.
"""
import hashlib
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).parent
OUT = ROOT / "index.html"
TEMPLATE = ROOT / "index.template.html"

SRC_ORDER = [
    "src/seqrender.js",
    "src/rules.js",
    "src/engine.js",
    "src/diagram.js",
    "src/explain.js",
    "src/discoveries.js",
    "src/template.js",
    "src/claude.js",
    "src/scenarios/01-edit-calls-out.js",
    "src/scenarios/02-nightly-sweep.js",
    "src/scenarios/03-create-compensation.js",
    "src/scenarios/04-pool-exhaustion.js",
    "src/scenarios/05-proxy-bypass.js",
    "src/scenarios/06-suspension.js",
    "src/ui.js",
]


def check_js(script: str) -> None:
    node = shutil.which("node")
    if not node:
        print("note: node not found, skipping JS syntax check")
        return
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as f:
        f.write(script)
    r = subprocess.run([node, "--check", f.name], capture_output=True, text=True)
    Path(f.name).unlink(missing_ok=True)
    if r.returncode != 0:
        sys.exit("JS syntax error:\n" + r.stderr)


def main() -> None:
    parts = []
    for rel in SRC_ORDER:
        p = ROOT / rel
        if p.exists():
            parts.append(f"// ---- {rel} ----\n" + p.read_text(encoding="utf-8"))
    script = "\n".join(parts)
    check_js(script)
    template = TEMPLATE.read_text(encoding="utf-8")
    build = hashlib.sha256((template + script).encode("utf-8")).hexdigest()[:12]
    html = template.replace("__SCRIPTS__", script).replace("__BUILD__", build)
    OUT.write_text(html, encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)} ({len(html):,} bytes, build {build})")


if __name__ == "__main__":
    main()
