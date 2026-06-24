#!/usr/bin/env python3
"""
Money Radar — License System Installer

Patches feeds.fun's application.py to add license middleware and routes.

Usage:
    python3 install_license.py [--feedsfun-dir ./feeds.fun]
"""

import argparse
import os
import sys
import shutil
from typing import Optional


PATCH_MARKER = "# Money Radar License Integration"
PATCH_CODE = '''
# Money Radar License Integration
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from license import setup_license
'''

INIT_CALL = "    setup_license(app)"


def find_app_file(feedsfun_dir: str) -> Optional[str]:
    """Find feeds.fun's application.py."""
    candidates = [
        os.path.join(feedsfun_dir, "ffun", "ffun", "application", "application.py"),
        os.path.join(feedsfun_dir, "ffun", "ffun", "application.py"),
        os.path.join(feedsfun_dir, "ffun", "application.py"),
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    return None


def patch_application(app_file: str) -> bool:
    """Add license integration to application.py."""
    with open(app_file, "r") as f:
        content = f.read()

    # Check if already patched
    if PATCH_MARKER in content:
        print(f"  Already patched: {app_file}")
        return True

    # Find the FastAPI app creation
    lines = content.split("\n")
    app_line_idx = None
    setup_line_idx = None

    for i, line in enumerate(lines):
        # Find "app = FastAPI(...)" or similar
        if "app" in line and "FastAPI" in line and "=" in line and "(" in line:
            app_line_idx = i
        # Find where we can insert the setup call (after app creation)
        if app_line_idx is not None and setup_line_idx is None:
            if line.strip() == "" or line.strip().startswith("#") or not line.startswith(" "):
                # Found a non-indented line after app creation
                if i > app_line_idx + 1:
                    setup_line_idx = i
                    break

    if app_line_idx is None:
        print(f"  WARNING: Could not find FastAPI app creation in {app_file}")
        print(f"  Please manually add the license integration.")
        return False

    # Insert import after the app creation block
    insert_idx = app_line_idx + 1
    while insert_idx < len(lines) and (lines[insert_idx].strip().startswith(")") or lines[insert_idx].strip() == ""):
        insert_idx += 1

    # Add import
    lines.insert(insert_idx, PATCH_CODE)

    # Find where to add setup_license(app) call
    # Look for the first method call on app after creation
    for i in range(insert_idx + len(PATCH_CODE.split("\n")), len(lines)):
        line = lines[i]
        if "app." in line and ("include_router" in line or "add_middleware" in line or "mount" in line):
            lines.insert(i, INIT_CALL)
            break
    else:
        # If no app.xxx calls found, add after imports
        for i in range(insert_idx + len(PATCH_CODE.split("\n")), len(lines)):
            if lines[i].strip() == "" or not lines[i].startswith(" ") and not lines[i].startswith("import") and not lines[i].startswith("from"):
                lines.insert(i, INIT_CALL)
                break

    # Write back
    with open(app_file, "w") as f:
        f.write("\n".join(lines))

    print(f"  Patched: {app_file}")
    return True


def copy_license_module(feedsfun_dir: str, source_dir: str) -> bool:
    """Copy license module into feeds.fun."""
    src = os.path.join(source_dir, "license")
    dst = os.path.join(feedsfun_dir, "license")

    if os.path.exists(dst):
        print(f"  License module already exists at {dst}")
        return True

    shutil.copytree(src, dst)
    print(f"  Copied license module to {dst}")
    return True


def main():
    parser = argparse.ArgumentParser(description="Install Money Radar license system")
    parser.add_argument(
        "--feedsfun-dir",
        default="./feeds.fun",
        help="Path to feeds.fun directory (default: ./feeds.fun)",
    )
    parser.add_argument(
        "--source-dir",
        default=".",
        help="Path to money-radar source directory (default: .)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes",
    )

    args = parser.parse_args()

    print("=== Money Radar License Installer ===")
    print()

    # Check feeds.fun exists
    if not os.path.isdir(args.feedsfun_dir):
        print(f"ERROR: feeds.fun directory not found: {args.feedsfun_dir}")
        print("Run setup.sh first to clone feeds.fun.")
        sys.exit(1)

    # Find application.py
    app_file = find_app_file(args.feedsfun_dir)
    if not app_file:
        print("ERROR: Could not find application.py in feeds.fun")
        sys.exit(1)

    print(f"Target: {app_file}")
    print()

    if args.dry_run:
        print("DRY RUN — no changes will be made.")
        print(f"  Would copy license/ to {args.feedsfun_dir}/license/")
        print(f"  Would patch {app_file}")
        return

    # Step 1: Copy license module
    print("[1/2] Copying license module...")
    if not copy_license_module(args.feedsfun_dir, args.source_dir):
        sys.exit(1)

    # Step 2: Patch application.py
    print("[2/2] Patching application.py...")
    if not patch_application(app_file):
        sys.exit(1)

    print()
    print("=== Installation Complete ===")
    print()
    print("Next steps:")
    print("  1. Add LICENSE_SECRET_KEY to .env")
    print("  2. Restart feeds.fun: docker compose restart backend-single-user")
    print("  3. Generate a license: python3 scripts/license_gen.py --days 30")
    print("  4. Test: curl -H 'X-License-Code: <token>' http://localhost:8000/api/license/status")


if __name__ == "__main__":
    main()
