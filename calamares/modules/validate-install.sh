#!/bin/bash
# =============================================================================
# Theonix OS — Post-Install Validation Script
# =============================================================================
# Runs after all installation steps but BEFORE umount.
# Verifies the installed system has all critical files.
# If any check fails, the installation is aborted with a clear error.
# =============================================================================

set -e

if [ -z "${ROOT}" ]; then
    echo "ERROR: ROOT variable is not set."
    exit 1
fi

echo "==> validate: Checking installed system integrity..."

ERRORS=0

check_exists() {
    local path="$1"
    local desc="$2"
    if [ -e "${ROOT}${path}" ]; then
        echo "  OK:   ${desc} (${path})"
    else
        echo "  FAIL: ${desc} — ${path} MISSING"
        ERRORS=$((ERRORS + 1))
    fi
}

check_exists "/boot/vmlinuz-linux"       "Linux kernel"
check_exists "/boot/initramfs-linux.img" "Initramfs image"
check_exists "/boot/grub/grub.cfg"       "GRUB configuration"
check_exists "/etc/fstab"                "Filesystem table"
check_exists "/etc/machine-id"           "Machine ID"
check_exists "/etc/os-release"           "OS release info"
check_exists "/etc/passwd"               "User database"
check_exists "/etc/shadow"               "Shadow passwords"
check_exists "/usr/bin/bash"             "Bash shell"
check_exists "/usr/lib/systemd/systemd"  "Systemd init"
check_exists "/usr/bin/sddm"             "SDDM display manager"

# Check that the root filesystem has real content (not just bind mounts)
FILE_COUNT=$(find "${ROOT}/usr" -maxdepth 1 -type d 2>/dev/null | wc -l)
if [ "$FILE_COUNT" -lt 5 ]; then
    echo "  FAIL: /usr has fewer than 5 subdirectories — unpackfs likely failed!"
    ERRORS=$((ERRORS + 1))
else
    echo "  OK:   /usr directory is populated ($FILE_COUNT entries)"
fi

echo ""
if [ $ERRORS -gt 0 ]; then
    echo "==> validate: FAILED — $ERRORS critical checks failed!"
    echo "==> The installation cannot continue. The system would not boot."
    exit 1
else
    echo "==> validate: All checks passed. System is ready to boot."
fi
