#!/bin/bash
set -e
echo "==> Mounting installed system for final initramfs fix..."
umount -R /mnt 2>/dev/null || true
mount /dev/sda2 /mnt
mkdir -p /mnt/boot/efi
mount /dev/sda1 /mnt/boot/efi

echo "==> Rebuilding initramfs without archiso hooks..."
arch-chroot /mnt bash -c '
    HOOKS=(base udev autodetect microcode modconf kms keyboard keymap consolefont block filesystems fsck)
    echo "HOOKS=(${HOOKS[@]})" > /etc/mkinitcpio.conf
    rm -f /etc/mkinitcpio.conf.d/archiso.conf 2>/dev/null
    rm -f /etc/mkinitcpio.d/linux.preset 2>/dev/null
    # Ensure standard linux preset exists
    echo "PRESETS=(\"default\" \"fallback\")" > /etc/mkinitcpio.d/linux.preset
    echo "default_kver=\"/boot/vmlinuz-linux\"" >> /etc/mkinitcpio.d/linux.preset
    echo "default_image=\"/boot/initramfs-linux.img\"" >> /etc/mkinitcpio.d/linux.preset
    echo "fallback_kver=\"/boot/vmlinuz-linux\"" >> /etc/mkinitcpio.d/linux.preset
    echo "fallback_image=\"/boot/initramfs-linux.img\"" >> /etc/mkinitcpio.d/linux.preset
    echo "fallback_options=\"-S autodetect\"" >> /etc/mkinitcpio.d/linux.preset
    
    mkinitcpio -P
'

echo "==> Updating GRUB..."
arch-chroot /mnt /usr/bin/grub-mkconfig -o /boot/grub/grub.cfg

umount -R /mnt
echo "==> FINISHED! You can safely reboot now!"
