#!/usr/bin/env bash
# =============================================================================
# Theonix OS — scripts/setup_btrfs_subvols.sh
# =============================================================================
# Creates the recommended btrfs subvolume layout for Theonix OS.
# Called by the Calamares post-install script or manually during installation.
#
# Subvolume layout:
#   @           → /
#   @home       → /home
#   @var        → /var
#   @var_log    → /var/log
#   @snapshots  → /.snapshots
#   @swap       → /swap (for swapfile, optional)
#
# Usage:
#   sudo ./setup_btrfs_subvols.sh /dev/sdXN /mnt
#   sudo ./setup_btrfs_subvols.sh /dev/mapper/luks-root /mnt
# =============================================================================

set -euo pipefail

DEVICE="${1:-}"
MOUNT_POINT="${2:-/mnt}"

if [[ -z "${DEVICE}" ]]; then
    echo "Usage: $0 <btrfs-device> [mount-point]" >&2
    echo "  e.g. $0 /dev/sda2 /mnt" >&2
    exit 1
fi

if [[ "${EUID}" -ne 0 ]]; then
    echo "ERROR: Must run as root." >&2
    exit 1
fi

echo "==> Theonix btrfs subvolume setup"
echo "    Device:      ${DEVICE}"
echo "    Mount point: ${MOUNT_POINT}"
echo ""

# Mount the top-level btrfs filesystem (subvol=5 = FS root)
echo "==> Mounting btrfs root..."
mkdir -p "${MOUNT_POINT}"
mount -o "defaults,noatime,compress=zstd:3,subvol=/" "${DEVICE}" "${MOUNT_POINT}"

# Create subvolumes
echo "==> Creating subvolumes..."
for subvol in @ @home @var @var_log @snapshots @swap; do
    if btrfs subvolume show "${MOUNT_POINT}/${subvol}" &>/dev/null; then
        echo "    [SKIP] Subvolume already exists: ${subvol}"
    else
        btrfs subvolume create "${MOUNT_POINT}/${subvol}"
        echo "    [CREATE] ${subvol}"
    fi
done

# Unmount top-level before remounting individual subvolumes
echo "==> Unmounting top-level..."
umount "${MOUNT_POINT}"

# Mount subvolumes into their correct positions
BTRFS_OPTS="defaults,noatime,compress=zstd:3,space_cache=v2"

echo "==> Mounting subvolumes..."

mount -o "${BTRFS_OPTS},subvol=@"          "${DEVICE}" "${MOUNT_POINT}"
mkdir -p "${MOUNT_POINT}"/{home,var,.snapshots,swap}
mkdir -p "${MOUNT_POINT}/var/log"

mount -o "${BTRFS_OPTS},subvol=@home"      "${DEVICE}" "${MOUNT_POINT}/home"
mount -o "${BTRFS_OPTS},subvol=@var"       "${DEVICE}" "${MOUNT_POINT}/var"
mount -o "${BTRFS_OPTS},subvol=@var_log"   "${DEVICE}" "${MOUNT_POINT}/var/log"
mount -o "${BTRFS_OPTS},subvol=@snapshots" "${DEVICE}" "${MOUNT_POINT}/.snapshots"
mount -o "${BTRFS_OPTS},subvol=@swap"      "${DEVICE}" "${MOUNT_POINT}/swap"

# Disable CoW on /var (pacman databases don't benefit from CoW)
chattr +C "${MOUNT_POINT}/var" 2>/dev/null || true

echo ""
echo "==> Subvolume layout complete. Verify with:"
echo "    btrfs subvolume list ${MOUNT_POINT}"
echo ""
btrfs subvolume list "${MOUNT_POINT}"
