# Changelog

All notable changes to evolver-tools are documented here.

---

## [v38.0.4] — 2026-06-01

### Added
- **Round 34**: Clean-room E2E test — verified install + 10 workflows. Found 2 syntax-broken tools that weren't registered (`json_to_yaml`, `markdown_to_html`). Fixed and registered. Tool count: 254→259.
- **Round 35**: README + metadata synced to 259 tools, v38.0.3→v38.0.4
- **Round 36**: Final PyPI publish confirmed. All cron jobs active (daily monitor, daily pulse, weekly PyPI downloads)
- **Round 37**: GitHub Issue #5 as announcement page (Google-indexed). Demo SVG 404 fixed. Awesome-cli-apps fork pushed (PR blocked by token scope).

### Fixed
- 2 unregistered tools detected and fixed in clean-room validation
- Ledger JSON structural bug repaired
- Demo SVG stale URL on GitHub Pages

### Stats
- **259 tools** across 18 categories
- **42+ PyPI releases** (38.0.x patch cycle)
- **Zero dependencies** (pure stdlib)
- **¥1,310.56** current balance | ¥0 external revenue so far

---

## [v38.0.3] — 2026-06-01

### Added
- PyPI SEO: 10 classifiers + 9 keywords for better discoverability
- Distributor tool: `evtool share <platform>` — generates HN/Reddit/tweet posts
- GitHub Action: `evolver-dev/setup-evolver-tools` published to Marketplace
- `try.sh` — curl-to-bash 60s interactive demo (10 tools showcase)
- Sales tutorial HTML page + navigation integration
- Documentation site: interactive playground, showcase page, cheatsheet

### Fixed
- Demo SVG formatted via svg-term (broken asciinema → working preview)

### Stats
- 254 tools across 18 categories

---

## [v38.0.2] — 2026-06-01

### Added
- SEO: sitemap.xml (285 URLs) + robots.txt + Google/Bing ping
- `docs/story.html`: "Built by AI" narrative page
- `docs/cheatsheet.html`: printable 254-tool reference (10 categories)
- `docs/playground.html`: interactive terminal demo (8 scenarios)
- `docs/showcase.html`: Top 10 visually impressive tools gallery
- `docs/quickstart.html`: CSV-to-report tutorial
- `docs/vs.html`: CLI comparison page (evtool vs jq/yq/csvkit/etc.)
- GitHub Discussions enabled + clean-room install validation
- CI/CD pipeline + issue/PR templates + FUNDING.yml
- OG social preview image + JSON-LD schema
- README narrative rewrite with "Built by AI" hook

### Stats
- 254 tools across 18 categories

---

## [v38.0.1] — 2026-06-01

### Added
- `evtool demo` — runs 5 preset demos covering different categories
- `evtool try` — interactive onboarding (pick a category → try tools)
- First SEO-optimized tool pages for GitHub Pages
- CHANGELOG.md logging
- FUNDING.yml + GitHub Sponsor configuration

### Stats
- 254 tools across 18 categories

---

## [v38.0.0] — 2026-06-01

### Added
- **`evtool categories`** — list all 18 categories with tool counts
- **`evtool showcase`** — interactive tool showcase (5 random picks)
- **`evtool search <query>`** — fuzzy search 254 tools by name + description
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
- **254 tools** across 18 categories
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
