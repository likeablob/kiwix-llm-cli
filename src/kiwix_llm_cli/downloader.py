"""ZIM file downloader with progress and hash verification"""

import hashlib
from pathlib import Path

import httpx
from tqdm import tqdm

from .meta4 import MetalinkInfo


def format_size(size: int) -> str:
    float_size: float = float(size)
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if float_size < 1024:
            return f"{float_size:.1f} {unit}"
        float_size /= 1024
    return f"{float_size:.1f} PB"


def compute_hash(filepath: Path, algorithm: str) -> str:
    hasher = hashlib.new(algorithm)
    with open(filepath, "rb") as f:
        while chunk := f.read(8192):
            hasher.update(chunk)
    return hasher.hexdigest()


def download_zim(
    metalink: MetalinkInfo,
    output_dir: Path,
    verbose: bool = True,
) -> Path:
    output_path = output_dir / metalink.filename

    if output_path.exists():
        existing_size = output_path.stat().st_size
        if existing_size == metalink.size:
            if metalink.sha256:
                computed = compute_hash(output_path, "sha256")
                if computed == metalink.sha256:
                    if verbose:
                        print(f"Already downloaded: {output_path}")
                    return output_path
            elif verbose:
                print(f"File exists with correct size: {output_path}")
                return output_path

    if not metalink.urls:
        raise ValueError("No download URLs available")

    url = metalink.urls[0]

    output_dir.mkdir(parents=True, exist_ok=True)

    if verbose:
        print(f"Downloading: {metalink.filename} ({format_size(metalink.size)})")
        print(f"URL: {url}")

    progress = None
    if verbose:
        progress = tqdm(
            total=metalink.size,
            unit="B",
            unit_scale=True,
            unit_divisor=1024,
            desc=metalink.filename[:30],
        )

    hasher = hashlib.sha256() if metalink.sha256 else None

    with httpx.stream("GET", url, follow_redirects=True) as response:
        response.raise_for_status()
        with open(output_path, "wb") as f:
            for chunk in response.iter_bytes(chunk_size=8192):
                f.write(chunk)
                if progress:
                    progress.update(len(chunk))
                if hasher:
                    hasher.update(chunk)

    if progress:
        progress.close()

    if hasher and metalink.sha256:
        computed = hasher.hexdigest()
        if computed != metalink.sha256:
            output_path.unlink()
            raise ValueError(
                f"Hash verification failed:\n"
                f"  Expected: {metalink.sha256}\n"
                f"  Computed: {computed}"
            )
        if verbose:
            print("Hash verified: SHA-256 OK")

    return output_path
