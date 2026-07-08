#!/bin/bash
# =============================================================================
# Theonix OS — Dynamic airootfs.sfs Resolver
# =============================================================================
# Finds the SquashFS image at runtime and writes the real path into
# unpackfs.conf so Calamares always unpacks the correct file,
# regardless of boot method (normal, copytoram, Ventoy, etc.).
# =============================================================================

set -e

echo "==> unpackfs-resolve: Searching for airootfs.sfs..."

SOURCE=$(find /run/archiso -name airootfs.sfs 2>/dev/null | head -n1)

if [ -z "$SOURCE" ]; then
    echo "ERROR: Cannot locate airootfs.sfs anywhere under /run/archiso/"
    exit 1
fi

echo "==> unpackfs-resolve: Found airootfs.sfs at: $SOURCE"

cat > /etc/calamares/modules/unpackfs.conf <<EOF
---
unpack:
    - source: "$SOURCE"
      sourcefs: "squashfs"
      destination: ""
EOF

echo "==> unpackfs-resolve: Wrote unpackfs.conf with dynamic source path"
echo "==> unpackfs-resolve: Final unpackfs.conf contents:"
cat /etc/calamares/modules/unpackfs.conf
