"""libzim direct search implementation"""

import os
import time
from contextlib import contextmanager
from pathlib import Path
from typing import List, NamedTuple

from libzim.reader import Archive
from libzim.search import Query, Searcher
from libzim.suggestion import SuggestionSearcher


@contextmanager
def suppress_libzim_output():
    devnull = open(os.devnull, "w")
    old_stdout = os.dup(1)
    old_stderr = os.dup(2)
    os.dup2(devnull.fileno(), 1)
    os.dup2(devnull.fileno(), 2)
    try:
        yield
    finally:
        os.dup2(old_stdout, 1)
        os.dup2(old_stderr, 2)
        devnull.close()


class SearchResult(NamedTuple):
    path: str
    title: str
    snippet: str = ""


class SearchResultList(NamedTuple):
    results: List[SearchResult]
    count: int
    elapsed_ms: float


class LibzimSearcher:
    def __init__(self, zim_path: Path):
        with suppress_libzim_output():
            self.archive = Archive(zim_path)
            self.searcher = Searcher(self.archive)
            self.suggestion_searcher = SuggestionSearcher(self.archive)

    def search(self, query: str, limit: int = 10) -> SearchResultList:
        start = time.time()

        with suppress_libzim_output():
            q = Query().set_query(query)
            search = self.searcher.search(q)
            count = search.getEstimatedMatches()
            results_raw = list(search.getResults(0, min(limit, count)))

        results = []
        for path in results_raw:
            try:
                entry = self.archive.get_entry_by_path(path)
                title = entry.title
                results.append(SearchResult(path=path, title=title))
            except Exception:
                results.append(SearchResult(path=path, title=path))

        elapsed_ms = (time.time() - start) * 1000

        return SearchResultList(results=results, count=count, elapsed_ms=elapsed_ms)

    def suggest(self, term: str, limit: int = 10) -> SearchResultList:
        start = time.time()

        with suppress_libzim_output():
            suggestion = self.suggestion_searcher.suggest(term)
            count = suggestion.getEstimatedMatches()
            results_raw = list(suggestion.getResults(0, min(limit, count)))

        results = []
        for path in results_raw:
            try:
                entry = self.archive.get_entry_by_path(path)
                title = entry.title
                results.append(SearchResult(path=path, title=title))
            except Exception:
                results.append(SearchResult(path=path, title=path))

        elapsed_ms = (time.time() - start) * 1000

        return SearchResultList(results=results, count=count, elapsed_ms=elapsed_ms)

    def info(self) -> dict:
        metadata = {}
        for key in [
            "Title",
            "Description",
            "Language",
            "Creator",
            "Publisher",
            "Date",
        ]:
            try:
                entry = self.archive.get_entry_by_path(f"M/{key}")
                metadata[key.lower()] = bytes(entry.get_item().content).decode("UTF-8")
            except Exception:
                metadata[key.lower()] = ""

        return {
            "filename": self.archive.filename,
            "title": metadata.get("title", ""),
            "description": metadata.get("description", ""),
            "language": metadata.get("language", ""),
            "creator": metadata.get("creator", ""),
            "publisher": metadata.get("publisher", ""),
            "date": metadata.get("date", ""),
            "article_count": self.archive.article_count,
            "has_fulltext_index": self.archive.has_fulltext_index,
            "has_title_index": self.archive.has_title_index,
        }

    def get_content(self, title: str) -> str:
        """Get article content as HTML"""
        try:
            entry = self.archive.get_entry_by_title(title)
            item = entry.get_item()
            content = item.content.tobytes().decode("utf-8", errors="ignore")
            return content
        except KeyError:
            raise ValueError(f"Article not found: {title}")
