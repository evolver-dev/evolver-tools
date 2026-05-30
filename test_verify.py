#!/usr/bin/env python3
"""Verify auto-discovery."""
from evolver_tools.autoreg import auto_discover
tools = auto_discover()
print(f"Found {len(tools)} tools:")
for n in sorted(tools.keys()):
    print(f"  - {n}: {tools[n]['desc']}")
