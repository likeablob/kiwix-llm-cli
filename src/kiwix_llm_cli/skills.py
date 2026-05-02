"""Skill installation for coding agents"""

from pathlib import Path
from typing import List, Optional

SKILL_TEMPLATE = """---
name: kiwix-llm-cli
description: Search offline Wikipedia, DevDocs, and ZIM content. Use when user mentions kiwix, zim, offline wikipedia, or local encyclopedia search/download.
---

# kiwix-llm-cli Skill

Search and retrieve content from offline Kiwix ZIM files (Wikipedia, DevDocs, StackExchange, etc.).

## Workflow

When user asks to search/lookup information from offline sources:

- **Check available ZIMs**: `kwxlc list`
- **Search**: `kwxlc search "<query>"` (uses default_zim from config)
- **Get article**: `kwxlc get "<title>"` (returns Markdown by default)
- **Summarize**: Provide relevant information from retrieved content

For downloading new ZIM files:

- **Catalog search**: `kwxlc remote catalog --lang eng --query <term> -f json`
  (use 3-letter codes: eng, jpn, fra, etc.)
- **Download**: `kwxlc remote download <zim-name>`

## Subcommands

| Command | Purpose |
|---------|---------|
| `list` | Show available ZIM files |
| `search <query>` | Full-text search |
| `suggest <term>` | Title autocomplete |
| `get <title>` | Retrieve article (Markdown/HTML) |
| `info` | ZIM file metadata |
| `remote catalog` | Search library.kiwix.org (use `-f json`) |
| `remote download` | Download ZIM file |

## Details

- `kwxlc <command> --help` for all options
- Config: `~/.config/kiwix-llm-cli/config.yaml`
- First run: `kwxlc init` to discover ZIMs
- Search operators: AND (spaces), phrase ("quoted"); OR/NOT unsupported
"""

AGENT_PATHS = {
    "opencode": ".agents/skills/kiwix-llm-cli",
    "claude-code": ".claude/skills/kiwix-llm-cli",
}


def get_skill_install_targets(
    agents: List[str] = ["claude-code"],
    target: Optional[Path] = None,
) -> List[Path]:
    if target:
        return [target]

    targets: List[Path] = []
    cwd = Path.cwd()

    for agent in agents:
        if agent in AGENT_PATHS:
            targets.append(cwd / AGENT_PATHS[agent])

    return targets


def install_skill(target: Path) -> bool:
    try:
        target.mkdir(parents=True, exist_ok=True)
        skill_file = target / "SKILL.md"
        skill_file.write_text(SKILL_TEMPLATE, encoding="utf-8")
        return True
    except Exception:
        return False


def install_skills(
    agents: List[str] = ["claude-code"],
    target: Optional[Path] = None,
) -> List[Path]:
    targets = get_skill_install_targets(agents, target)
    installed: List[Path] = []

    for t in targets:
        if install_skill(t):
            installed.append(t)

    return installed
