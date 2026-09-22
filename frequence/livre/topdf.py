#!/usr/bin/env python3
"""HTML -> A4 PDF via headless Chromium.

Chromium is the reference renderer because the HTML is also the artefact you
open in a browser, so the print must match what the browser shows. WeasyPrint
was evaluated and is degraded: it lacks color-mix(), so every tint vanishes.
"""
import asyncio
import os
import re
import sys


async def _render(html_path, pdf_path):
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto(f"file://{os.path.abspath(html_path)}")
        await page.emulate_media(media="print")
        await page.pdf(path=pdf_path, format="A4",
                       print_background=True, prefer_css_page_size=True)
        await browser.close()


def render(html_path, pdf_path):
    """Render one HTML file to A4 PDF. Overwrites pdf_path."""
    asyncio.run(_render(html_path, pdf_path))


def page_count(pdf_path):
    """Number of pages in a PDF, by counting page objects."""
    data = open(pdf_path, "rb").read()
    return len(re.findall(rb"/Type\s*/Page[^s]", data))


if __name__ == "__main__":
    for arg in sys.argv[1:]:
        out = arg.replace(".html", ".pdf")
        render(arg, out)
        print(f"{out}  {os.path.getsize(out)//1024} KB  {page_count(out)} pages")
