#!/usr/bin/env python3
import sys
import zipfile
from pathlib import Path

def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <path>")
        sys.exit(1)

    root = Path(sys.argv[1])
    if not root.is_dir():
        print(f"Error: '{root}' is not a directory")
        sys.exit(1)

    for f in root.rglob("*"):
        if f.is_file():
            f.write_bytes(b"")
            print(f"Cleared: {f}")

    zip_path = root.parent / f"{root.name}.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in sorted(root.rglob("*")):
            zf.write(f, f.relative_to(root.parent))
    print(f"Zipped: {zip_path}")

if __name__ == "__main__":
    main()
