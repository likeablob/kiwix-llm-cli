"""ZIM file auto-discovery"""

import os
from pathlib import Path
from typing import Dict, List, Optional, TypedDict

from libzim.reader import Archive

from .libzim_search import suppress_libzim_output


class ZimInfo(TypedDict, total=False):
    name: str
    path: str
    title: str
    language: str
    article_count: int
    has_fulltext_index: bool
    has_title_index: bool
    filesize: int
    error: str


def discover_zim_files(
    search_dirs: Optional[List[Path]] = None,
    include_cwd: bool = False,
) -> Dict[str, ZimInfo]:
    discovered: Dict[str, ZimInfo] = {}

    dirs_to_search: List[Path] = []

    if search_dirs:
        dirs_to_search.extend(search_dirs)
        env_home = os.environ.get("KIWIX_HOME")
        if env_home:
            dirs_to_search.append(Path(env_home.replace("~", str(Path.home()))))

    if include_cwd:
        dirs_to_search.append(Path.cwd())

    for search_dir in dirs_to_search:
        if not search_dir.exists():
            continue
        for zim_file in search_dir.glob("*.zim"):
            info = get_zim_info(zim_file)
            name = info.get("name")
            if name and name not in discovered:
                info["path"] = str(zim_file)
                discovered[name] = info

    return discovered


def extract_zim_name(zim_path: Path) -> Optional[str]:
    try:
        with suppress_libzim_output():
            archive = Archive(zim_path)
            try:
                entry = archive.get_entry_by_path("M/Name")
                name = bytes(entry.get_item().content).decode("utf-8").strip()
            except Exception:
                name = None

        if name:
            return name

        stem = zim_path.stem
        stem = stem.lower()
        stem = stem.replace(" ", "_")
        stem = stem.replace("+", "plus")
        import unicodedata

        stem = (
            unicodedata.normalize("NFKD", stem)
            .encode("ascii", "ignore")
            .decode("ascii")
        )
        return stem

    except Exception:
        return zim_path.stem.lower()


def get_zim_info(zim_path: Path) -> ZimInfo:
    try:
        with suppress_libzim_output():
            archive = Archive(zim_path)
            info: ZimInfo = {
                "name": extract_zim_name(zim_path) or zim_path.stem,
                "title": "",
                "language": "",
                "article_count": archive.article_count,
                "has_fulltext_index": archive.has_fulltext_index,
                "has_title_index": archive.has_title_index,
                "filesize": zim_path.stat().st_size,
            }

            for key in ["Title", "Language"]:
                try:
                    entry = archive.get_entry_by_path(f"M/{key}")
                    value = bytes(entry.get_item().content).decode("utf-8").strip()
                    if key == "Title":
                        info["title"] = value
                    elif key == "Language":
                        info["language"] = value
                except Exception:
                    pass

        return info
    except Exception as e:
        return {"name": zim_path.stem, "error": str(e)}
