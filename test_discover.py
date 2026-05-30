#!/usr/bin/env python3
"""Debug auto-discovery."""
import pkgutil
import importlib
import os
import sys

# Find the vendor dir
vendor_dir = os.path.join(os.path.dirname(__file__), "src/evolver_tools/vendor")
if not os.path.exists(vendor_dir):
    vendor_dir = os.path.join(os.getcwd(), "src/evolver_tools/vendor")
print(f"Vendor dir: {vendor_dir}")
print(f"Exists: {os.path.exists(vendor_dir)}")
print(f"Files there: {[f for f in os.listdir(vendor_dir) if not f.startswith('.')][:10]}...")

# Test what pkgutil finds
for importer, modname, ispkg in pkgutil.iter_modules([vendor_dir]):
    print(f"  {modname} (ispkg={ispkg})")
