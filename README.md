# ASIXFlash

[English](README.md) | [繁體中文](README.zh-TW.md)

_Change the permanent MAC address of ASIX AX88179-family USB Ethernet adapters. The change is stored on the adapter itself, so it persists when the adapter is plugged into a different computer._

![Changed MAC](https://raw.github.com/jglim/ASIXFlash/master/etc/mac-change.png)

> **Which chip do you have?** Adapters with the **original AX88179** use an EEPROM, which `flash.py` can rewrite. Newer adapters with the **AX88179B** (and AX88179A) share the same USB ID (`0b95:1790`) but store their MAC in **eFuse**, which `flash.py` does not support. Identify your chip first: see [Identify your chip](#identify-your-chip).

## Contents

- [Identify your chip](#identify-your-chip)
- [Original AX88179: flash.py (EEPROM)](#original-ax88179-flashpy-eeprom)
- [AX88179B / AX88179A: ASIX official tool (eFuse)](#ax88179b--ax88179a-asix-official-tool-efuse)
- [Choosing a MAC address](#choosing-a-mac-address)
- [Troubleshooting](#troubleshooting)
- [How it works](#how-it-works)
- [Credits and license](#credits-and-license)

## Identify your chip

Both chips report USB ID `0b95:1790`, so `lsusb` alone is not enough. Check the product string and `bcdDevice` (device revision):

```bash
lsusb -d 0b95:1790
lsusb -v -d 0b95:1790 2>/dev/null | grep -E 'bcdDevice|iProduct'
```

| Output | Chip | Storage | Use |
|---|---|---|---|
| `bcdDevice 1.00` | Original AX88179 | EEPROM (rewritable) | [`flash.py`](#original-ax88179-flashpy-eeprom) |
| `bcdDevice 2.00`, `iProduct ... AX88179B` | AX88179B | eFuse (append-only) | [ASIX official tool](#ax88179b--ax88179a-asix-official-tool-efuse) |
| `bcdDevice 2.00`, `iProduct ... AX88179A` | AX88179A | eFuse (append-only) | [ASIX official tool](#ax88179b--ax88179a-asix-official-tool-efuse) |

Other signs that you have an AX88179B:

- On Linux, `lsusb -t` shows the adapter bound to `cdc_ncm` (the AX88179B supports driverless CDC-NCM mode).
- `flash.py` fails with `USBError: [Errno 32] Pipe error` when reading the MAC.
- On Windows, a backup created by `flash.py` contains only `FF` bytes (see [jglim/ASIXFlash#3](https://github.com/jglim/ASIXFlash/issues/3)).

`flash.py` checks `bcdDevice` and refuses AX88179A/AX88179B devices before reading or writing anything.

## Original AX88179: flash.py (EEPROM)

Requires **Python 3.6+**, the **pyusb** package, and one of **libusb 0.1** / **libusb 1.0** / **OpenUSB**.

### Requirements

- Install libusb.
    - Linux: `sudo apt-get install libusb-1.0-0-dev`
    - macOS: via MacPorts, `sudo port install libusb`
    - Windows: there isn't a clear installation process, though [this installer for libusb-0.1 should work](https://sourceforge.net/projects/libusb-win32/files/libusb-win32-releases/1.2.6.0/libusb-win32-devel-filter-1.2.6.0.exe/download)
- Python 3.6+, with `pyusb`: `pip install -r ASIXFlash/requirements.txt`
- (Windows only) Change the loaded AX88179 driver to libusb:
    - Run Zadig `zadig-2.4.exe`
    - Select Options -> List all devices (✓)
    - In the dropdown list, select your AX88179 device
    - Press the little arrow on the up-down control until you get an option with `libusb-win32`
    - Click the big button, usually `Replace Driver`

![Zadig Guide](https://raw.github.com/jglim/ASIXFlash/master/etc/zadig.gif)

### Steps

1. Download and unarchive the repository into a folder.
2. Open `ASIXFlash/flash.py` and change `NEW_MAC_ADDRESS = "1BADCAFEBABE"` to the MAC address of your choice (12 hex digits, no separators). There are no checks, so make sure it is 100% accurate.
3. Run the script:
    - Windows / macOS: `python flash.py`
    - Linux: USB access normally requires root. If you use a virtual environment, run that environment's Python through sudo, for example `sudo ../venv/bin/python flash.py`. Plain `sudo python3` uses the system Python, which may not have `pyusb`.
4. The script prints the old MAC, backs up the EEPROM to `ax88179.bin`, writes the new MAC and prints the result. Keep `ax88179.bin`: it is your original EEPROM content.

![Demo](https://raw.github.com/jglim/ASIXFlash/master/etc/cmd.png)

The browser version in [`WebUSB/index.html`](WebUSB/index.html) uses the same EEPROM protocol and also supports only the original AX88179.

## AX88179B / AX88179A: ASIX official tool (eFuse)

The AX88179B stores its MAC address in **eFuse** (one-time programmable memory) instead of an EEPROM. ASIX ships a Linux programming tool with its driver source. This procedure was tested on Ubuntu (kernel 7.0, Secure Boot enabled) with an AX88179B adapter.

> [!WARNING]
> **eFuse writes are irreversible.** Programmed bits cannot be erased. Changing the MAC does not overwrite the old value: the tool appends a new record in an empty eFuse block, and the chip uses the latest valid record. Every change permanently consumes a block, and once no blocks are left, the MAC cannot be changed again.
>
> - Use only the MAC-only command (`wefuse -m ... -p ...`) shown below.
> - Do **not** use `wflash` or write eFuse from a file unless you know exactly what you are doing.
> - Double-check the MAC address before writing. A typo also consumes a block.

### 1. Install build tools

```bash
sudo apt install build-essential linux-headers-$(uname -r) mokutil
```

### 2. Download and build the ASIX driver and tools

1. Download **"Linux kernel up to 6.14.x Driver"** from the [ASIX AX88179B product page](https://www.asix.com.tw/en/product/USBEthernet/Super-Speed_USB_Ethernet/AX88179B) (Support → Driver). Version 4.2.0 was used for testing; despite its title it built on kernel 7.0.
2. Extract and build. The archive name may differ:

    ```bash
    tar -xf ASIX_USB_NIC_Linux_Driver_Source_v4.2.0.tar.bz2
    cd ASIX_USB_NIC_Linux_Driver_Source_v4.2.0
    make
    ```

    This builds the kernel module `ax_usb_nic.ko` and the eFuse tool `ax88179b_179a_772e_772d_programmer`. You do not need `make install`: the driver is only needed while changing the MAC.

### 3. Sign the driver (only if Secure Boot is enabled)

```bash
mokutil --sb-state
```

If the output is `SecureBoot enabled`, the kernel rejects unsigned modules with `Key was rejected by service`. Instead of disabling Secure Boot, sign the module with your own Machine Owner Key (MOK). The commands below use Ubuntu's `update-secureboot-policy`; on other distributions, create a MOK with `openssl` and import it with `mokutil`.

1. Create a key and request enrollment. `mokutil` asks for a one-time password that you will need after rebooting:

    ```bash
    sudo update-secureboot-policy --new-key
    sudo mokutil --import /var/lib/shim-signed/mok/MOK.der
    ```

    If `update-secureboot-policy --new-key` reports that a key already exists, reuse it.

2. Reboot. In the blue **MOK Management** screen, choose **Enroll MOK → Continue → Yes**, enter the password, then **Reboot**.
3. Confirm the key is enrolled:

    ```bash
    mokutil --test-key /var/lib/shim-signed/mok/MOK.der
    # Expected: ... is already enrolled
    ```

4. Sign the module (from the driver directory):

    ```bash
    sudo /usr/src/linux-headers-$(uname -r)/scripts/sign-file sha256 \
      /var/lib/shim-signed/mok/MOK.priv \
      /var/lib/shim-signed/mok/MOK.der \
      ax_usb_nic.ko
    modinfo ax_usb_nic.ko | grep signer
    ```

The enrolled key lets the kernel trust modules you sign. Keep `MOK.priv` private.

### 4. Load the driver

```bash
sudo modprobe mii
sudo insmod ./ax_usb_nic.ko
lsusb -t
```

`lsusb -t` should show the adapter with `Driver=ax_usb_nic`. If it still shows `cdc_ncm`, unplug and replug the adapter. Loading the driver may briefly interrupt this adapter's network connection.

### 5. Read the current MAC and back up eFuse (read-only)

```bash
sudo ./ax88179b_179a_772e_772d_programmer rmacaddr
sudo ./ax88179b_179a_772e_772d_programmer refuse -f efuse_backup.txt
```

Example output:

```text
enx000ec6123456 MAC address: 00:0E:C6:12:34:56
[INFO] 22 eFuse blocks are still available.
```

The backup is a record of the original content; it **cannot** be used to restore eFuse. If the tool reports `No eFuse blocks are available`, stop: the MAC cannot be changed.

### 6. Write the new MAC

Replace the address with yours. Use colons as separators:

```bash
sudo ./ax88179b_179a_772e_772d_programmer wefuse -m 02:00:00:AB:CD:EF -p AX88179B
```

For an AX88179A, use `-p AX88179A`. Expected output:

```text
[INFO] 21 eFuse blocks are still available.
SUCCESS
```

### 7. Replug and verify

The new MAC is loaded when the adapter initializes. **Unplug the adapter, wait about 5 seconds and plug it back in**, then check:

```bash
sudo ./ax88179b_179a_772e_772d_programmer rmacaddr
ip -br link
```

The interface name also follows the MAC (for example `enx020000abcdef`).

### 8. Clean up

```bash
sudo rmmod ax_usb_nic
```

Replug the adapter to return it to the in-box driver. The new MAC is stored on the adapter, so you do not need to keep the ASIX driver loaded. In testing, the new MAC was confirmed with the ASIX driver on Linux and with ASIX's Windows driver on another computer.

## Choosing a MAC address

- The first byte must be even (the lowest bit is 0). An odd first byte is a multicast address and will not work.
- For a made-up address, set the second hex digit to `2`, `6`, `A` or `E` (a "locally administered" address, for example `02:xx:xx:xx:xx:xx`), so that it cannot collide with a vendor-assigned address.
- If you copy the MAC of another network card, never connect both to the network at the same time. Duplicate MACs on the same network break DHCP and switching, even when both cards are in the same computer.

## Troubleshooting

| Symptom | Cause | Solution |
|---|---|---|
| `USBError: [Errno 32] Pipe error` in `flash.py` | The adapter is an AX88179B/AX88179A, which rejects the original EEPROM commands. | Use the [ASIX official tool](#ax88179b--ax88179a-asix-official-tool-efuse). |
| `USBError(13, 'Access denied (insufficient permissions)')` | Linux requires root to access the USB device. | Run with sudo, using your virtual environment's Python if needed. |
| `Unsupported device: AX88179A/AX88179B (bcdDevice=0x0200)` | `flash.py` detected a chip it does not support. Nothing was written. | Use the [ASIX official tool](#ax88179b--ax88179a-asix-official-tool-efuse). |
| `insmod: ... Key was rejected by service` | Secure Boot rejects unsigned kernel modules. | [Sign the driver](#3-sign-the-driver-only-if-secure-boot-is-enabled). |
| `No AX88179B_179A_772E_772D found` | `ax_usb_nic` is not loaded, or the adapter is still bound to `cdc_ncm`. | Load the driver, then replug the adapter and check `lsusb -t`. |
| MAC unchanged right after `wefuse` | The chip reads the MAC only when it initializes. | Unplug and replug the adapter. |
| The new MAC is shown, but there is no IP address | A duplicate MAC on the network, or network access control such as IEEE 802.1X. | Make sure no other device uses the same MAC. 802.1X authenticates the device with credentials or certificates, so copying a MAC does not pass it; configure 802.1X or contact your network administrator. |

### Optional: allow a single programmer command without a password

If an automation tool must run the programmer, grant only fixed commands with `sudo visudo -f /etc/sudoers.d/asixflash` instead of full root access. Install the programmer in a root-owned directory first, and escape colons as `\:`:

```sudoers
youruser ALL=(root) NOPASSWD: /usr/local/libexec/asixflash/programmer rmacaddr
youruser ALL=(root) NOPASSWD: /usr/local/libexec/asixflash/programmer wefuse -m 02\:00\:00\:AB\:CD\:EF -p AX88179B
```

Validate with `sudo visudo -cf /etc/sudoers.d/asixflash` and remove the file when done.

## How it works

A network adapter has two copies of its MAC address:

| Location | Purpose | Persistent |
|---|---|---|
| Non-volatile storage (EEPROM or eFuse) | Default MAC loaded when the adapter starts | Yes, survives power loss and moving to another computer |
| Working register | MAC the adapter currently uses | No, reloaded at reset |

Changing the MAC in the operating system only changes the working register. These tools change the non-volatile storage.

- **Original AX88179 (`flash.py`)**: uses ASIX vendor USB control requests to enable EEPROM writes (`0x07`), write the 6 MAC bytes as three 16-bit words at offset 0 (`0x04`), disable writes (`0x08`) and reload the configuration (`0x06`).
- **AX88179B**: the configuration is stored in 32 eFuse blocks of 20 bytes. The ASIX tool reads the existing MAC record, builds a new record with the new address and checksum, and programs it into the next empty block through the `ax_usb_nic` driver. The chip uses the latest valid record. In testing, changing the MAC consumed one block.

## Credits and license

- Original tool and EEPROM protocol research: [jglim/ASIXFlash](https://github.com/jglim/ASIXFlash) and [Adding new, undocumented features into a kernel driver](https://jg.sn.sg/ax88179/).
- AX88179B discussion: [jglim/ASIXFlash#3](https://github.com/jglim/ASIXFlash/issues/3).
- AX88179B driver and eFuse tool: [ASIX Electronics](https://www.asix.com.tw/en/product/USBEthernet/Super-Speed_USB_Ethernet/AX88179B); a mirror is available at [enlyze/ax-usb-nic](https://github.com/enlyze/ax-usb-nic).

This project is licensed under the MIT License. The ASIX driver and tools are licensed under GPL-2.0 and are **not** included in this repository; download them from ASIX.

Use at your own risk. Changing the MAC address of a device may be subject to your network's policies.
