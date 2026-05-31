#!/usr/bin/env python3
"""Check tool descriptions in TOOL_META for quality."""
import sys
sys.path.insert(0, 'src')
from evolver_tools.autoreg import auto_discover

tools = auto_discover()
print(f"Total tools: {len(tools)}")
print()

# Find all tools with short/poor descriptions
poor = {}
for name, info in sorted(tools.items()):
    desc = info['desc']
    if len(desc) < 20 or desc == name or desc.lower() == name.lower():
        poor[name] = desc

print(f"Tools with poor descriptions (< 20 chars or identical to name): {len(poor)}")
print()
for name, desc in sorted(poor.items()):
    print(f"  {name:25s} -> \"{desc}\"")

print()
# Count README claims vs reality
print("=== README says 238 CLI tools + 9 flagship ===")
print(f"=== Actual count: {len(tools)} tools ===")
