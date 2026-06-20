#!/bin/bash
# Theonix OS - Initial Archiso Build Script
# This script wraps the archiso build process to generate a minimal bootable ISO.

set -e

# Configuration
# Use native linux filesystem for heavy I/O
WORKDIR="/build-cache/work_$(date +%s)"
OUTDIR="/build-cache/out"
PROFILE_DIR="/build-cache/profile_$(date +%s)"
ISO_NAME="theonix-os-beta"
ISO_LABEL="THEONIX_$(date +%Y%m)"

echo "=== Theonix OS ISO Builder ==="

# Check for root
if [ "$EUID" -ne 0 ]; then
  echo "Error: Please run as root."
  exit 1
fi

# Check dependencies
if ! command -v mkarchiso &> /dev/null; then
    echo "Error: archiso is not installed. Please install it (e.g., pacman -S archiso)."
    exit 1
fi

# Setup profile directory from scratch every time to ensure no corrupted files exist
echo "Copying clean releng profile..."
rm -rf "$PROFILE_DIR"
cp -r /usr/share/archiso/configs/releng/ "$PROFILE_DIR"

echo "Overlaying custom profile configurations..."
cp -aT /workdir/profile/ "$PROFILE_DIR"

# Customizing the packages
echo "Customizing packages..."
cat <<EOF >> "$PROFILE_DIR/packages.x86_64"
# Theonix OS Core Packages
wayland
plasma-meta
sddm
ollama
networkmanager
pipewire
wireplumber
apparmor
plymouth
EOF

# Branding configuration
echo "Applying Theonix OS Branding..."
find "$PROFILE_DIR/syslinux" -type f -name "*.cfg" -exec sed -i 's/Arch Linux/Theonix OS/g' {} +
find "$PROFILE_DIR/efiboot/loader/entries" -type f -name "*.conf" -exec sed -i 's/Arch Linux/Theonix OS/g' {} +
find "$PROFILE_DIR/grub" -type f -name "*.cfg" -exec sed -i 's/Arch Linux/Theonix OS/g' {} +
sed -i 's/Arch Linux/Theonix OS/g' "$PROFILE_DIR/airootfs/etc/motd"

# Patch profiledef.sh so mkarchiso names the ISO correctly
echo "Patching profiledef.sh..."
sed -i "s/iso_name=\"archlinux\"/iso_name=\"theonix-os\"/g" "$PROFILE_DIR/profiledef.sh"
sed -i "s/iso_label=\"ARCH_\$(date +%Y%m)\"/iso_label=\"THEONIX_$(date +%Y%m)\"/g" "$PROFILE_DIR/profiledef.sh"
sed -i "s/iso_publisher=\"Arch Linux <https:\/\/archlinux.org>\"/iso_publisher=\"Theonix OS <https:\/\/theonix.org>\"/g" "$PROFILE_DIR/profiledef.sh"
sed -i "s/iso_application=\"Arch Linux live\/rescue disk\"/iso_application=\"Theonix OS Live\"/g" "$PROFILE_DIR/profiledef.sh"

# Configure os-release
cat <<EOF > "$PROFILE_DIR/airootfs/etc/os-release"
NAME="Theonix OS"
PRETTY_NAME="Theonix OS"
ID=theonix
BUILD_ID=rolling
ANSI_COLOR="38;2;23;147;209"
HOME_URL="https://theonix.org/"
DOCUMENTATION_URL="https://theonix.org/docs"
SUPPORT_URL="https://theonix.org/support"
BUG_REPORT_URL="https://github.com/theonix-os/issues"
LOGO=theonix-logo
EOF

# Write archiso.conf with zstd compression (xz -9e hangs in Docker)
echo "Writing archiso.conf with zstd compression..."
mkdir -p "$PROFILE_DIR/airootfs/etc/mkinitcpio.conf.d"
cat <<EOF > "$PROFILE_DIR/airootfs/etc/mkinitcpio.conf.d/archiso.conf"
HOOKS=(base udev plymouth microcode modconf kms memdisk archiso archiso_loop_mnt archiso_pxe_common archiso_pxe_nbd archiso_pxe_http archiso_pxe_nfs block filesystems keyboard)
COMPRESSION="zstd"
COMPRESSION_OPTIONS=(-19 --long)
EOF

# Ensure SDDM auto-login is active
mkdir -p "$PROFILE_DIR/airootfs/etc/sddm.conf.d"
cat <<EOF > "$PROFILE_DIR/airootfs/etc/sddm.conf.d/autologin.conf"
[Autologin]
User=root
Session=plasma
EOF

# Ensure a clean workdir so mkarchiso doesn't use cached Arch Linux branding
echo "Using unique workdir..."
mkdir -p "$WORKDIR" "$OUTDIR"

# Ensure critical packages are in the list
echo "Ensuring required packages are included..."
for pkg in plymouth calamares; do
    if ! grep -q "^$pkg$" "$PROFILE_DIR/packages.x86_64"; then
        echo "$pkg" >> "$PROFILE_DIR/packages.x86_64"
    fi
done

# Ensure problematic packages are removed because they break the Live ISO build
sed -i '/^snapper$/d' "$PROFILE_DIR/packages.x86_64"
sed -i '/^grub-btrfs$/d' "$PROFILE_DIR/packages.x86_64"

# Inject custom UI themes into the Live Environment
echo "Injecting UI themes..."
mkdir -p "$PROFILE_DIR/airootfs/etc/theonix"
if [ -f "design/ui_mockups/theme.qss" ]; then
    cp "design/ui_mockups/theme.qss" "$PROFILE_DIR/airootfs/etc/theonix/"
fi

# Install custom design themes
echo "Installing custom design themes..."
mkdir -p "$PROFILE_DIR/airootfs/usr/share/sddm/themes"
cp -a /workdir/design/themes/sddm/theonix "$PROFILE_DIR/airootfs/usr/share/sddm/themes/"

mkdir -p "$PROFILE_DIR/airootfs/usr/share/plymouth/themes"
cp -a /workdir/design/themes/plymouth/theonix "$PROFILE_DIR/airootfs/usr/share/plymouth/themes/"

mkdir -p "$PROFILE_DIR/airootfs/usr/share/plasma/look-and-feel"
cp -a /workdir/design/themes/kde/theonix "$PROFILE_DIR/airootfs/usr/share/plasma/look-and-feel/org.theonix.desktop"

mkdir -p "$PROFILE_DIR/airootfs/usr/share/color-schemes"
cp -a /workdir/design/themes/kde/theonix/colors/Theonix.colors "$PROFILE_DIR/airootfs/usr/share/color-schemes/"

mkdir -p "$PROFILE_DIR/airootfs/usr/share/wallpapers/Theonix/contents/images"
cp -a /workdir/design/themes/kde/theonix/contents/images/3840x2160.png "$PROFILE_DIR/airootfs/usr/share/wallpapers/Theonix/contents/images/"
cp -a /workdir/design/themes/kde/wallpaper_metadata.desktop "$PROFILE_DIR/airootfs/usr/share/wallpapers/Theonix/metadata.desktop"

mkdir -p "$PROFILE_DIR/airootfs/usr/share/grub/themes"
cp -a /workdir/design/themes/grub/theonix "$PROFILE_DIR/airootfs/usr/share/grub/themes/"

# Install Calamares configurations
echo "Installing Calamares configurations..."
mkdir -p "$PROFILE_DIR/airootfs/etc/calamares"
cp -a /workdir/calamares/* "$PROFILE_DIR/airootfs/etc/calamares/"

# Enable SDDM and Graphical Boot directly before build to avoid Windows symlink issues
echo "Configuring systemd targets for graphical boot..."
mkdir -p "$PROFILE_DIR/airootfs/etc/systemd/system/multi-user.target.wants"
ln -sf /usr/lib/systemd/system/sddm.service "$PROFILE_DIR/airootfs/etc/systemd/system/display-manager.service"
ln -sf /usr/lib/systemd/system/graphical.target "$PROFILE_DIR/airootfs/etc/systemd/system/default.target"
ln -sf /usr/lib/systemd/system/NetworkManager.service "$PROFILE_DIR/airootfs/etc/systemd/system/multi-user.target.wants/NetworkManager.service"
ln -sf /usr/lib/systemd/system/systemd-resolved.service "$PROFILE_DIR/airootfs/etc/systemd/system/multi-user.target.wants/systemd-resolved.service"

# Build ISO
echo "Starting ISO build..."
mkarchiso -v -w "$WORKDIR" -o "$OUTDIR" "$PROFILE_DIR"

echo "=== Build Complete ==="
echo "ISO is located in $OUTDIR/"
