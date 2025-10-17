#!/usr/bin/env python3
# Restored snapshot of passbot_final_fixed.py (confirmed version)
# This file mirrors the finalized implementation with full UI/animations,
# no '-' or '.' separators (optional '_'), Full/Strong modes, incremental
# saving, and safe Ctrl+C resume. For latest, see passbot.py.

from passbot import *

# Delegate to the same entrypoint to avoid code duplication
if __name__ == "__main__":
    sys.exit(main())
