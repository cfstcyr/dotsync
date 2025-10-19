APP_NAME = "DotSync"

EXEC_SCRIPT = r"""
#!/usr/bin/env -S uv run --script
#
# /// script
{config_block}
# ///
import re
import sys
from dotsync.__main__ import main
if __name__ == "__main__":
    sys.argv[0] = re.sub(r"(-script\.pyw|\.exe)?$", "", sys.argv[0])

    if len(sys.argv) == 1:
        sys.argv.extend(["sync", "."])

    sys.exit(main())
""".strip()
