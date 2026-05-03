"""kiwix-llm-cli - Kiwix ZIM file search CLI for LLM coding agents"""

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

import httpx
from rich.console import Console
from rich.prompt import Confirm
from rich.table import Table

from . import __version__
from .config import DEFAULT_CONFIG_FILE, Settings, dump_config
from .discovery import discover_zim_files
from .downloader import download_zim, format_size
from .formatter import format_info, format_search_result, format_suggest_result
from .libzim_search import LibzimSearcher
from .markdown_converter import html_to_markdown
from .meta4 import parse_metalink4
from .opds import search_entries, strip_date_suffix
from .serve_search import ServeSearcher

console = Console()


def get_settings(config_path: Optional[Path] = None) -> Settings:
    return Settings.load(config_path=config_path)


def find_zim_file(
    zim_name: Optional[str] = None,
    settings: Optional[Settings] = None,
    include_cwd: bool = True,
) -> Optional[Path]:
    if not settings:
        settings = get_settings()

    discovered = discover_zim_files(
        search_dirs=settings.get_search_dirs(),
        include_cwd=include_cwd,
    )

    if zim_name:
        if zim_name in discovered:
            return Path(discovered[zim_name]["path"])
        return None

    if settings.default_zim and settings.default_zim in discovered:
        return Path(discovered[settings.default_zim]["path"])

    if discovered:
        first_name = list(discovered.keys())[0]
        return Path(discovered[first_name]["path"])

    return None


def get_backend(backend_arg: Optional[str], settings: Settings) -> str:
    if backend_arg:
        return backend_arg
    return settings.backend


def init_action(args):
    """Initialize configuration file."""
    settings = Settings.load(ignore_config=args.bare)

    output_path = args.path
    if output_path and output_path.is_dir():
        output_path = output_path / ".kiwix-llm-cli.yaml"
    if not output_path:
        if args.bare:
            output_path = None
        else:
            output_path = DEFAULT_CONFIG_FILE

    if output_path and output_path.exists():
        console.print(f"[yellow]Config file already exists: {output_path}[/yellow]")
        console.print(
            "Use --bare to output default values to stdout, or remove the file first."
        )
        sys.exit(1)

    if not args.bare:
        discovered = discover_zim_files(
            search_dirs=settings.get_search_dirs(),
            include_cwd=True,
        )
        if discovered:
            console.print(f"[green]Discovered {len(discovered)} ZIM files[/green]")
            for name, info in discovered.items():
                console.print(
                    f"  {name}: {info['path']} ({info.get('article_count', 'N/A')} articles)"
                )

            if not settings.default_zim and discovered:
                settings.default_zim = list(discovered.keys())[0]

    config_text = dump_config(settings, output_path)
    if output_path:
        console.print(f"[green]Config written to: {output_path}[/green]")
    else:
        print(config_text)


def list_action(args):
    """List ZIM files."""
    settings = get_settings(args.config)
    actual_backend = get_backend(args.backend, settings)
    actual_url = args.kiwix_api_url or settings.get_kiwix_api_url()

    if actual_backend == "api":
        searcher = ServeSearcher(actual_url)
        console.print(f"[dim]API: {actual_url}[/dim]")
        books = searcher.list_books()
        searcher.close()

        if not books:
            console.print("[yellow]No ZIM files found[/yellow]")
            return

        if args.format == "json":
            print(json.dumps(books, indent=2))
        elif args.format == "simple":
            for book in books:
                print(f"{book['name']}: {book['title']}")
        else:
            table = Table(title="ZIM Files (API)")
            table.add_column("Name", style="cyan")
            table.add_column("Title", style="green")
            table.add_column("Articles", justify="right")
            table.add_column("Size", justify="right")

            for book in books:
                table.add_row(
                    book.get("name", ""),
                    book.get("title", ""),
                    str(book.get("article_count", "N/A")),
                    format_size(book.get("size", 0)),
                )

            console.print(table)
    else:
        discovered = discover_zim_files(
            search_dirs=settings.get_search_dirs(),
            include_cwd=True,
        )

        if not discovered:
            console.print("[yellow]No ZIM files found[/yellow]")
            return

        if args.format == "json":
            print(json.dumps(discovered, indent=2))
        elif args.format == "simple":
            for name, info in discovered.items():
                print(f"{name}: {info['path']}")
        else:
            table = Table(title="Discovered ZIM Files")
            table.add_column("Name", style="cyan")
            table.add_column("Path", style="green")
            table.add_column("Articles", justify="right")
            table.add_column("Fulltext", justify="center")

            for name, info in discovered.items():
                table.add_row(
                    name,
                    info.get("path", ""),
                    str(info.get("article_count", "N/A")),
                    "✓" if info.get("has_fulltext_index") else "✗",
                )

            console.print(table)


def delete_action(args):
    """Delete ZIM files."""
    settings = get_settings(args.config)

    discovered = discover_zim_files(
        search_dirs=settings.get_search_dirs(),
        include_cwd=True,
    )

    if not discovered:
        console.print("[yellow]No ZIM files found[/yellow]")
        return

    to_delete = []
    for name in args.names:
        if name not in discovered:
            console.print(f"[red]ZIM file not found: {name}[/red]")
            sys.exit(1)
        to_delete.append(name)

    for name in to_delete:
        info = discovered[name]
        zim_path = Path(info["path"])
        size = info.get("filesize", 0)

        if not args.force:
            console.print(f'\n[bold]Delete "{name}"?[/bold]')
            console.print(f"  Path: {zim_path}")
            console.print(f"  Size: {format_size(size)}")

            if settings.default_zim == name:
                console.print(
                    f'[yellow]  Warning: "{name}" is set as default_zim in config.[/yellow]'
                )

            if not Confirm.ask("Proceed?", default=False):
                console.print(f"[dim]Skipped: {name}[/dim]")
                continue

        try:
            zim_path.unlink()
            console.print(f"[green]Deleted: {name}[/green]")
        except OSError as e:
            console.print(f"[red]Failed to delete {name}: {e}[/red]")
            sys.exit(1)


def install_skills_action(args):
    """Install skill files for coding agents."""
    from .skills import install_skills as _install_skills

    agents = args.agent or ["claude-code"]
    installed = _install_skills(agents=agents, target=args.target)

    if installed:
        console.print(f"[green]Installed skill to {len(installed)} location(s)[/green]")
        for path in installed:
            console.print(f"  {path}/SKILL.md")
    else:
        console.print("[red]Failed to install skill[/red]")
        sys.exit(1)


def search_action(args):
    """Full-text search in ZIM file."""
    settings = get_settings(args.config)
    actual_backend = get_backend(args.backend, settings)
    actual_url = args.kiwix_api_url or settings.get_kiwix_api_url()

    if actual_backend == "libzim":
        zim_path = None
        if args.zim:
            if Path(args.zim).exists():
                zim_path = Path(args.zim)
            else:
                zim_path = find_zim_file(args.zim, settings)

        if not zim_path:
            zim_path = find_zim_file(None, settings)

        if not zim_path:
            console.print("[red]ZIM file not found[/red]")
            sys.exit(1)

        console.print(f"[dim]ZIM: {zim_path}[/dim]")
        searcher = LibzimSearcher(zim_path)
        results = searcher.search(args.query, args.limit)
    else:
        searcher = ServeSearcher(actual_url)
        console.print(f"[dim]ZIM: {searcher.zim_name} @ {actual_url}[/dim]")
        results = searcher.search(args.query, args.limit)
        searcher.close()

    format_search_result(results)


def suggest_action(args):
    """Title suggestion search."""
    settings = get_settings(args.config)
    actual_backend = get_backend(args.backend, settings)
    actual_url = args.kiwix_api_url or settings.get_kiwix_api_url()

    if actual_backend == "libzim":
        zim_path = None
        if args.zim:
            if Path(args.zim).exists():
                zim_path = Path(args.zim)
            else:
                zim_path = find_zim_file(args.zim, settings)

        if not zim_path:
            zim_path = find_zim_file(None, settings)

        if not zim_path:
            console.print("[red]ZIM file not found[/red]")
            sys.exit(1)

        console.print(f"[dim]ZIM: {zim_path}[/dim]")
        searcher = LibzimSearcher(zim_path)
        results = searcher.suggest(args.term, args.limit)
    else:
        searcher = ServeSearcher(actual_url)
        console.print(f"[dim]ZIM: {searcher.zim_name} @ {actual_url}[/dim]")
        results = searcher.suggest(args.term, args.limit)
        searcher.close()

    format_suggest_result(results)


def info_action(args):
    """Show ZIM file information."""
    settings = get_settings(args.config)
    actual_backend = get_backend(args.backend, settings)
    actual_url = args.kiwix_api_url or settings.get_kiwix_api_url()

    if actual_backend == "libzim":
        zim_path = None
        if args.zim:
            if Path(args.zim).exists():
                zim_path = Path(args.zim)
            else:
                zim_path = find_zim_file(args.zim, settings)

        if not zim_path:
            zim_path = find_zim_file(None, settings)

        if not zim_path:
            console.print("[red]ZIM file not found[/red]")
            sys.exit(1)

        console.print(f"[dim]ZIM: {zim_path}[/dim]")
        searcher = LibzimSearcher(zim_path)
        data = searcher.info()
    else:
        searcher = ServeSearcher(actual_url)
        console.print(f"[dim]ZIM: {searcher.zim_name} @ {actual_url}[/dim]")
        data = searcher.info()
        searcher.close()

    format_info(data)


def get_action(args):
    """Get article content."""
    settings = get_settings(args.config)
    actual_backend = get_backend(args.backend, settings)
    actual_url = args.kiwix_api_url or settings.get_kiwix_api_url()

    if actual_backend == "api":
        searcher = ServeSearcher(actual_url)
        console.print(f"[dim]API: {actual_url}[/dim]")
        content = searcher.get_article(args.title)
        searcher.close()
    else:
        zim_path = None
        if args.zim:
            if Path(args.zim).exists():
                zim_path = Path(args.zim)
            else:
                zim_path = find_zim_file(args.zim, settings)

        if not zim_path:
            zim_path = find_zim_file(None, settings)

        if not zim_path:
            console.print("[red]ZIM file not found[/red]")
            sys.exit(1)

        console.print(f"[dim]ZIM: {zim_path}[/dim]")
        searcher = LibzimSearcher(zim_path)
        content = searcher.get_content(args.title)

    if args.format == "markdown":
        markdown = html_to_markdown(content)
        print(markdown)
    elif args.format == "html":
        print(content)
    else:
        print(content)


def remote_catalog_action(args):
    """Search library.kiwix.org catalog for ZIM files."""
    entries = search_entries(
        lang=args.lang,
        category=args.category,
        name=args.name,
        q=args.query,
        count=args.count,
    )

    if not entries:
        console.print("[yellow]No ZIM files found[/yellow]")
        return

    if args.format == "json":
        data = [
            {
                "name": e.name,
                "title": e.title,
                "size": e.size,
                "article_count": e.article_count,
                "category": e.category,
                "meta4_url": e.meta4_url,
            }
            for e in entries
        ]
        print(json.dumps(data, indent=2))
    elif args.format == "simple":
        for e in entries:
            print(f"{e.name}: {e.title} ({format_size(e.size)})")
    else:
        table = Table(title="Kiwix Library")
        table.add_column("Name", style="cyan")
        table.add_column("Title", style="green")
        table.add_column("Size", justify="right")
        table.add_column("Articles", justify="right")
        table.add_column("Category")

        for entry in entries:
            table.add_row(
                entry.name,
                entry.title,
                format_size(entry.size),
                str(entry.article_count),
                entry.category,
            )

        console.print(table)


def remote_download_action(args):
    """Download ZIM file from library.kiwix.org."""
    settings = get_settings(args.config)
    output_dir = args.output or settings.get_download_dir()

    console.print(f"[cyan]Searching for: {args.zim_name}[/cyan]")
    search_name = strip_date_suffix(args.zim_name)
    entries = search_entries(name=search_name, count=10)

    if not entries:
        console.print("[red]ZIM not found in library[/red]")
        sys.exit(1)

    exact_match = None
    for entry in entries:
        if entry.name == args.zim_name or entry.name == search_name:
            exact_match = entry
            break

    if not exact_match:
        exact_match = entries[0]

    entry = exact_match
    console.print(f"[green]Found: {entry.title} ({format_size(entry.size)})[/green]")

    console.print("[dim]Fetching download info...[/dim]")
    response = httpx.get(entry.meta4_url)
    metalink = parse_metalink4(response.text)

    if not metalink:
        console.print("[red]Failed to parse download info[/red]")
        sys.exit(1)

    try:
        path = download_zim(metalink, output_dir)
        console.print(f"[green]Downloaded to: {path}[/green]")
    except ValueError as e:
        console.print(f"[red]{e}[/red]")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="kiwix-llm-cli - Kiwix ZIM file search CLI for LLM coding agents",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("-c", "--config", type=Path, help="Config file path")
    parser.add_argument(
        "--version", action="version", version=f"kiwix-llm-cli {__version__}"
    )

    backend_parent = argparse.ArgumentParser(add_help=False)
    backend_parent.add_argument(
        "-b", "--backend", choices=["libzim", "api"], help="Backend to use"
    )
    backend_parent.add_argument("-u", "--kiwix-api-url", help="kiwix-serve API URL")

    zim_parent = argparse.ArgumentParser(add_help=False)
    zim_parent.add_argument("-z", "--zim", help="ZIM file name or path")

    subparsers = parser.add_subparsers(dest="command", help="Subcommands")

    init_parser = subparsers.add_parser("init", help="Initialize configuration file")
    init_parser.add_argument(
        "-p", "--path", type=Path, help="Config file or directory path"
    )
    init_parser.add_argument(
        "--bare", action="store_true", help="Output default values only"
    )
    init_parser.set_defaults(func=init_action)

    list_parser = subparsers.add_parser(
        "list", help="List ZIM files", parents=[backend_parent]
    )
    list_parser.add_argument(
        "-f", "--format", choices=["table", "json", "simple"], default="table"
    )
    list_parser.set_defaults(func=list_action)

    delete_parser = subparsers.add_parser("delete", help="Delete ZIM files")
    delete_parser.add_argument("names", nargs="+", help="ZIM file names to delete")
    delete_parser.add_argument(
        "-f", "--force", action="store_true", help="Skip confirmation"
    )
    delete_parser.set_defaults(func=delete_action)

    install_parser = subparsers.add_parser(
        "install-skills", help="Install skill files for coding agents"
    )
    install_parser.add_argument(
        "-a",
        "--agent",
        action="append",
        choices=["opencode", "claude-code"],
        help="Agent type (default: claude-code, can specify multiple)",
    )
    install_parser.add_argument(
        "-t", "--target", type=Path, help="Custom installation path"
    )
    install_parser.set_defaults(func=install_skills_action)

    search_parser = subparsers.add_parser(
        "search",
        help="Full-text search in ZIM file",
        parents=[backend_parent, zim_parent],
    )
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument(
        "-l", "--limit", type=int, default=10, help="Result limit"
    )
    search_parser.set_defaults(func=search_action)

    suggest_parser = subparsers.add_parser(
        "suggest", help="Title suggestion search", parents=[backend_parent, zim_parent]
    )
    suggest_parser.add_argument("term", help="Suggestion term")
    suggest_parser.add_argument(
        "-l", "--limit", type=int, default=10, help="Result limit"
    )
    suggest_parser.set_defaults(func=suggest_action)

    info_parser = subparsers.add_parser(
        "info", help="Show ZIM file information", parents=[backend_parent, zim_parent]
    )
    info_parser.set_defaults(func=info_action)

    get_parser = subparsers.add_parser(
        "get", help="Get article content", parents=[backend_parent, zim_parent]
    )
    get_parser.add_argument("title", help="Article title")
    get_parser.add_argument(
        "-f", "--format", choices=["markdown", "html", "raw"], default="markdown"
    )
    get_parser.set_defaults(func=get_action)

    remote_parser = subparsers.add_parser(
        "remote", help="Remote library operations (library.kiwix.org)"
    )
    remote_subparsers = remote_parser.add_subparsers(
        dest="remote_command", help="Remote subcommands"
    )

    remote_catalog_parser = remote_subparsers.add_parser(
        "catalog", help="Search library.kiwix.org catalog"
    )
    remote_catalog_parser.add_argument(
        "-l", "--lang", help="Language code (e.g., jpn, eng)"
    )
    remote_catalog_parser.add_argument("-c", "--category", help="Category filter")
    remote_catalog_parser.add_argument("-n", "--name", help="ZIM name (exact match)")
    remote_catalog_parser.add_argument("-q", "--query", help="Title/description search")
    remote_catalog_parser.add_argument(
        "--count", type=int, default=10, help="Number of results"
    )
    remote_catalog_parser.add_argument(
        "-f",
        "--format",
        choices=["table", "json", "simple"],
        default="table",
        help="Output format",
    )
    remote_catalog_parser.set_defaults(func=remote_catalog_action)

    remote_download_parser = remote_subparsers.add_parser(
        "download", help="Download ZIM file from library.kiwix.org"
    )
    remote_download_parser.add_argument("zim_name", help="ZIM file name")
    remote_download_parser.add_argument(
        "-o", "--output", type=Path, help="Output directory"
    )
    remote_download_parser.set_defaults(func=remote_download_action)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    if args.command == "remote" and not args.remote_command:
        remote_parser.print_help()
        sys.exit(0)

    args.func(args)


if __name__ == "__main__":
    main()
