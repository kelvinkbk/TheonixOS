#!/bin/bash
echo "==> Preparing environment..."
umount -R /mnt 2>/dev/null || true
mount /dev/sda2 /mnt
mkdir -p /mnt/boot/efi
mount /dev/sda1 /mnt/boot/efi

echo "==> Configuring GRUB to use direct partition paths instead of UUIDs..."
sed -i 's/.*GRUB_DISABLE_LINUX_UUID.*/GRUB_DISABLE_LINUX_UUID=true/g' /mnt/etc/default/grub
if ! grep -q "GRUB_DISABLE_LINUX_UUID=true" /mnt/etc/default/grub; then
    echo "GRUB_DISABLE_LINUX_UUID=true" >> /mnt/etc/default/grub
fi

echo "==> Generating clean GRUB configuration..."
arch-chroot /mnt /usr/bin/grub-mkconfig -o /boot/grub/grub.cfg

echo "==> Appending Failsafe Boot Entry..."
cat << 'EOF' >> /mnt/boot/grub/grub.cfg

menuentry "Theonix OS (Direct Boot)" {
    load_video
    set gfxpayload=keep
    insmod gzio
    insmod part_gpt
    insmod ext2
    set root='hd0,gpt2'
    linux /boot/vmlinuz-linux root=/dev/sda2 rw quiet
    initrd /boot/initramfs-linux.img
}
EOF

echo "==> Cleaning up..."
umount -R /mnt
echo "==> GRUB SUCCESSFULLY PATCHED! You can safely reboot now!"
