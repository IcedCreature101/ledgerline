"""Put `src/` on the import path.

The project uses a src layout, so `import ledgerline` only works from an installed distribution or with
this. Keeping it here means a fresh clone can run `pytest` with nothing installed but pytest itself.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))
