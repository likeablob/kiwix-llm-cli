"""Tests for kiwix-llm-cli discovery"""

from pathlib import Path
from unittest.mock import patch

from kiwix_llm_cli.discovery import discover_zim_files


def test_discover_zim_files_empty(tmp_path: Path):
    discovered = discover_zim_files(search_dirs=[tmp_path])
    assert discovered == {}


def test_discover_zim_files_with_zim(tmp_path: Path):
    zim_file = tmp_path / "test.zim"
    zim_file.touch()

    with patch("kiwix_llm_cli.discovery.get_zim_info") as mock_info:
        mock_info.return_value = {"name": "test_zim"}
        discovered = discover_zim_files(search_dirs=[tmp_path])
        assert "test_zim" in discovered


def test_discover_zim_files_include_cwd(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    zim_file = tmp_path / "cwd_test.zim"
    zim_file.touch()

    with patch("kiwix_llm_cli.discovery.get_zim_info") as mock_info:
        mock_info.return_value = {"name": "cwd_test"}
        discovered = discover_zim_files(include_cwd=True)
        assert "cwd_test" in discovered


def test_extract_zim_name_from_stem():
    path = Path("/some/path/My_Test_File.zim")
    stem = path.stem.lower().replace(" ", "_").replace("+", "plus")
    assert stem == "my_test_file"
