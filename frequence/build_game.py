#!/usr/bin/env python3
"""Generate the self-contained multi-language frequency vocabulary game (game.html).

Reads the per-language `word = translation` lists (frequency-ordered) and bakes
them all into a single offline HTML page. No server, no database — progress and
the chosen language live in the browser's localStorage.
"""
import hashlib
import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).parent          # blog/frequence (game source lives here)
OUT = ROOT.parent / "frequence" / "index.html"   # /frequence/ on the site; the root is the hub
SOURCES = {                       # language code -> translations file
    "fr": ROOT / "data" / "translations.txt",
    "es": ROOT / "data" / "translations.es.txt",
    "el": ROOT / "data" / "translations.el.txt",
    "it": ROOT / "data" / "translations.it.txt",
}


def load_words(path):
    words = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        word, _, trans = line.partition(" = ")
        word, trans = word.strip(), trans.strip()
        if word and trans:
            words.append([word, trans])
    return words


def check_js(html):
    """Fail the build if the page's <script> has a JS syntax error.

    Best-effort: needs `node`. Skipped (with a note) if node is absent.
    """
    node = shutil.which("node")
    if not node:
        print("note: node not found, skipping JS syntax check")
        return
    script = re.search(r"<script>(.*?)</script>", html, re.DOTALL).group(1)
    with tempfile.NamedTemporaryFile("w", suffix=".js", encoding="utf-8") as f:
        f.write(script)
        f.flush()
        r = subprocess.run([node, "--check", f.name], capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(f"JS syntax error in generated page:\n{r.stderr}")


def next_build_number(content_hash):
    """Monotonic build counter that advances only when the content changes.

    Stored in build_number.json (committed) so the number is stable across
    machines and no-op rebuilds. Returns the integer to stamp into the page.
    """
    vf = ROOT / "build_number.json"
    prev = {"build": 0, "hash": ""}
    if vf.exists():
        try:
            prev = json.loads(vf.read_text(encoding="utf-8"))
        except Exception:
            pass
    number = prev.get("build", 0)
    if prev.get("hash") != content_hash:        # content changed -> new build
        number += 1
    number = max(number, 1)
    vf.write_text(json.dumps({"build": number, "hash": content_hash}) + "\n", encoding="utf-8")
    return number


def main():
    by_lang = {code: load_words(path) for code, path in SOURCES.items()}
    data_json = json.dumps(by_lang, ensure_ascii=False, separators=(",", ":"))
    template = (ROOT / "game.template.html").read_text(encoding="utf-8")
    # Content-based build id: changes whenever the code or word data changes, so
    # a deployed page can detect that a newer build is live and reload itself.
    build_id = hashlib.sha1((template + data_json).encode("utf-8")).hexdigest()[:10]
    build_no = next_build_number(build_id)
    html = (template.replace("__DATA__", data_json)
                    .replace("__BUILD__", build_id)
                    .replace("__BUILDNO__", str(build_no)))
    check_js(html)
    OUT.write_text(html, encoding="utf-8")
    counts = ", ".join(f"{c}={len(w)}" for c, w in by_lang.items())
    print(f"wrote {OUT} (build #{build_no} {build_id}; {counts}; {OUT.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
