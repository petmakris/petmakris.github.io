import json, os, re, tempfile
import build, topdf

CARD = {
    "id": "t", "tier": 1, "order": 1,
    "title_fr": "Test", "title_el": "δοκιμή", "accent": "#B5531F",
    "example": None,
    "items": [{"fr": "sur", "el": "πάνω σε", "key": "on_box"}],
}

def _fixture(d, **over):
    c = dict(CARD); c.update(over)
    json.dump(c, open(os.path.join(d, f"{c['id']}.json"), "w", encoding="utf-8"),
              ensure_ascii=False)

def _check_self_contained(html_src):
    """Verify HTML is fully self-contained with no external references.

    Permits:
    - data: URIs (inlined fonts, images)
    - Fragment references (#anchor)
    - Inline SVG and scripts

    Rejects:
    - http://, https://, // (protocol-relative) URLs
    - @import of external resources
    - url() with external origins or relative paths
    - src= or href= pointing outside document
    - xlink:href pointing outside document
    """
    issues = []

    # Check for http://, https://, and protocol-relative // URLs in attributes
    for match in re.finditer(r'(?:href|src)\s*=\s*["\']([^"\']+)["\']', html_src):
        url_content = match.group(1)
        # Allow only: data: URIs and fragments
        if not url_content.startswith('data:') and not url_content.startswith('#'):
            if 'http://' in url_content or 'https://' in url_content or url_content.startswith('//'):
                issues.append(f"{match.group().split('=')[0]}= with external URL: {url_content}")

    # Check for @import (excluding ones pointing to data: URIs)
    for match in re.finditer(r'@import\s+["\']?(?!data:)([^"\';\n]+)', html_src):
        content = match.group(0)
        if not 'data:' in content:
            issues.append(f"@import found: {content}")

    # Check for url() with non-data: URIs and non-fragments
    for match in re.finditer(r'url\s*\(\s*([^)]+)\s*\)', html_src):
        url_content = match.group(1).strip('\'"')
        if not url_content.startswith('data:') and not url_content.startswith('#'):
            issues.append(f"url() with external/relative path: {url_content}")

    # Check for xlink:href (excluding data: and fragments)
    for match in re.finditer(r'xlink:href\s*=\s*["\']([^"\']+)["\']', html_src):
        url_content = match.group(1)
        if not url_content.startswith('data:') and not url_content.startswith('#'):
            issues.append(f"xlink:href with external/relative path: {url_content}")

    if issues:
        raise AssertionError("HTML is not self-contained:\n" + "\n".join(issues))

def test_build_writes_html_and_pdf():
    with tempfile.TemporaryDirectory() as d:
        cd = os.path.join(d, "cards"); os.makedirs(cd)
        _fixture(cd)
        h, p = build.build(cd, os.path.join(d, "out"))
        assert os.path.exists(h) and os.path.exists(p)
        assert topdf.page_count(p) >= 1

def test_html_is_self_contained():
    with tempfile.TemporaryDirectory() as d:
        cd = os.path.join(d, "cards"); os.makedirs(cd)
        _fixture(cd)
        h, _ = build.build(cd, os.path.join(d, "out"))
        src = open(h, encoding="utf-8").read()
        _check_self_contained(src)

def test_tier_filter_selects_cards():
    with tempfile.TemporaryDirectory() as d:
        cd = os.path.join(d, "cards"); os.makedirs(cd)
        _fixture(cd, id="a", tier=1, title_fr="TierOne")
        _fixture(cd, id="b", tier=3, title_fr="TierThree")
        h, _ = build.build(cd, os.path.join(d, "out"), tiers=(1,))
        src = open(h, encoding="utf-8").read()
        assert src.count('class="card"') == 1
        assert "TierOne" in src  # tier-1 card included
        assert "TierThree" not in src  # tier-3 card excluded

def test_build_return_value():
    with tempfile.TemporaryDirectory() as d:
        cd = os.path.join(d, "cards"); os.makedirs(cd)
        _fixture(cd)
        out = os.path.join(d, "out")
        h, p = build.build(cd, out)
        assert h == os.path.join(out, "livre.html")
        assert p == os.path.join(out, "livre.pdf")
        assert os.path.isabs(h)
        assert os.path.isabs(p)

def test_build_title_reaches_html():
    with tempfile.TemporaryDirectory() as d:
        cd = os.path.join(d, "cards"); os.makedirs(cd)
        _fixture(cd)
        custom_title = "Mon Livre Personnalisé"
        h, _ = build.build(cd, os.path.join(d, "out"), title=custom_title)
        src = open(h, encoding="utf-8").read()
        assert custom_title in src

def test_build_creates_missing_out_dir():
    with tempfile.TemporaryDirectory() as d:
        cd = os.path.join(d, "cards"); os.makedirs(cd)
        _fixture(cd)
        out = os.path.join(d, "deeply", "nested", "out")
        assert not os.path.exists(out)
        h, p = build.build(cd, out)
        assert os.path.exists(out)
        assert os.path.exists(h)
        assert os.path.exists(p)

def test_build_prints_summary(capsys):
    with tempfile.TemporaryDirectory() as d:
        cd = os.path.join(d, "cards"); os.makedirs(cd)
        _fixture(cd, id="a", tier=1)
        _fixture(cd, id="b", tier=1)
        h, _ = build.build(cd, os.path.join(d, "out"))
        captured = capsys.readouterr()
        # Extract and assert the actual numbers from the summary line
        match = re.search(r'(\d+) cards,\s+(\d+) items,\s+(\d+) pages', captured.out)
        assert match is not None
        cards, items, pages = int(match.group(1)), int(match.group(2)), int(match.group(3))
        assert cards == 2  # two cards created
        assert items == 2  # each fixture has 1 item, 2 total
        assert pages >= 1  # at least one page

def test_scanner_rejects_absolute_external_url():
    with tempfile.TemporaryDirectory() as d:
        cd = os.path.join(d, "cards"); os.makedirs(cd)
        _fixture(cd)
        h, _ = build.build(cd, os.path.join(d, "out"))
        src = open(h, encoding="utf-8").read()
        # Inject a malicious absolute URL
        bad_src = src.replace('</body>', '<script src="https://evil.com/malware.js"></script></body>')
        try:
            _check_self_contained(bad_src)
            assert False, "Scanner should have rejected https:// URL"
        except AssertionError as e:
            assert "external URL" in str(e)

def test_strict_fails_on_bad_explicit_icon():
    with tempfile.TemporaryDirectory() as d:
        cd = os.path.join(d, "cards"); os.makedirs(cd)
        _fixture(cd, items=[{"fr": "manger", "el": "τρώω", "key": "eat",
                              "icon": "FFFFFF"}])
        try:
            build.build(cd, os.path.join(d, "out"), strict=True)
            assert False, "strict mode should have refused the bad icon"
        except SystemExit as e:
            assert "manger" in str(e)
            assert "FFFFFF" in str(e)

def test_strict_passes_on_legitimate_placeholder():
    """A word with no icon (no `icon` key, no keyword match) is a real gap,
    not a typo — strict mode must not flag it."""
    with tempfile.TemporaryDirectory() as d:
        cd = os.path.join(d, "cards"); os.makedirs(cd)
        _fixture(cd, items=[{"fr": "le coude", "el": "ο αγκώνας", "key": "elbow"}])
        h, p = build.build(cd, os.path.join(d, "out"), strict=True)
        assert os.path.exists(h) and os.path.exists(p)

def test_scanner_rejects_protocol_relative_url():
    with tempfile.TemporaryDirectory() as d:
        cd = os.path.join(d, "cards"); os.makedirs(cd)
        _fixture(cd)
        h, _ = build.build(cd, os.path.join(d, "out"))
        src = open(h, encoding="utf-8").read()
        # Inject a malicious protocol-relative URL
        bad_src = src.replace('</body>', '<script src="//evil.cdn.com/x.js"></script></body>')
        try:
            _check_self_contained(bad_src)
            assert False, "Scanner should have rejected // protocol-relative URL"
        except AssertionError as e:
            assert "external URL" in str(e)
