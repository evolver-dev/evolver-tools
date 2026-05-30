#!/usr/bin/env python3
"""Inject TOOL_META into new vendor files from remote, cleanup orphans."""

import re
import os

VENDOR_DIR = "/root/evolver-tools/src/evolver_tools/vendor"

# Part 1: Inject TOOL_META for 9 new tools
new_tools = {
    "firewall_rule.py": {"name": "firewall-rule", "func": "main", "desc": "iptables/nftables firewall rule helper"},
    "ssh_key_gen.py": {"name": "ssh-key-gen", "func": "main", "desc": "Generate SSH key pairs"},
    "figlet_tool.py": {"name": "figlet", "func": "main", "desc": "ASCII banner generator (figlet-style)"},
    "db_schema.py": {"name": "db-schema", "func": "main", "desc": "Display database schema as ASCII"},
    "audit_log.py": {"name": "audit-log", "func": "main", "desc": "Parse and filter system audit logs"},
    "config_validator.py": {"name": "config-validator", "func": "main", "desc": "Validate config files (JSON, YAML, TOML)"},
    "api_tester.py": {"name": "api-tester", "func": "main", "desc": "HTTP API testing tool"},
    "agent_b_tool.py": {"name": "agent-b-tool", "func": "main", "desc": "Agent B tool"},
    "log_analyzer.py": {"name": "log-analyzer", "func": "main", "desc": "Log file analyzer"},
}

injected = 0
for fname, meta in new_tools.items():
    path = os.path.join(VENDOR_DIR, fname)
    with open(path) as f:
        content = f.read()
    
    # Remove any previous TOOL_META if double-inserted
    content = re.sub(r'\n# === Auto-registration metadata ===\nTOOL_META = \{.*?\n\}', '', content, flags=re.DOTALL)
    
    meta_block = f"""
# === Auto-registration metadata ===
TOOL_META = {{
    "name": "{meta['name']}",
    "func": "{meta['func']}",
    "desc": {repr(meta['desc'])},
}}
"""
    # Insert before __main__ block, or at end
    main_patterns = [
        r'if\s+__name__\s*==\s*["\']__main__["\']\s*:',
    ]
    inserted = False
    for p in main_patterns:
        m = re.search(p, content)
        if m:
            insert_pos = m.start()
            content = content[:insert_pos] + meta_block + "\n" + content[insert_pos:]
            inserted = True
            break
    
    if not inserted:
        content += meta_block
    
    with open(path, 'w') as f:
        f.write(content)
    injected += 1
    print(f"  Injected: {fname} -> {meta['name']}")

print(f"\n{injected} new tools got TOOL_META")

# Part 2: Remove TOOL_META from orphan .py files (those with directory counterparts)
orphans = ['split.py', 'timer_pro.py', 'changelog_gen.py', 'banner.py']
for fname in orphans:
    path = os.path.join(VENDOR_DIR, fname)
    with open(path) as f:
        content = f.read()
    content = re.sub(r'\n# === Auto-registration metadata ===\nTOOL_META = \{.*?\n\}', '', content, flags=re.DOTALL)
    content = re.sub(r'\nTOOL_META = \{.*?\n\}', '', content, flags=re.DOTALL)
    with open(path, 'w') as f:
        f.write(content)
    print(f"  Cleaned: {fname} (removed TOOL_META)")

print("\nDone!")
