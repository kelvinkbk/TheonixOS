#!/bin/bash
# =============================================================================
# Theonix OS — Bootloader Installation Script
# =============================================================================
# Replaces the native Calamares bootloader module for full control.
# Handles UEFI, BIOS/MBR, and BIOS/GPT (with BIOS Boot Partition creation).
# Logs everything to help debug failures.
# =============================================================================

set -euo pipefail

if [ -z "${ROOT:-}" ]; then
    echo "ERROR: ROOT variable is not set."
    exit 1
fi

LOG="/tmp/theonix-bootloader.log"
exec > >(tee -a "$LOG") 2>&1

echo "==> bootloader: Starting bootloader installation..."
echo "==> bootloader: ROOT=$ROOT"
echo "==> bootloader: Date: $(date)"

# Detect firmware type
if [ -d /sys/firmware/efi ]; then
    FIRMWARE="uefi"
else
    FIRMWARE="bios"
fi
echo "==> bootloader: Firmware type: $FIRMWARE"

# Find the root device
ROOT_DEV=$(findmnt -n -o SOURCE "$ROOT" 2>/dev/null || true)
if [ -z "$ROOT_DEV" ]; then
    ROOT_DEV=$(awk '$2=="/" {print $1; exit}' "${ROOT}/etc/fstab" 2>/dev/null || true)
fi
echo "==> bootloader: Root device: $ROOT_DEV"

# Get the parent disk (e.g., /dev/sda from /dev/sda2)
if [ -n "$ROOT_DEV" ]; then
    DISK=$(lsblk -ndo pkname "$ROOT_DEV" 2>/dev/null | head -1)
    if [ -n "$DISK" ]; then
        DISK="/dev/$DISK"
    else
        # Fallback: strip trailing partition number
        DISK=$(echo "$ROOT_DEV" | sed 's/[0-9]*$//' | sed 's/p$//')
    fi
else
    DISK="/dev/sda"
fi
echo "==> bootloader: Target disk: $DISK"

# Detect partition table type
TABLE_TYPE=$(blkid -o value -s PTTYPE "$DISK" 2>/dev/null || echo "unknown")
echo "==> bootloader: Partition table: $TABLE_TYPE"

# Ensure GRUB is installed in the target
if [ ! -f "${ROOT}/usr/bin/grub-install" ]; then
    echo "==> bootloader: grub-install not found in target. Installing grub..."
    arch-chroot "${ROOT}" pacman -S --noconfirm grub 2>&1 || true
fi

install_grub_uefi() {
    echo "==> bootloader: Installing GRUB for UEFI..."

    # Ensure EFI directory exists
    local EFI_DIR="${ROOT}/boot/efi"
    mkdir -p "$EFI_DIR"

    # Mount EFI partition if not already mounted
    local EFI_PART=$(fdisk -l "$DISK" 2>/dev/null | grep -i 'EFI' | awk '{print $1}' | head -1)
    if [ -n "$EFI_PART" ] && ! mountpoint -q "$EFI_DIR" 2>/dev/null; then
        mount "$EFI_PART" "$EFI_DIR" 2>/dev/null || true
    fi

    # Try 1: Normal EFI install
    echo "==> bootloader: Attempt 1 — standard EFI install"
    if arch-chroot "${ROOT}" grub-install \
        --target=x86_64-efi \
        --efi-directory=/boot/efi \
        --bootloader-id=theonix \
        --recheck 2>&1; then
        echo "==> bootloader: UEFI install succeeded (standard)."
        # Copy to fallback path
        mkdir -p "${EFI_DIR}/EFI/BOOT"
        cp "${EFI_DIR}/EFI/theonix/grubx64.efi" "${EFI_DIR}/EFI/BOOT/BOOTX64.EFI" 2>/dev/null || true
        return 0
    fi

    # Try 2: With --no-nvram
    echo "==> bootloader: Attempt 2 — EFI with --no-nvram"
    if arch-chroot "${ROOT}" grub-install \
        --target=x86_64-efi \
        --efi-directory=/boot/efi \
        --bootloader-id=theonix \
        --no-nvram \
        --recheck 2>&1; then
        echo "==> bootloader: UEFI install succeeded (no-nvram)."
        mkdir -p "${EFI_DIR}/EFI/BOOT"
        cp "${EFI_DIR}/EFI/theonix/grubx64.efi" "${EFI_DIR}/EFI/BOOT/BOOTX64.EFI" 2>/dev/null || true
        return 0
    fi

    # Try 3: Removable + no-nvram (ultimate fallback)
    echo "==> bootloader: Attempt 3 — EFI with --removable --no-nvram"
    if arch-chroot "${ROOT}" grub-install \
        --target=x86_64-efi \
        --efi-directory=/boot/efi \
        --removable \
        --no-nvram \
        --recheck 2>&1; then
        echo "==> bootloader: UEFI install succeeded (removable)."
        return 0
    fi

    echo "==> bootloader: All UEFI attempts failed!"
    return 1
}

install_grub_bios() {
    echo "==> bootloader: Installing GRUB for BIOS on $DISK..."

    # Try 1: Normal BIOS install
    echo "==> bootloader: Attempt 1 — standard BIOS install"
    if arch-chroot "${ROOT}" grub-install \
        --target=i386-pc \
        --recheck \
        "$DISK" 2>&1; then
        echo "==> bootloader: BIOS install succeeded (standard)."
        return 0
    fi

    # Try 2: With --no-floppy (fixes VMware)
    echo "==> bootloader: Attempt 2 — BIOS with --no-floppy"
    if arch-chroot "${ROOT}" grub-install \
        --target=i386-pc \
        --recheck \
        --no-floppy \
        "$DISK" 2>&1; then
        echo "==> bootloader: BIOS install succeeded (no-floppy)."
        return 0
    fi

    # Try 3: Force install
    echo "==> bootloader: Attempt 3 — BIOS with --force --no-floppy"
    if arch-chroot "${ROOT}" grub-install \
        --target=i386-pc \
        --recheck \
        --force \
        --no-floppy \
        "$DISK" 2>&1; then
        echo "==> bootloader: BIOS install succeeded (force)."
        return 0
    fi

    # Try 4: If GPT, try to create BIOS boot partition space
    if [ "$TABLE_TYPE" = "gpt" ]; then
        echo "==> bootloader: GPT detected on BIOS system. Trying --force with explicit boot directory..."
        if arch-chroot "${ROOT}" grub-install \
            --target=i386-pc \
            --boot-directory=/boot \
            --force \
            --no-floppy \
            "$DISK" 2>&1; then
            echo "==> bootloader: BIOS/GPT install succeeded."
            return 0
        fi
    fi

    echo "==> bootloader: All BIOS attempts failed!"
    return 1
}

# ---- Main ----

if [ "$FIRMWARE" = "uefi" ]; then
    install_grub_uefi
    RESULT=$?
else
    install_grub_bios
    RESULT=$?
fi

if [ $RESULT -ne 0 ]; then
    echo "==> bootloader: FATAL — Could not install GRUB. See $LOG for details."
    exit 1
fi

# Generate GRUB configuration
echo "==> bootloader: Generating grub.cfg..."
arch-chroot "${ROOT}" grub-mkconfig -o /boot/grub/grub.cfg 2>&1 || \
    echo "==> bootloader: Warning — grub-mkconfig failed (non-fatal)"

echo "==> bootloader: Complete. Log saved to $LOG"
