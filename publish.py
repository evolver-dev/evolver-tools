#!/usr/bin/env python3
"""Publish to PyPI using token from .pypirc"""
import re, os, sys

with open("/root/.pypirc") as f:
    content = f.read()
m = re.search(r'password = (.+)', content)
token = m.group(1).strip() if m else ""

os.environ["TWINE_USERNAME"] = "__token__"
os.environ["TWINE_PASSWORD"] = token
os.environ["TWINE_NON_INTERACTIVE"] = "1"

sys.exit(os.system("cd /root/evolver-tools && twine upload --skip-existing dist/*.whl dist/*.tar.gz 2>&1"))
