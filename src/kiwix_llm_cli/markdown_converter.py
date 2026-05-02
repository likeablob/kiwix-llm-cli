"""HTML to Markdown converter for ZIM content"""

import re
import urllib.parse

from bs4 import BeautifulSoup
from markdownify import MarkdownConverter


class ZimMarkdownConverter(MarkdownConverter):
    """Custom converter for ZIM Wikipedia HTML"""

    def convert_style(self, el, text, parent_tags):
        return ""

    def convert_script(self, el, text, parent_tags):
        return ""

    def convert_a(self, el, text, parent_tags):
        href = el.get("href", "")
        if href:
            href = urllib.parse.unquote(href)
        return f"[{text}]({href})"


def html_to_markdown(html: str, clean: bool = True) -> str:
    """Convert ZIM HTML to clean Markdown"""
    if clean:
        soup = BeautifulSoup(html, "html.parser")
        remove_selectors = [
            "style",
            "script",
            ".mw-editsection",
            ".reference",
            ".noprint",
            ".navbox",
            ".infobox",
            ".ambox",
            ".mbox",
            ".sidebar",
            "#footer",
            "#mw-navigation",
        ]
        for selector in remove_selectors:
            for tag in soup.select(selector):
                tag.decompose()
        html = str(soup)

    converter = ZimMarkdownConverter(heading_style="ATX", strip=["script", "style"])
    markdown = converter.convert(html)

    markdown = re.sub(r"\n{3,}", "\n\n", markdown)
    markdown = markdown.strip()

    return markdown
