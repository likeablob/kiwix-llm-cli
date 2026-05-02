"""OPDS catalog parsing for library.kiwix.org"""

import re
from dataclasses import dataclass
from typing import Optional

import feedparser

LIBRARY_URL = "https://library.kiwix.org"
OPDS_ENTRIES_URL = f"{LIBRARY_URL}/catalog/v2/entries"


@dataclass
class ZimEntry:
    name: str
    title: str
    language: str
    category: str
    flavour: str
    tags: list[str]
    article_count: int
    media_count: int
    size: int
    meta4_url: str
    zim_id: str


def strip_date_suffix(zim_name: str) -> str:
    match = re.search(r"^(.+)_(\d{4}-\d{2}(?:-\d{2})?)$", zim_name)
    if match:
        return match.group(1)
    return zim_name


def parse_zim_name_from_url(url: str) -> str:
    match = re.search(r"/([^/]+)\.zim\.meta4$", url)
    if match:
        return match.group(1)
    match = re.search(r"/content/([^/]+)$", url)
    if match:
        return match.group(1)
    return ""


def parse_tags(tags_data: list[dict]) -> list[str]:
    all_tags = []
    for tag in tags_data:
        term = tag.get("term", "")
        if ";" in term:
            all_tags.extend(term.split(";"))
        else:
            all_tags.append(term)
    return [t for t in all_tags if t and not t.startswith("_")]


def parse_category(tags: list[str]) -> str:
    for tag in tags:
        if "category:" in tag:
            return tag.split(":")[-1]
    if tags:
        return tags[0]
    return ""


def parse_entry(entry: dict) -> Optional[ZimEntry]:
    meta4_url = ""
    size = 0
    for link in entry.get("links", []):
        href = link.get("href", "")
        if "meta4" in href:
            meta4_url = href
            size = int(link.get("length", 0))
            break

    if not meta4_url:
        return None

    name = parse_zim_name_from_url(meta4_url)

    tags_data = entry.get("tags", [])
    tags = parse_tags(tags_data)

    return ZimEntry(
        name=name,
        title=entry.get("title", ""),
        language=entry.get("language", ""),
        category=parse_category(tags),
        flavour=entry.get("flavour", ""),
        tags=tags,
        article_count=int(entry.get("articlecount", 0)),
        media_count=int(entry.get("mediacount", 0)),
        size=size,
        meta4_url=meta4_url,
        zim_id=entry.get("id", "").replace("urn:uuid:", ""),
    )


def search_entries(
    lang: Optional[str] = None,
    category: Optional[str] = None,
    name: Optional[str] = None,
    q: Optional[str] = None,
    count: int = 10,
    start: int = 0,
) -> list[ZimEntry]:
    params = []
    if lang:
        params.append(f"lang={lang}")
    if category:
        params.append(f"category={category}")
    if name:
        params.append(f"name={name}")
    if q:
        params.append(f"q={q}")
    params.append(f"count={count}")
    params.append(f"start={start}")

    url = f"{OPDS_ENTRIES_URL}?{'&'.join(params)}"
    feed = feedparser.parse(url)

    entries = []
    for entry in feed.entries:
        zim_entry = parse_entry(entry)
        if zim_entry:
            entries.append(zim_entry)

    return entries
