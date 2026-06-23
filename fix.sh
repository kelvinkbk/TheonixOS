#!/bin/bash
echo "==> Deploying ultimate arch-chroot bypass fix..."

# 1. Remove broken modules
sed -i '/- bootloader/d' /etc/calamares/settings.conf
sed -i '/- packages/d' /etc/calamares/settings.conf

# 2. Inject our custom grub-install shellprocess safely (only if not already there)
if ! grep -q "shellprocess@grubinstall" /etc/calamares/settings.conf; then
    sed -i '/- grubcfg/a \      - shellprocess@grubinstall' /etc/calamares/settings.conf
fi

# 3. Create the custom shellprocess module
cat << 'EOF' > /etc/calamares/modules/shellprocess_grubinstall.conf
# SPDX-FileCopyrightText: no
# SPDX-License-Identifier: CC0-1.0
---
dontChroot: true
timeout: 300
script:
  - "arch-chroot ${ROOT} /usr/bin/grub-install --target=x86_64-efi --efi-directory=/boot/efi --bootloader-id=theonix --force --no-nvram"
  - "arch-chroot ${ROOT} mkdir -p /boot/efi/EFI/BOOT"
  - "arch-chroot ${ROOT} cp /boot/efi/EFI/theonix/grubx64.efi /boot/efi/EFI/BOOT/BOOTX64.EFI"
EOF

# Fix gsName just in case grubcfg needs it
sed -i 's/gsname/gsName/g' /etc/calamares/modules/grubcfg.conf

echo "==> Live VM successfully patched! You can now run Calamares!"
