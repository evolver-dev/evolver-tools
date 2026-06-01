# Changelog

All notable changes to evolver-tools are documented here.

---

## [v38.1.0] — 2026-06-02

### Added
- **CI/CD infrastructure**: 3 GitHub Actions workflows
  - `ci.yml`: Python 3.8–3.12 smoke tests + ruff lint + build
  - `docker-publish.yml`: Build & publish Docker image to ghcr.io
  - `pypi-publish.yml`: Build & upload to PyPI on release / manual dispatch
- **Smoke tests**: `tests/test_basic.py` — 10 tests covering import, CLI invocation, tool execution, and zero-dependency verification
- **CI badge**: Updated README to point to real workflow

### Changed
- Moved `docker-publish.workflow.yml` to `.github/workflows/docker-publish.yml`

---

## [v38.0.19] — 2026-06-01

### Fixed
- Version display bug: `evtool --help` now shows v38.0.19 (was stuck at 38.0.19)

### Changed
- PyPI version synced to 38.0.19

### Stats
- **260 tools** across 30+ categories
- **0 external dependencies**
- PyPI release: https://pypi.org/project/evolver-tools/38.0.19/

## [v38.0.10] — 2026-06-01

### Fixed
- Version synced to 38.0.10 on PyPI (was 38.0.9)
- README version reference updated from 38.0.8 to 38.0.10

### Stats
- **260 tools** across 30+ categories
- **0 external dependencies**
- PyPI release #42: https://pypi.org/project/evolver-tools/38.0.10/

## [v38.0.5] — 2026-06-01

### Fixed
- DNS resolution: `socket.getaddrinfo` fallback for IPv4-only environments
- Website: tool count updated to 258 (accurate auto-discovery), version bumped to v38.0.5
- README, README_CN: version sync to 38.0.5, tool count consistency

### Stats
- **260 tools** across 30+ categories
- **0 external dependencies**

## [v38.0.0] — 2026-06-01

### Added
- **`evtool categories`** — list all 18 categories with tool counts
- **`evtool showcase`** — interactive tool showcase (5 random picks)
- **`evtool search <query>`** — fuzzy search 260 tools by name + description
- 277 SEO-optimized individual tool pages at `docs/tools/` for discoverability
- "Browse All" navigation link to the tools directory
- `CONTRIBUTING.md` for community contributions
- `demo.sh` — 30-second first-user experience script
- GitHub `.gitattributes` for correct language detection

### Fixed
- Tool count consistently reads 254 (auto_discovered), not hardcoded
- `--version` flag now reads from `__init__` before fallback
- CLI alias: underscores ↔ hyphens auto-converted in tool names

### Changed
- Marketing landing page with hero, install demo, category grid
- README overhaul with preview GIF and star CTA
- PyPI metadata: 20 classifiers, 17 keywords, sponsor/funding URLs

### Stats
- **260 tools** across 18 categories
- **40 PyPI releases**
- **Zero dependencies** (pure stdlib)
- GitHub Pages site: https://evolver-dev.github.io/evolver-tools/

---

## [v37.0.0] — 2026-05-xx

### Added
- 5 new tools: `git-ignore`, `mime-type`, `color-convert`, `csv-concat`, `ansi-to-html`
- Ledger system, status.json for financial tracking

### Stats
- 254 total tools

---

## [v35.0.0]

### Added
- 5 new tools: `merge-json`, `validate`, `diff-lines`, `csv-schema`, `chrono`

### Stats
- 249 total tools

---

## [v34.0.0]

### Added
- 5 new tools: `emoji-cli`, `html-strip`, `json-patch`, `markdown-format`, `ansi-to-txt`

### Stats
- 244 total tools

---

## [v33.0.0]

### Added
- 5 new tools: `diff-yaml`, `hexdec`, `csv-pretty`, `humanize`, `cron-check`

### Stats
- 239 total tools

---

## [v32.0.0]

### Added
- 5 new tools: `csv-sort`, `json-keys`, `file-type`, `link-check`, `csv-head`

### Stats
- 234 total tools

---

## [v31.0.0]

### Added
- 5 new tools: `find-empty`, `mac-address`, `csv-filter`, `file-patch`, `env-sorter`
- README rewrite with new structure

### Stats
- 238 total tools

---

## [v30.0.0]

### Added
- 5 new tools: `csv-to-table`, `json-to-table`, `dedup-files`, `text-wrap`, `slugify`
- README overhaul

### Stats
- 233 total tools

---

## [v29.0.0]

### Added
- 5 new tools: `csv-slice`, `json-sort`, `text-dedent`, `random-string`, `http-status`

### Stats
- 228 total tools

---

## [v28.0.0]

### Added
- 5 new tools: `json-to-yaml`, `xml-format`, `case-convert`, `time-duration`, `markdown-to-html`

### Stats
- 223 total tools

---

## [v27.0.0]

### Added
- 5 new tools: `scan-open-ports`, `banner` (→`ascii-banner`), `code-review`, `csv-dedup`, `json-path`
- QC tools v2.0: batch calculation, HTML/CSV, certificates

### Stats
- 218 total tools

---

## [v25.0.0]

### Added
- 5 new tools: `macrogen`, `code-review`, `pdf-text`, `csv-view`, `random-cli`

### Stats
- 208 total tools

---

## [v24.0.0]

### Added
- 5 new tools: `cal`, `calendar-cli`, `stopwatch`, `watch`, `sysmon-pro`

### Stats
- 203 total tools

---

## [v23.0.0]

### Added
- 5 new tools: `pipe-viewer`, `progress-bar`, `spinner`, `rainbow`, `qr-cli`

### Stats
- 198 total tools

---

## [v22.0.0]

### Added
- 5 new tools: `ascii-gen`, `figlet`, `cowsay`, `joke`, `quote`

### Stats
- 193 total tools

---

## v1.0–v21.0

Initial rapid-growth phase. Each version averaged +5 tools. The project grew from a handful of utilities to over 188 tools across 18 categories, covering CSV processing, JSON manipulation, networking, text processing, file operations, encryption, system monitoring, and more.

---

## Format

This changelog follows [Keep a Changelog](https://keepachangelog.com/) conventions.
