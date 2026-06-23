#!/bin/bash
set -e
echo "==> Mounting installed system for full bootloader repair..."
mount /dev/sda2 /mnt
mkdir -p /mnt/boot/efi
mount /dev/sda1 /mnt/boot/efi

echo "==> Initializing pacman keyring..."
arch-chroot /mnt pacman-key --init
arch-chroot /mnt pacman-key --populate archlinux

echo "==> Installing Linux Kernel..."
arch-chroot /mnt pacman -Sy --noconfirm linux linux-firmware mkinitcpio

echo "==> Installing GRUB bootloader..."
arch-chroot /mnt /usr/bin/grub-install --target=x86_64-efi --efi-directory=/boot/efi --bootloader-id=theonix --force --no-nvram

echo "==> Creating VirtualBox UEFI fallback..."
arch-chroot /mnt mkdir -p /boot/efi/EFI/BOOT
arch-chroot /mnt cp /boot/efi/EFI/theonix/grubx64.efi /boot/efi/EFI/BOOT/BOOTX64.EFI

echo "==> Generating GRUB configuration menu..."
arch-chroot /mnt /usr/bin/grub-mkconfig -o /boot/grub/grub.cfg

echo "==> Cleaning up..."
umount -R /mnt

echo "==> FULL BOOTLOADER REPAIR SUCCESSFUL! You can safely reboot now!"
