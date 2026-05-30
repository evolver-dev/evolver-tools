"""config-vault main entry point.

Allows running as: python -m config_vault
or via the installed console_scripts entry: config-vault
"""

import sys

from config_vault.cli import main

if __name__ == "__main__":
    sys.exit(main())
