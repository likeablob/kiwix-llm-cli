"""Output formatter"""

from rich.console import Console
from rich.text import Text

from .libzim_search import SearchResultList

console = Console()


def format_search_result(results: SearchResultList) -> None:
    console.print(f"{results.count} results ({results.elapsed_ms:.1f}ms)")
    for i, r in enumerate(results.results, 1):
        text = Text()
        text.append(f"{i}. ", style="dim")
        text.append(r.title, style="bold")
        if r.path:
            text.append(f" [{r.path}]", style="dim")
        console.print(text)


def format_suggest_result(results: SearchResultList) -> None:
    console.print(f"{results.count} results")
    titles = [r.title for r in results.results if r.title]
    if titles:
        console.print(", ".join(titles))


def format_info(info: dict) -> None:
    console.print(f"ZIM: {info.get('title', 'N/A')}", style="bold")
    console.print(f"  Language: {info.get('language', 'N/A')}")
    console.print(f"  Creator: {info.get('creator', 'N/A')}")
    console.print(f"  Date: {info.get('date', 'N/A')}")
    console.print(f"  Articles: {info.get('article_count', 'N/A')}")
    console.print(f"  Fulltext: {info.get('has_fulltext_index', False)}")
    console.print(f"  Title index: {info.get('has_title_index', False)}")
