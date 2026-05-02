# kiwix-llm-cli

Kiwix ZIM file search CLI/Skill for coding agents.

Agentic search for Wikipedia, DevDocs, StackExchange, and other offline content from ZIM files.

## Installation

```bash
uv tool install kiwix-llm-cli

kwxlc -h
```

## Quick Start

1. Initialize configuration (shows download directory):

   ```bash
   kwxlc init                    # Global config
   kwxlc init -p .               # Local config for project (./.kiwix-llm-cli.yaml)
   ```

   Config locations (Linux example, OS-dependent, see `init` output):
   - Global: `~/.config/kiwix-llm-cli/config.yaml`
   - Download: `~/.local/share/kiwix-llm-cli/`

2. Get ZIM files:

   ```bash
   # Search and download from library.kiwix.org
   kwxlc remote catalog --lang eng --query wikipedia --count 5
   kwxlc remote download wikipedia_en_100_2026-04

   # Or download manually from https://library.kiwix.org/
   # Place in: ~/.local/share/kiwix-llm-cli/ (see your config.yaml)
   ```

3. List discovered ZIM files:

   ```bash
   kwxlc list
   ```

4. Search:
   ```bash
   kwxlc search "machine learning"
   ```

## Commands Reference

```bash
kwxlc init [-p PATH]              # Generate config file
kwxlc list [-f FORMAT]            # List discovered ZIM files
kwxlc search QUERY [-l LIMIT]     # Full-text search
kwxlc suggest TERM [-l LIMIT]     # Title suggestion
kwxlc get TITLE [-f FORMAT]       # Get article (markdown/html/raw)
kwxlc info                        # Show ZIM file info
kwxlc install-skills [-a AGENT]   # Install skill for coding agents

kwxlc remote catalog [OPTIONS]    # Search library.kiwix.org
kwxlc remote download NAME [-o DIR] # Download ZIM file

Options:
  -c, --config PATH       Config file path
  -b, --backend {libzim,api}  Backend selection
  -u, --kiwix-api-url URL     API endpoint URL
  -z, --zim NAME              ZIM file name/path
```

## Skill Installation

Installs SKILL.md for coding agents (default: `.claude/skills`):

```bash
 # ./.claude/skills (default)
kwxlc install-skills

# ./.agents/skills
kwxlc install-skills -a opencode

# Both
kwxlc install-skills -a opencode -a claude-code
```

## Configuration

### Config File Locations (Linux example)

| Type   | Location                                |
| ------ | --------------------------------------- |
| Global | `~/.config/kiwix-llm-cli/config.yaml`   |
| Local  | `./.kiwix-llm-cli.yaml` (auto-detected) |

### Config Structure

```yaml
default_zim: wikipedia_en_wp1-0.8_nopic_2026-04
backend: libzim # Default backend (libzim or api)
kiwix_api_url: http://localhost:8080 # API endpoint URL
search_dirs: # Directories to search for ZIM files
  - ~/.local/share/kiwix-llm-cli # Default (OS-dependent)
  - ~/Documents/zim
download_dir: ~/.local/share/kiwix-llm-cli
```

### Priority (low to high)

1. Global config
2. Local config (`./.kiwix-llm-cli.yaml`)
3. Environment variables (`KWXLC_*`)
4. Command-line options (`-c`, `--zim`, `--backend`)

### Environment Variables

```bash
KWXLC_DEFAULT_ZIM=wikipedia_en_wp1-0.8_nopic_2026-04
KWXLC_BACKEND=api
KWXLC_KIWIX_API_URL=http://localhost:8080
```

## API Backend

Use [kiwix-serve](https://github.com/kiwix/kiwix-tools) to serve ZIM files via HTTP UI/API.

When `backend: api` in config, commands default to API backend.

```bash
# Start kiwix-serve (example)
kiwix-serve --port 8080 ~/.local/share/kiwix-llm-cli/*.zim

# Config with backend: api
kwxlc search "query"  # Uses kiwix-serve automatically

# Or override explicitly
kwxlc search "query" --backend api --kiwix-api-url http://custom:9999
```

## Development

```bash
# Setup
mise trust
uv sync --dev

# Lint & Format
uv run ruff check .
uv run ruff format .

# Type check
uv run ty check src/

# Test
uv run pytest

# Pre-commit
uv run pre-commit run --all-files

# Pin GitHub Actions versions
pinact run
```

## Tips

- OR/NOT operators are not supported (Xapian limitation)

## Related Projects

- [Kiwix](https://kiwix.org/): Offline content reader

## License

MIT
