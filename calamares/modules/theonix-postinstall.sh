#!/bin/bash
# =============================================================================
# Theonix OS — Post-Install Configuration Script
# =============================================================================
# Called by Calamares via shellprocess module after all packages are installed.
# Runs inside the target system chroot.
# =============================================================================

set -e

echo "==> theonix-postinstall: Starting"

# ---- 1. Enable essential services -------------------------------------------
for service in \
    NetworkManager \
    sddm \
    fstrim.timer \
    paccache.timer; do
    if systemctl enable "$service" 2>/dev/null; then
        echo "  Enabled: $service"
    else
        echo "  Warning: Failed to enable $service (may not be installed)"
    fi
done

# ---- 2. Mask live-ISO-only services -----------------------------------------
for service in \
    livecd-talk \
    choose-mirror \
    pacman-init; do
    systemctl mask "$service" 2>/dev/null && echo "  Masked: $service" || true
done

# ---- 3. Set SDDM theme -----------------------------------------------------
mkdir -p /etc/sddm.conf.d
cat > /etc/sddm.conf.d/theonix.conf << 'SDDM_EOF'
[Theme]
Current=theonix
SDDM_EOF
echo "  SDDM theme set to: theonix"

# ---- 4. Set Plymouth theme --------------------------------------------------
if command -v plymouth-set-default-theme &>/dev/null; then
    # Copy the Theonix Plymouth theme into the installed system
    THEME_SRC="/usr/share/plymouth/themes/theonix"
    if [ -d "$THEME_SRC" ]; then
        plymouth-set-default-theme theonix 2>/dev/null && \
            echo "  Plymouth theme set to: theonix" || \
            echo "  Warning: Plymouth theme set failed (non-fatal)"
        
        # Add 'plymouth' hook to mkinitcpio and rebuild initramfs
        # so the splash appears on actual boot, not just in the live session
        MKINITCPIO_CONF="/etc/mkinitcpio.conf"
        if [ -f "$MKINITCPIO_CONF" ] && ! grep -q "plymouth" "$MKINITCPIO_CONF"; then
            sed -i 's/^HOOKS=(\(.*\)udev\(.*\))/HOOKS=(\1udev plymouth\2)/' \
                "$MKINITCPIO_CONF" 2>/dev/null || true
            echo "  Added plymouth hook to mkinitcpio.conf"
        fi
        mkinitcpio -P 2>/dev/null && echo "  initramfs rebuilt with Plymouth" || \
            echo "  Warning: mkinitcpio failed (non-fatal)"
    else
        echo "  Warning: Theonix Plymouth theme not found, skipping"
    fi
else
    echo "  Warning: plymouth-set-default-theme not available (non-fatal)"
fi

# ---- 5. Configure journald limits -------------------------------------------
mkdir -p /etc/systemd/journald.conf.d
cat > /etc/systemd/journald.conf.d/theonix.conf << 'JOURNAL_EOF'
[Journal]
SystemMaxUse=500M
SystemKeepFree=1G
MaxFileSec=1month
Compress=yes
JOURNAL_EOF
echo "  journald limits configured"

# ---- 6. Enable tmpfs /tmp ---------------------------------------------------
systemctl enable tmp.mount 2>/dev/null || true
echo "  tmpfs /tmp enabled"

# ---- 7. Set GRUB defaults for the installed system --------------------------
cat > /etc/default/grub << 'GRUB_EOF'
GRUB_DEFAULT=0
GRUB_TIMEOUT=3
GRUB_TIMEOUT_STYLE=hidden
GRUB_DISTRIBUTOR="Theonix OS"
GRUB_CMDLINE_LINUX_DEFAULT="quiet loglevel=3 systemd.show_status=auto rd.udev.log_level=3 splash video=1920x1080"
GRUB_CMDLINE_LINUX=""
GRUB_PRELOAD_MODULES="part_gpt part_msdos"
GRUB_TERMINAL_INPUT=console
GRUB_GFXMODE=auto
GRUB_GFXPAYLOAD_LINUX=keep
GRUB_DISABLE_RECOVERY=false
GRUB_EOF

# Regenerate GRUB config
grub-mkconfig -o /boot/grub/grub.cfg 2>/dev/null || \
    echo "  Warning: grub-mkconfig failed (may be OK if using systemd-boot)"

# ---- 8. Create the first-boot wizard marker ---------------------------------
mkdir -p /etc/theonix
touch /etc/theonix/firstboot
echo "  First-boot wizard marker created"

# ---- 9. Write Theonix OS os-release additions -------------------------------
cat >> /etc/os-release << 'OSREL_EOF'

# Theonix OS additions
THEONIX_VERSION="1.0"
THEONIX_CODENAME="Orion"
THEONIX_WEBSITE="https://theonix.org"
THEONIX_CREATOR="Kelvin Benny Koshy"
OSREL_EOF

# ---- 10. Set package cache cleanup policy -----------------------------------
cat > /etc/paccache.conf << 'PACC_EOF'
[paccache]
KEEP=2
PACC_EOF

echo "==> theonix-postinstall: Complete"
