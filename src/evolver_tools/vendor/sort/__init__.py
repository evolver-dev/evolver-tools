# sort package — re-export from single file
from .sort import *

# === Auto-registration metadata ===
TOOL_META = {
    "name": "sort",
    "func": "main",
    "desc": 'Line sorting (alpha, numeric, unique, by column)',
}
