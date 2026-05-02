"""Tests for OPDS parsing"""

from kiwix_llm_cli.opds import (
    parse_category,
    parse_entry,
    parse_tags,
    parse_zim_name_from_url,
    strip_date_suffix,
)


def test_strip_date_suffix_with_date():
    assert strip_date_suffix("freecodecamp_ja_all_2026-02") == "freecodecamp_ja_all"
    assert (
        strip_date_suffix("wikipedia_ja_top_mini_2026-04-15") == "wikipedia_ja_top_mini"
    )


def test_strip_date_suffix_without_date():
    assert strip_date_suffix("freecodecamp_ja_all") == "freecodecamp_ja_all"
    assert strip_date_suffix("wikipedia_en") == "wikipedia_en"


def test_parse_zim_name_from_url_meta4():
    url = "https://download.kiwix.org/zim/wikipedia/wikipedia_ja_all_maxi_2025-10.zim.meta4"
    assert parse_zim_name_from_url(url) == "wikipedia_ja_all_maxi_2025-10"


def test_parse_zim_name_from_url_content():
    url = "https://library.kiwix.org/content/wikipedia_ja_top_mini_2026-04"
    assert parse_zim_name_from_url(url) == "wikipedia_ja_top_mini_2026-04"


def test_parse_zim_name_from_url_empty():
    assert parse_zim_name_from_url("https://example.com/") == ""


def test_parse_tags():
    tags_data = [
        {"term": "wikipedia;_category:wikipedia;_ftindex:yes"},
        {"term": "_pictures:yes"},
    ]
    result = parse_tags(tags_data)
    assert "wikipedia" in result
    assert "_category:wikipedia" not in result


def test_parse_category():
    tags = ["wikipedia", "_category:wikipedia", "other"]
    assert parse_category(tags) == "wikipedia"

    tags = ["stack_exchange", "other"]
    assert parse_category(tags) == "stack_exchange"


def test_parse_entry():
    entry = {
        "title": "Test ZIM",
        "language": "jpn",
        "flavour": "mini",
        "articlecount": "1000",
        "mediacount": "50",
        "tags": [{"term": "test;_category:test"}],
        "links": [
            {
                "href": "https://download.kiwix.org/zim/test/test_zim_mini_2026-01.zim.meta4",
                "length": "1000000",
            }
        ],
        "id": "urn:uuid:abc123",
    }
    result = parse_entry(entry)
    assert result is not None
    assert result.name == "test_zim_mini_2026-01"
    assert result.title == "Test ZIM"
    assert result.language == "jpn"
    assert result.flavour == "mini"
    assert result.article_count == 1000
    assert result.size == 1000000


def test_parse_entry_no_meta4():
    entry = {
        "title": "Test ZIM",
        "links": [{"href": "https://example.com/content/test"}],
    }
    result = parse_entry(entry)
    assert result is None
