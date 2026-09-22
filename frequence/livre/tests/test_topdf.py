import os, tempfile
import topdf

A4_PT = (595, 842)

def test_renders_a4_pdf():
    html = '<!doctype html><html><head><meta charset="utf-8">' \
           '<style>@page{size:A4;margin:0}</style></head>' \
           '<body><p>bonjour · καλημέρα</p></body></html>'
    with tempfile.TemporaryDirectory() as d:
        h = os.path.join(d, "t.html")
        p = os.path.join(d, "t.pdf")
        open(h, "w", encoding="utf-8").write(html)
        topdf.render(h, p)
        assert os.path.getsize(p) > 500
        assert topdf.page_count(p) == 1

def test_page_count_counts_pages():
    html = '<!doctype html><html><head><meta charset="utf-8">' \
           '<style>@page{size:A4;margin:0}.b{break-after:page}</style></head>' \
           '<body><div class="b">un</div><div class="b">deux</div><div>trois</div></body></html>'
    with tempfile.TemporaryDirectory() as d:
        h = os.path.join(d, "t.html")
        p = os.path.join(d, "t.pdf")
        open(h, "w", encoding="utf-8").write(html)
        topdf.render(h, p)
        assert topdf.page_count(p) == 3
