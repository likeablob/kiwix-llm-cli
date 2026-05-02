"""Tests for meta4 parsing"""

from kiwix_llm_cli.meta4 import parse_metalink4


def test_parse_metalink4():
    content = """<?xml version="1.0" encoding="UTF-8"?>
<metalink xmlns="urn:ietf:params:xml:ns:metalink">
  <file name="test.zim">
    <size>1000000</size>
    <hash type="md5">abc123</hash>
    <hash type="sha-1">def456</hash>
    <hash type="sha-256">ghi789</hash>
    <url>https://example.com/test.zim</url>
  </file>
</metalink>"""
    result = parse_metalink4(content)
    assert result is not None
    assert result.filename == "test.zim"
    assert result.size == 1000000
    assert result.md5 == "abc123"
    assert result.sha1 == "def456"
    assert result.sha256 == "ghi789"
    assert len(result.urls) == 1


def test_parse_metalink4_multiple_urls():
    content = """<?xml version="1.0" encoding="UTF-8"?>
<metalink xmlns="urn:ietf:params:xml:ns:metalink">
  <file name="test.zim">
    <size>1000</size>
    <url priority="1">https://mirror1.example.com/test.zim</url>
    <url priority="2">https://mirror2.example.com/test.zim</url>
  </file>
</metalink>"""
    result = parse_metalink4(content)
    assert result is not None
    assert len(result.urls) == 2


def test_parse_metalink4_empty():
    content = """<?xml version="1.0" encoding="UTF-8"?>
<metalink xmlns="urn:ietf:params:xml:ns:metalink">
</metalink>"""
    result = parse_metalink4(content)
    assert result is None
