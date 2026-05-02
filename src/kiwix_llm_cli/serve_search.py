"""kiwix-serve HTTP API search implementation"""

import time
import xml.etree.ElementTree as ET
from typing import List, Optional

import httpx

from .libzim_search import SearchResult, SearchResultList


class ServeSearcher:
    def __init__(self, base_url: str, zim_name: Optional[str] = None):
        self.base_url = base_url.rstrip("/")
        self.zim_name = zim_name
        self._catalog_name = zim_name
        self.client = httpx.Client(timeout=30.0)

        if zim_name is None:
            self.zim_name, self._catalog_name = self._get_zim_info()

    def search(self, query: str, limit: int = 10) -> SearchResultList:
        start = time.time()

        params = {
            "pattern": query,
            "books.name": self.zim_name,
            "pageLength": limit,
            "format": "xml",
        }

        try:
            resp = self.client.get(f"{self.base_url}/search", params=params)
            resp.raise_for_status()

            results = self._parse_search_xml(resp.text)
            count = len(results)

        except Exception:
            results = []
            count = 0

        elapsed_ms = (time.time() - start) * 1000

        return SearchResultList(results=results, count=count, elapsed_ms=elapsed_ms)

    def suggest(self, term: str, limit: int = 10) -> SearchResultList:
        start = time.time()

        params = {"content": self.zim_name, "term": term, "count": limit}

        try:
            resp = self.client.get(f"{self.base_url}/suggest", params=params)
            resp.raise_for_status()

            data = resp.json()
            results = []
            for item in data[:limit]:
                if isinstance(item, dict) and item.get("kind") == "path":
                    results.append(
                        SearchResult(
                            path=item.get("path", ""), title=item.get("value", "")
                        )
                    )

            count = len(results)

        except Exception:
            results = []
            count = 0

        elapsed_ms = (time.time() - start) * 1000

        return SearchResultList(results=results, count=count, elapsed_ms=elapsed_ms)

    def info(self) -> dict:
        try:
            resp = self.client.get(f"{self.base_url}/catalog/v2/entries?count=-1")
            resp.raise_for_status()

            for entry in self._parse_catalog_xml(resp.text):
                if entry.get("name") == self._catalog_name:
                    return entry

        except Exception:
            pass

        return {}

    def list_books(self) -> List[dict]:
        try:
            resp = self.client.get(f"{self.base_url}/catalog/v2/entries?count=-1")
            resp.raise_for_status()
            return self._parse_catalog_xml(resp.text)
        except Exception:
            return []

    def get_article(self, title: str) -> str:
        try:
            resp = self.client.get(f"{self.base_url}/content/{self.zim_name}/{title}")
            resp.raise_for_status()
            return resp.text
        except Exception as e:
            raise ValueError(f"Article not found: {title}") from e

    def _get_zim_info(self) -> tuple:
        try:
            resp = self.client.get(f"{self.base_url}/catalog/v2/entries?count=1")
            resp.raise_for_status()
            entries = self._parse_catalog_xml(resp.text)
            if entries:
                entry = entries[0]
                catalog_name = entry.get("name", "")
                content_name = entry.get("content_name", catalog_name)
                return content_name, catalog_name
        except Exception:
            pass
        return "", ""

    def _parse_search_xml(self, xml: str) -> List[SearchResult]:
        results = []
        try:
            root = ET.fromstring(xml)
            for item in root.findall(".//item"):
                title_elem = item.find("title")
                link_elem = item.find("link")
                desc_elem = item.find("description")

                title: str = title_elem.text or "" if title_elem is not None else ""
                link: str = link_elem.text or "" if link_elem is not None else ""
                snippet: str = desc_elem.text or "" if desc_elem is not None else ""

                path: str = link.split("/content/")[-1] if "/content/" in link else link

                results.append(SearchResult(path=path, title=title, snippet=snippet))
        except Exception:
            pass

        return results

    def _parse_catalog_xml(self, xml: str) -> List[dict]:
        entries = []
        try:
            root = ET.fromstring(xml)
            for entry in root.findall(".//{http://www.w3.org/2005/Atom}entry"):
                info = {}
                for child in entry:
                    tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
                    if tag == "name":
                        info["name"] = child.text
                    elif tag == "title":
                        info["title"] = child.text
                    elif tag == "language":
                        info["language"] = child.text
                    elif tag == "summary":
                        info["description"] = child.text
                    elif tag == "articleCount":
                        info["article_count"] = int(child.text) if child.text else 0
                    elif tag == "link":
                        href = child.get("href", "")
                        rel = child.get("rel", "")
                        link_type = child.get("type", "")
                        length = child.get("length", "")
                        if rel == "" and href.startswith("/content/"):
                            content_name = href.split("/content/")[-1].strip("/")
                            info["content_name"] = content_name
                        if link_type == "application/x-zim" and length:
                            info["size"] = int(length)
                    elif tag == "author":
                        for author_child in child:
                            author_tag = (
                                author_child.tag.split("}")[-1]
                                if "}" in author_child.tag
                                else author_child.tag
                            )
                            if author_tag == "name":
                                info["creator"] = author_child.text
                    elif tag == "publisher":
                        for pub_child in child:
                            pub_tag = (
                                pub_child.tag.split("}")[-1]
                                if "}" in pub_child.tag
                                else pub_child.tag
                            )
                            if pub_tag == "name":
                                info["publisher"] = pub_child.text
                    elif tag == "updated":
                        info["date"] = child.text
                if info.get("name"):
                    entries.append(info)
        except Exception:
            pass

        return entries

    def close(self):
        self.client.close()
