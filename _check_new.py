#!/usr/bin/env python3
from evolver_tools.autoreg import auto_discover
tools = auto_discover()
new = ['emoji-cli', 'html-strip', 'json-patch', 'markdown-format', 'ansi-to-txt']
for n in new:
    if n in tools:
        print(f'OK  {n}: {tools[n]["desc"]}')
    else:
        print(f'FAIL {n}: NOT FOUND')
print(f'\nTotal tools: {len(tools)}')
# Also check git for current version
