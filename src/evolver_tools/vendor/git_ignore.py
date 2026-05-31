#!/usr/bin/env python3
"""git-ignore — .gitignore template generator."""
TOOL_META = {"name": "git-ignore", "func": "main", "desc": "Generate .gitignore templates for common languages/frameworks"}

TEMPLATES = {
    "python": """# Python
__pycache__/
*.py[cod]
*.egg-info/
dist/
build/
.venv/
venv/
env/
*.egg
.Python
*.so
*.whl
*.egg-info/
.eggs/
.Pipenv.lock
.pytest_cache/
.mypy_cache/
.ruff_cache/
.tox/
.coverage
htmlcov/
*.db
*.sqlite
.DS_Store
*.swp
*.swo
*~
""",
    "node": """# Node
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*
.pnpm-store/
.next/
dist/
build/
.cache/
.env
.env.local
.env.*.local
*.tsbuildinfo
*.swp
*.swo
*~
.DS_Store
coverage/
.nyc_output/
""",
    "go": """# Go
*.exe
*.exe~
*.dll
*.so
*.dylib
*.test
*.out
vendor/
.idea/
*.swp
*.swo
*~
.DS_Store
dist/
build/
coverage.txt
coverage.out
""",
    "rust": """# Rust
target/
**/*.rs.bk
Cargo.lock
*.swp
*.swo
*~
.DS_Store
""",
    "java": """# Java
*.class
*.jar
*.war
*.nar
*.ear
*.zip
*.tar.gz
*.rar
hs_err_pid*
replay_pid*
target/
!**/src/main/**/target/
!**/src/test/**/target/
.idea/
*.iml
*.ipr
*.iws
.settings/
.project
.classpath
bin/
build/
.gradle/
*.swp
*.swo
*~
.DS_Store
""",
    "docker": """# Docker
.docker/
docker-compose.override.yml
*.swp
*.swo
*~
.DS_Store
""",
    "vim": """# Vim
*.swp
*.swo
*~
[._]*.s[a-w][a-z]
[._]s[a-w][a-z]
*.un~
Session.vim
.netrwhist
""",
    "macos": """# macOS
.DS_Store
.AppleDouble
.LSOverride
Icon
._*
.DocumentRevisions-V100
.fseventsd
.Spotlight-V100
.TemporaryItems
.Trashes
.VolumeIcon.icns
.com.apple.timemachine.donotpresent
""",
    "windows": """# Windows
Thumbs.db
Thumbs.db:encryptable
ehthumbs.db
ehthumbs_vista.db
*.stackdump
[Dd]esktop.ini
$RECYCLE.BIN/
*.lnk
""",
    "latex": """# LaTeX
*.aux
*.bbl
*.blg
*.brf
*.fls
*.idx
*.ilg
*.ind
*.lof
*.log
*.lot
*.nav
*.out
*.run.xml
*.snm
*.synctex.gz
*.toc
*.vrb
*.xdv
_site/
""",
}

def main():
    import sys
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help", "help"):
        print("Usage: git-ignore <template> [template...]")
        print(f"Templates: {', '.join(sorted(TEMPLATES.keys()))}")
        print("  git-ignore python    → print Python .gitignore")
        print("  git-ignore python node macos → combined")
        return

    combined = ""
    seen = set()
    for tpl in args:
        tpl = tpl.lower().replace("-", "").replace("_", "")
        found = None
        for key in TEMPLATES:
            if key.replace("-", "").replace("_", "") == tpl:
                found = key
                break
        if found and found not in seen:
            combined += f"### {found.title()} ###\n{TEMPLATES[found]}\n"
            seen.add(found)
        elif not found:
            print(f"Warning: no template '{tpl}'", file=sys.stderr)
    sys.stdout.write(combined)


if __name__ == "__main__":
    main()
