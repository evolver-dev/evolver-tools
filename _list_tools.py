#!/usr/bin/env python3
import sys
sys.path.insert(0, 'src')
from evolver_tools.autoreg import auto_discover
tools = auto_discover()
for name in sorted(tools.keys()):
    print(name)
print(f"\n--- Total: {len(tools)} ---")
