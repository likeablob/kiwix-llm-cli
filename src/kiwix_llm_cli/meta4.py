"""Metalink4 file parsing for ZIM download URLs"""

import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Optional


@dataclass
class MetalinkInfo:
    filename: str
    size: int
    md5: Optional[str]
    sha1: Optional[str]
    sha256: Optional[str]
    urls: list[str]


def parse_metalink4(content: str) -> Optional[MetalinkInfo]:
    root = ET.fromstring(content)

    file_elem = root.find(".//{urn:ietf:params:xml:ns:metalink}file")
    if file_elem is None:
        return None

    filename = file_elem.get("name", "")

    size_elem = file_elem.find("{urn:ietf:params:xml:ns:metalink}size")
    size = int(size_elem.text or "0") if size_elem is not None else 0

    hashes = {}
    for hash_elem in file_elem.findall("{urn:ietf:params:xml:ns:metalink}hash"):
        hash_type = hash_elem.get("type", "")
        hashes[hash_type] = hash_elem.text or ""

    urls = []
    for url_elem in file_elem.findall("{urn:ietf:params:xml:ns:metalink}url"):
        url = url_elem.text
        if url:
            urls.append(url)

    return MetalinkInfo(
        filename=filename,
        size=size,
        md5=hashes.get("md5"),
        sha1=hashes.get("sha-1"),
        sha256=hashes.get("sha-256"),
        urls=urls,
    )
