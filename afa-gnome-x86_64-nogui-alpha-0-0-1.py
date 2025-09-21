# Written by Amilie for the Archcord Community
# ArchForAll is a simple, yet effective, Arch installation script.

# Necessary for running the unix commands.
import os
import socket
import sys
import subprocess
import time

def pre_disk():
    # System needs to have internet in order to continue with installation.
    def check_internet():
        try:
            socket.getaddrinfo('google.com', 80)
            return True
        except:
            print("Your system does not have an appropriate connection. Please see iwctl docs for more information.")
            return False

    # If there is no internet, the script will be exited.
    if not check_internet():
        sys.exit("NO_INTERNET")

    # Load United States keymap for installation.
    # Probably not necessary - but it's just to be sure.
    os.system('loadkeys us')

    # Call check internet function to ensure internet connectivity is enabled.
    check_internet()

    # Ensure OS is of required firmware version. For more information see https://wiki.archlinux.org/title/Installation_guide, section 1.6.
    try:
        sysstatus = int(subprocess.check_output(['cat', '/sys/firmware/efi/fw_platform_size']).decode().strip())
    except Exception:
        sysstatus = 0

    if sysstatus == 64:
        pass
    elif sysstatus == 32:
        print("---------------------------------------------------------------------------------------------------------------------")
        print("System is booted with 32bit UEFI. This is unsupported on Arch for All - Please reboot with an appropriate UEFI setup.")
        print("---------------------------------------------------------------------------------------------------------------------")
    else:
        print("----------------------------------------------------------------------------------------------------------")
        print("No supported UEFI/EFI setup found. Reboot and boot via Arch UEFI. Ensure your system supports 64 bit UEFI.")
        print("----------------------------------------------------------------------------------------------------------")


    # Sync System Clock.
    os.system('timedatectl set-ntp true')

    # Disk partitioning. Query the user for what disk they want to partition.
    os.system('lsblk')
    print("Above is a list of all your disks. Please find which disk is yours and type it in below. You must include /dev/ for example: /dev/sda or /dev/nvme0n1")
    disk_selected = input("Input which disk you want to select: ").strip()

    print("!!! THE FOLLOWING ACTIONS WILL WIPE THIS DISK COMPLETELY. THERE IS NO TURNING BACK.")
    disk_confirmation = input("ARE YOU COMPLETELY SURE? [Y/n]").lower()

    # This is the dangerous section! This actually wipes the disk! DO NOT CALL WITHOUT PRIOR CONFIRMATION AND ENSURING YOU NEED IT.
    def disk_partitioning_procedure():
        global disk_selected
        sfdisk_script = f"""
        label: gpt
        ,1G,ef02
        ,8G,8200
        ,,8300
        """

        print(f"Now writing the partition table to {disk_selected}!")
        os.system(f"echo '{sfdisk_script}' | sfdisk {disk_selected}")

        # Actually format the partitions to the required selection.
        # Includes checks for nvmes, and general drives. NVMEs are different for some reason.
        if "nvme" in disk_selected:
            part1 = f"{disk_selected}p1"
            part2 = f"{disk_selected}p2"
            part3 = f"{disk_selected}p3"
        else:
            part1 = f"{disk_selected}1"
            part2 = f"{disk_selected}2"
            part3 = f"{disk_selected}3"

        os.system(f"mkfs.fat -F32 {part1}")
        os.system(f"mkswap {part2}")
        os.system(f"mkfs.ext4 {part3}")

        # Mounting users drives. Prepare for completion of drive section, the dangerous section.
        os.system(f"mkdir /mnt")
        os.system(f"mkdir /mnt/boot")
        os.system(f"swapon {part2}")
        os.system(f"mount {part3} /mnt")
        os.system(f"mount {part1} /mnt/boot")

    if disk_confirmation == 'n':
        sys.exit("DENY_DISK_MODIFICATION")
    else:
        disk_partitioning_procedure()

def post_disk():
    # Installing core user packages.
    print("Beginning installation of core packages! Hold tight!")
    time.sleep(3)
    os.system(f"pacstrap -K /mnt linux linux-firmware nano man man-db sof-firmware dosfstools e2fsprogs ntfs-3g networkmanager")

    # Fstab Generation
    os.system(f"genfstab -U /mnt >> /mnt/etc/fstab")

    user_timezone = input("What is your timezone? Please input in the format Continent/Capital - eg Europe/London, or Africa/Cairo")
    print("You may need to use timedatectl list-timezones for this, if you do not know what city to put - I recommend Europe/London - you can fix it post install!")
    os.system(f'arch-chroot /mnt /bin/bash -c "ln -sf /usr/share/zoneinfo/{user_timezone} /etc/localtime"')
    os.system(f'arch-chroot /mnt /bin/bash -c "hwclock --systohc"')

    print("By default, your system will be in English - with the keyboard US. You can again, change this at a later data via GNOME settings.")
    os.system('arch-chroot /mnt /bin/bash -c "echo LANG=en_US.UTF-8 > /etc/locale.conf"')
    os.system('arch-chroot /mnt /bin/bash -c "locale-gen"')

    print("What would you like your system to be called?")
    user_hostname = input("Input here: ").lower().strip()
    os.system(f'arch-chroot /mnt /bin/bash -c "echo {user_hostname} > /etc/hostname"')

    os.system(f'arch-chroot /mnt /bin/bash -c "mkinitcpio -P"')
    
    print("What would you like your root password to be? (This is for sudo commands!)")
    user_root_password = input("Input here: ")
    os.system(f'arch-chroot /mnt /bin/bash -c "echo root:{user_root_password} | chpasswd"')

    print("What would you like your user account to be called? (This is for the desktop!)")
    user_username = input("Input here: ")
    os.system(f'arch-chroot /mnt /bin/bash -c "useradd -m -G wheel -s /bin/bash {user_username}"')

    print("And your users password? ")
    user_password = input("Input here: ")
    os.system(f'arch-chroot /mnt /bin/bash -c "echo {user_username}:{user_password} | chpasswd"')

    os.system(f'arch-chroot /mnt /bin/bash -c "bootctl install"')

    os.system(f'arch-chroot /mnt /bin/bash -c "pacman -S gnome gdm gnome-tweaks gnome-shell-extensions --noconfirm"')
    os.system(f'arch-chroot /mnt /bin/bash -c "systemctl enable gdm"')

    os.system(f'arch-chroot /mnt /bin/bash -c "pacman -S git base-devel --noconfirm"')
    os.system(f'arch-chroot /mnt /bin/bash -c "git clone https://aur.archlinux.org/yay.git && cd yay && makepkg -si --noconfirm && cd /"')

    print("Preparing to reboot! Once the screen goes fully black, unplug your USB!")
    time.sleep(5)
    os.system("reboot")

def main():
    pre_disk()
    post_disk()

main()
