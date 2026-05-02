"""Tests for downloader"""

from kiwix_llm_cli.downloader import format_size


def test_format_size_bytes():
    assert format_size(500) == "500.0 B"


def test_format_size_kb():
    assert format_size(1024) == "1.0 KB"


def test_format_size_mb():
    assert format_size(1048576) == "1.0 MB"


def test_format_size_gb():
    assert format_size(1073741824) == "1.0 GB"


def test_format_size_tb():
    assert format_size(1099511627776) == "1.0 TB"
