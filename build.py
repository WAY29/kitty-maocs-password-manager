#!/usr/bin/env python3
"""
Build script to bundle the SSH manager into a single file using stickytape.
"""

import sys
from pathlib import Path

import stickytape


def main():
    project_root = Path(__file__).parent
    src_dir = project_root / "src"
    output_file = project_root / "ssh_manager.py"
    entry_point = src_dir / "main.py"

    if not entry_point.exists():
        print(f"Error: Entry point not found: {entry_point}", file=sys.stderr)
        sys.exit(1)

    # Use stickytape API to bundle the code
    output = stickytape.script(
        str(entry_point),
        add_python_paths=[str(project_root)],
        copy_shebang=True,
    )

    # Write the bundled output
    output_file.write_text(output)
    print(f"Successfully bundled to: {output_file}")


if __name__ == "__main__":
    main()
