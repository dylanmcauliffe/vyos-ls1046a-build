#!/usr/bin/env python3
"""Patch image_installer.py to make architecture/flavor compatibility check
graceful when the new image lacks metadata fields.

The upstream validate_compatibility() treats missing architecture/flavor as a
hard failure (aborts installation).  On LS1046A we may install images built
without these fields, so we downgrade missing-field checks to warnings.

Applied during vyos-1x build via pre_build_hook.
"""

import re
import sys
from pathlib import Path

TARGET = Path("src/op_mode/image_installer.py")

if not TARGET.exists():
    print(f"W: {TARGET} not found — skipping image compat patch")
    sys.exit(0)

src = TARGET.read_text()

# --- Patch 1: Missing architecture → warning instead of failure ---
# Original pattern:
#     if current_architecture != new_architecture:
#         success = False
#         if not new_architecture:
#             print(MSG_ERR_MISSING_ARCHITECTURE)
#         else:
#             print(MSG_ERR_ARCHITECTURE_MISMATCH.format(...))
#
# Replacement: skip check entirely when new_architecture is None

old_arch = re.compile(
    r'(\s+)if current_architecture != new_architecture:\s*\n'
    r'\1    success = False\s*\n'
    r'\1    if not new_architecture:\s*\n'
    r'\1        print\(MSG_ERR_MISSING_ARCHITECTURE\)\s*\n'
    r'\1    else:\s*\n'
    r'\1        print\(MSG_ERR_ARCHITECTURE_MISMATCH\.format\(current_architecture,\s*new_architecture\)\)',
    re.MULTILINE
)

new_arch_code = r"""\1if not new_architecture:
\1    print('W: New image does not specify architecture, skipping check')
\1elif current_architecture != new_architecture:
\1    success = False
\1    print(MSG_ERR_ARCHITECTURE_MISMATCH.format(current_architecture, new_architecture))"""

result, count = old_arch.subn(new_arch_code, src)
if count:
    print("  ✓ Patched architecture check (missing → warning)")
    src = result
else:
    print("  W: Architecture check pattern not found — may already be patched or code changed")

# --- Patch 2: Missing flavor → warning instead of failure ---
# Original pattern:
#     if current_flavor != new_flavor:
#         if not force:
#             success = False
#         if not new_flavor:
#             print(MSG_ERR_MISSING_FLAVOR)
#         else:
#             print(MSG_ERR_FLAVOR_MISMATCH.format(...))

old_flavor = re.compile(
    r'(\s+)if current_flavor != new_flavor:\s*\n'
    r'\1    if not force:\s*\n'
    r'\1        success = False\s*\n'
    r'\1    if not new_flavor:\s*\n'
    r'\1        print\(MSG_ERR_MISSING_FLAVOR\)\s*\n'
    r'\1    else:\s*\n'
    r'\1        print\(MSG_ERR_FLAVOR_MISMATCH\.format\(current_flavor,\s*new_flavor\)\)',
    re.MULTILINE
)

new_flavor_code = r"""\1if not new_flavor:
\1    print('W: New image does not specify flavor, skipping check')
\1elif current_flavor != new_flavor:
\1    if not force:
\1        success = False
\1    print(MSG_ERR_FLAVOR_MISMATCH.format(current_flavor, new_flavor))"""

result, count = old_flavor.subn(new_flavor_code, src)
if count:
    print("  ✓ Patched flavor check (missing → warning)")
    src = result
else:
    print("  W: Flavor check pattern not found — may already be patched or code changed")

TARGET.write_text(src)
print(f"  image_installer.py patched successfully")