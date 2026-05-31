#!/usr/bin/env python3
"""license-cli — 开源许可证文本生成器

Usage:
    license-cli mit -a "John Doe"
    license-cli gpl-3.0 -a "John Doe" -o LICENSE
    license-cli list
    license-cli apache-2.0 --year 2024
"""

import argparse
import sys
import os
from datetime import datetime
from pathlib import Path

# ── Embedded short licenses ──

LICENSES_DATA = {}

LICENSES_DATA["mit"] = """MIT License

Copyright (c) {year} {author}

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

LICENSES_DATA["bsd-2-clause"] = """BSD 2-Clause License

Copyright (c) {year}, {author}

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.
2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

LICENSES_DATA["bsd-3-clause"] = """BSD 3-Clause License

Copyright (c) {year}, {author}

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.
2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.
3. Neither the name of the copyright holder nor the names of its
   contributors may be used to endorse or promote products derived from
   this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

LICENSES_DATA["isc"] = """ISC License

Copyright (c) {year}, {author}

Permission to use, copy, modify, and/or distribute this software for any
purpose with or without fee is hereby granted, provided that the above
copyright notice and this permission notice appear in all copies.

THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
"""

LICENSES_DATA["unlicense"] = """This is free and unencumbered software released into the public domain.

Anyone is free to copy, modify, publish, use, compile, sell, or
distribute this software, either in source code form or as a compiled
binary, for any purpose, commercial or non-commercial, and by any
means.

In jurisdictions that recognize copyright laws, the author or authors
of this software dedicate any and all copyright interest in the
software to the public domain. We make this dedication for the benefit
of the public at large and to the detriment of our heirs and
successors. We intend this dedication to be an overt act of
relinquishment in perpetuity of all present and future rights to this
software under copyright law.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL THE AUTHORS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
OTHER DEALINGS IN THE SOFTWARE.

For more information, please refer to <https://unlicense.org/>
"""

LICENSES_DATA["mpl-2.0"] = """Mozilla Public License Version 2.0
==================================

1. Definitions
--------------

1.1. "Contributor"
    means each individual or legal entity that creates, contributes to
    the creation of, or owns Covered Software.

1.2. "Contributor Version"
    means the combination of the Contributions of others (if any) used
    by a Contributor and that particular Contributor's Contribution.

1.3. "Contribution"
    means Covered Software of a particular Contributor.

1.4. "Covered Software"
    means Source Code Form to which the initial Contributor has attached
    the notice in Exhibit A, the Executable Form of such Source Code
    Form, and Modifications of such Source Code Form, in each case
    including portions thereof.

[Full text available at https://www.mozilla.org/MPL/2.0/]

Exhibit A - Source Code Form License Notice
-------------------------------------------

  This Source Code Form is subject to the terms of the Mozilla Public
  License, v. 2.0. If a copy of the MPL was not distributed with this
  file, You can obtain one at http://mozilla.org/MPL/2.0/.

Exhibit B - "Incompatible With Secondary Licenses" Notice
-----------------------------------------------------------

  This Source Code Form is "Incompatible With Secondary Licenses", as
  defined by the Mozilla Public License, v. 2.0.
"""


LICENSES_META = {
    "mit":           {"name": "MIT License",                     "spdx": "MIT"},
    "apache-2.0":    {"name": "Apache License 2.0",              "spdx": "Apache-2.0"},
    "gpl-3.0":       {"name": "GNU General Public License v3.0", "spdx": "GPL-3.0-only"},
    "bsd-2-clause":  {"name": "BSD 2-Clause \"Simplified\"",     "spdx": "BSD-2-Clause"},
    "bsd-3-clause":  {"name": "BSD 3-Clause \"New\"",            "spdx": "BSD-3-Clause"},
    "mpl-2.0":       {"name": "Mozilla Public License 2.0",      "spdx": "MPL-2.0"},
    "unlicense":     {"name": "The Unlicense",                   "spdx": "Unlicense"},
    "isc":           {"name": "ISC License",                     "spdx": "ISC"},
}

ALIASES = {
    "apache": "apache-2.0", "gpl": "gpl-3.0",
    "gplv3": "gpl-3.0",  "gpl3": "gpl-3.0",
    "bsd2": "bsd-2-clause", "bsd3": "bsd-3-clause",
    "bsd": "bsd-3-clause", "mpl": "mpl-2.0",
}


def _load_license_text(key):
    """Try data/ files first (full texts), then embedded."""
    data_dir = Path(__file__).parent / "data"
    txt_file = data_dir / f"{key}.txt"
    if txt_file.exists():
        return txt_file.read_text(encoding="utf-8")
    if key in LICENSES_DATA:
        return LICENSES_DATA[key]
    return None


def get_supported():
    items = sorted(LICENSES_META.items(), key=lambda x: x[1]["name"])
    lines = []
    for key, info in items:
        aliases = [a for a, v in ALIASES.items() if v == key]
        has_text = "✓" if _load_license_text(key) else "✗"
        alias_str = f"  (also: {', '.join(aliases)})" if aliases else ""
        lines.append(f"  {key:20s}  {info['name']:40s} {has_text}{alias_str}")
    return "\n".join(lines)


def generate(license_id, author, year):
    key = ALIASES.get(license_id, license_id)
    if key not in LICENSES_META:
        sys.stderr.write(f"error: unknown license '{license_id}'\n")
        sys.stderr.write(f"Run 'license-cli list' to see available licenses.\n")
        sys.exit(1)

    text = _load_license_text(key)
    if text is None:
        sys.stderr.write(f"error: full text for '{key}' is not embedded.\n")
        sys.stderr.write(f"Try: license-cli {key} --download\n")
        sys.exit(1)

    return text.format(year=year, author=author)


def main():
    parser = argparse.ArgumentParser(
        prog="license-cli",
        description="开源许可证文本生成器 — 一键生成 MIT/GPL/Apache/BSD/MPL/Unlicense/ISC",
        epilog="Example: license-cli mit -a 'John Doe' -o LICENSE",
    )
    parser.add_argument("license", nargs="?", default=None,
                        help="许可证类型 (e.g. mit, apache, gpl, bsd, mpl, unlicense, isc)")
    parser.add_argument("-a", "--author", default=None,
                        help="版权人/作者名 (默认: git config user.name)")
    parser.add_argument("-y", "--year", default=None,
                        help="年份 (默认: 当前年份)")
    parser.add_argument("-o", "--output", default=None,
                        help="输出到文件 (默认输出到 stdout)")

    args = parser.parse_args()

    if not args.license or args.license == "list":
        print("Available licenses:")
        print(get_supported())
        print()
        print("Usage: license-cli <license> [-a AUTHOR] [-y YEAR] [-o FILE]")
        return

    year_val = args.year or str(datetime.now().year)

    author_val = args.author
    if not author_val:
        try:
            import subprocess
            result = subprocess.run(
                ["git", "config", "user.name"],
                capture_output=True, text=True, timeout=2
            )
            if result.returncode == 0 and result.stdout.strip():
                author_val = result.stdout.strip()
        except Exception:
            pass
    if not author_val:
        author_val = "Author"

    text = generate(args.license, author_val, year_val)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"✅ License written to {args.output}")
    else:
        print(text)



# === Auto-registration metadata ===
TOOL_META = {
    "name": "license-cli",
    "func": "main",
    "desc": 'Open-source license generator and validator',
}

if __name__ == "__main__":
    main()
