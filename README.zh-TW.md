# ASIXFlash

[English](README.md) | [繁體中文](README.zh-TW.md)

_修改 ASIX AX88179 系列 USB 網卡的永久 MAC 位址。修改內容存放在網卡本身，換到其他電腦也會繼續生效。_

![Changed MAC](https://raw.github.com/jglim/ASIXFlash/master/etc/mac-change.png)

> **你的網卡是哪一種晶片？** 使用**原版 AX88179** 的網卡把 MAC 存在 EEPROM，可以用 `flash.py` 修改。較新的 **AX88179B**（以及 AX88179A）雖然 USB ID 相同（`0b95:1790`），但 MAC 存在 **eFuse**，`flash.py` 不支援。請先[分辨晶片版本](#分辨晶片版本)。

## 目錄

- [分辨晶片版本](#分辨晶片版本)
- [原版 AX88179：使用 flash.py（EEPROM）](#原版-ax88179使用-flashpyeeprom)
- [AX88179B / AX88179A：使用 ASIX 官方工具（eFuse）](#ax88179b--ax88179a使用-asix-官方工具efuse)
- [如何選擇 MAC 位址](#如何選擇-mac-位址)
- [疑難排解](#疑難排解)
- [運作原理](#運作原理)
- [致謝與授權](#致謝與授權)

## 分辨晶片版本

兩種晶片的 USB ID 都是 `0b95:1790`，只看 `lsusb` 無法分辨。請檢查產品名稱與 `bcdDevice`（裝置版本）：

```bash
lsusb -d 0b95:1790
lsusb -v -d 0b95:1790 2>/dev/null | grep -E 'bcdDevice|iProduct'
```

| 輸出 | 晶片 | 儲存方式 | 使用工具 |
|---|---|---|---|
| `bcdDevice 1.00` | 原版 AX88179 | EEPROM（可重複寫入） | [`flash.py`](#原版-ax88179使用-flashpyeeprom) |
| `bcdDevice 2.00`，`iProduct ... AX88179B` | AX88179B | eFuse（只能追加） | [ASIX 官方工具](#ax88179b--ax88179a使用-asix-官方工具efuse) |
| `bcdDevice 2.00`，`iProduct ... AX88179A` | AX88179A | eFuse（只能追加） | [ASIX 官方工具](#ax88179b--ax88179a使用-asix-官方工具efuse) |

其他代表你的網卡是 AX88179B 的跡象：

- 在 Linux 上，`lsusb -t` 顯示網卡使用 `cdc_ncm` 驅動（AX88179B 支援免驅動的 CDC-NCM 模式）。
- 執行 `flash.py` 讀取 MAC 時出現 `USBError: [Errno 32] Pipe error`。
- 在 Windows 上，`flash.py` 產生的備份檔內容全是 `FF`（參見 [jglim/ASIXFlash#3](https://github.com/jglim/ASIXFlash/issues/3)）。

`flash.py` 會檢查 `bcdDevice`，遇到 AX88179A/AX88179B 時，會在讀寫任何資料之前停止。

## 原版 AX88179：使用 flash.py（EEPROM）

需要 **Python 3.6+**、**pyusb** 套件，以及 **libusb 0.1** / **libusb 1.0** / **OpenUSB** 其中一種。

### 安裝需求

- 安裝 libusb：
    - Linux：`sudo apt-get install libusb-1.0-0-dev`
    - macOS：透過 MacPorts，`sudo port install libusb`
    - Windows：沒有明確的安裝流程，不過[這個 libusb-0.1 安裝程式應該可以使用](https://sourceforge.net/projects/libusb-win32/files/libusb-win32-releases/1.2.6.0/libusb-win32-devel-filter-1.2.6.0.exe/download)
- Python 3.6+ 與 `pyusb`：`pip install -r ASIXFlash/requirements.txt`
- （僅限 Windows）將 AX88179 的驅動換成 libusb：
    - 執行 Zadig `zadig-2.4.exe`
    - 選擇 Options -> List all devices（✓）
    - 在下拉選單中選擇你的 AX88179 裝置
    - 按上下箭頭，直到出現 `libusb-win32`
    - 按下大按鈕，通常是 `Replace Driver`

![Zadig Guide](https://raw.github.com/jglim/ASIXFlash/master/etc/zadig.gif)

### 操作步驟

1. 下載並解壓縮這個 repository。
2. 開啟 `ASIXFlash/flash.py`，把 `NEW_MAC_ADDRESS = "1BADCAFEBABE"` 改成你要的 MAC 位址（12 個十六進位字元，不含分隔符號）。程式不會檢查內容，請確認完全正確。
3. 執行程式：
    - Windows / macOS：`python flash.py`
    - Linux：存取 USB 通常需要 root 權限。如果使用虛擬環境，請用 sudo 執行虛擬環境裡的 Python，例如 `sudo ../venv/bin/python flash.py`。直接用 `sudo python3` 會改用系統的 Python，可能找不到 `pyusb`。
4. 程式會顯示原本的 MAC，把 EEPROM 備份成 `ax88179.bin`，寫入新的 MAC，再顯示結果。請保留 `ax88179.bin`，這是原始的 EEPROM 內容。

![Demo](https://raw.github.com/jglim/ASIXFlash/master/etc/cmd.png)

瀏覽器版本 [`WebUSB/index.html`](WebUSB/index.html) 使用相同的 EEPROM 協定，同樣只支援原版 AX88179。

## AX88179B / AX88179A：使用 ASIX 官方工具（eFuse）

AX88179B 的 MAC 存在 **eFuse**（只能燒錄一次的記憶體），而不是 EEPROM。ASIX 在驅動原始碼中附有 Linux 燒錄工具。以下步驟已在 Ubuntu（kernel 7.0，Secure Boot 開啟）搭配 AX88179B 網卡測試成功。

> [!WARNING]
> **eFuse 寫入無法復原。** 已燒錄的位元無法清除。修改 MAC 不會覆蓋舊資料，而是在空白的 eFuse 區塊**新增**一筆紀錄，晶片會採用最新的有效紀錄。每次修改都會永久用掉一個區塊，區塊用完後就再也無法修改 MAC。
>
> - 只使用下方的 MAC 專用命令（`wefuse -m ... -p ...`）。
> - 除非你非常清楚後果，**不要**使用 `wflash`，也不要從檔案寫入 eFuse。
> - 寫入前再三確認 MAC 位址。打錯字一樣會用掉一個區塊。

### 1. 安裝編譯工具

```bash
sudo apt install build-essential linux-headers-$(uname -r) mokutil
```

### 2. 下載並編譯 ASIX 驅動與工具

1. 從 [ASIX AX88179B 產品頁面](https://www.asix.com.tw/en/product/USBEthernet/Super-Speed_USB_Ethernet/AX88179B)（Support → Driver）下載 **「Linux kernel up to 6.14.x Driver」**。測試時使用 4.2.0 版；雖然標題寫到 6.14，在 kernel 7.0 上也能編譯。
2. 解壓縮並編譯（壓縮檔名稱可能不同）：

    ```bash
    tar -xf ASIX_USB_NIC_Linux_Driver_Source_v4.2.0.tar.bz2
    cd ASIX_USB_NIC_Linux_Driver_Source_v4.2.0
    make
    ```

    完成後會產生驅動模組 `ax_usb_nic.ko` 與 eFuse 工具 `ax88179b_179a_772e_772d_programmer`。不需要執行 `make install`，驅動只在修改 MAC 時使用。

### 3. 簽署驅動（僅限 Secure Boot 開啟時）

```bash
mokutil --sb-state
```

如果顯示 `SecureBoot enabled`，核心會拒絕載入未簽章的模組，並出現 `Key was rejected by service`。不需要關閉 Secure Boot，改用自己的 Machine Owner Key（MOK）簽署模組即可。以下命令使用 Ubuntu 的 `update-secureboot-policy`；其他發行版可以用 `openssl` 建立 MOK，再用 `mokutil` 匯入。

1. 建立金鑰並申請註冊。`mokutil` 會要求設定一次性密碼，重新開機後要用：

    ```bash
    sudo update-secureboot-policy --new-key
    sudo mokutil --import /var/lib/shim-signed/mok/MOK.der
    ```

    如果 `update-secureboot-policy --new-key` 表示金鑰已存在，直接使用現有金鑰即可。

2. 重新開機。在藍色的 **MOK Management** 畫面中，選擇 **Enroll MOK → Continue → Yes**，輸入剛才設定的密碼，再選 **Reboot**。
3. 確認金鑰已註冊：

    ```bash
    mokutil --test-key /var/lib/shim-signed/mok/MOK.der
    # 應顯示：... is already enrolled
    ```

4. 簽署模組（在驅動目錄中執行）：

    ```bash
    sudo /usr/src/linux-headers-$(uname -r)/scripts/sign-file sha256 \
      /var/lib/shim-signed/mok/MOK.priv \
      /var/lib/shim-signed/mok/MOK.der \
      ax_usb_nic.ko
    modinfo ax_usb_nic.ko | grep signer
    ```

註冊後，核心會信任所有用這把金鑰簽署的模組。請妥善保管 `MOK.priv`，不要外流。

### 4. 載入驅動

```bash
sudo modprobe mii
sudo insmod ./ax_usb_nic.ko
lsusb -t
```

`lsusb -t` 應顯示網卡使用 `Driver=ax_usb_nic`。如果仍是 `cdc_ncm`，請拔掉網卡再重新插上。載入驅動時，這張網卡的連線可能會短暫中斷。

### 5. 讀取目前的 MAC 並備份 eFuse（唯讀）

```bash
sudo ./ax88179b_179a_772e_772d_programmer rmacaddr
sudo ./ax88179b_179a_772e_772d_programmer refuse -f efuse_backup.txt
```

輸出範例：

```text
enx000ec6123456 MAC address: 00:0E:C6:12:34:56
[INFO] 22 eFuse blocks are still available.
```

備份只是原始內容的紀錄，**無法**用來還原 eFuse。如果工具顯示 `No eFuse blocks are available`，請停止操作，這張網卡已無法再修改 MAC。

### 6. 寫入新的 MAC

把位址換成你的 MAC，並以冒號分隔：

```bash
sudo ./ax88179b_179a_772e_772d_programmer wefuse -m 02:00:00:AB:CD:EF -p AX88179B
```

AX88179A 請改用 `-p AX88179A`。預期輸出：

```text
[INFO] 21 eFuse blocks are still available.
SUCCESS
```

### 7. 重新插拔並驗證

新的 MAC 會在網卡初始化時載入。**拔掉網卡，等待約 5 秒再插回去**，然後檢查：

```bash
sudo ./ax88179b_179a_772e_772d_programmer rmacaddr
ip -br link
```

網路介面名稱也會跟著 MAC 改變（例如 `enx020000abcdef`）。

### 8. 收尾

```bash
sudo rmmod ax_usb_nic
```

重新插拔網卡，就會改回系統內建的驅動。新的 MAC 存在網卡上，不需要一直載入 ASIX 驅動。測試時，已在 Linux 上用 ASIX 驅動，以及在另一台電腦上用 ASIX 的 Windows 驅動確認新的 MAC。

## 如何選擇 MAC 位址

- 第一個位元組必須是偶數（最低位元為 0）。第一個位元組為奇數時是多播（multicast）位址，無法使用。
- 如果是自訂的位址，請把第二個十六進位字元設為 `2`、`6`、`A` 或 `E`（「本地管理」位址，例如 `02:xx:xx:xx:xx:xx`），避免和廠商分配的位址衝突。
- 如果複製其他網卡的 MAC，絕對不要讓兩張網卡同時連上網路。同一個網路中出現重複的 MAC 會導致 DHCP 和交換器運作異常，即使兩張網卡在同一台電腦上也一樣。

## 疑難排解

| 症狀 | 原因 | 解決方法 |
|---|---|---|
| `flash.py` 出現 `USBError: [Errno 32] Pipe error` | 網卡是 AX88179B/AX88179A，不接受原版的 EEPROM 指令。 | 改用 [ASIX 官方工具](#ax88179b--ax88179a使用-asix-官方工具efuse)。 |
| `USBError(13, 'Access denied (insufficient permissions)')` | Linux 存取 USB 裝置需要 root 權限。 | 用 sudo 執行；有需要時使用虛擬環境裡的 Python。 |
| `Unsupported device: AX88179A/AX88179B (bcdDevice=0x0200)` | `flash.py` 偵測到不支援的晶片，沒有寫入任何資料。 | 改用 [ASIX 官方工具](#ax88179b--ax88179a使用-asix-官方工具efuse)。 |
| `insmod: ... Key was rejected by service` | Secure Boot 拒絕載入未簽章的核心模組。 | [簽署驅動](#3-簽署驅動僅限-secure-boot-開啟時)。 |
| `No AX88179B_179A_772E_772D found` | 尚未載入 `ax_usb_nic`，或網卡仍使用 `cdc_ncm`。 | 載入驅動後重新插拔網卡，再用 `lsusb -t` 確認。 |
| 執行 `wefuse` 後 MAC 沒變 | 晶片只在初始化時讀取 MAC。 | 拔掉網卡再重新插上。 |
| 顯示新的 MAC，但拿不到 IP | 網路上有重複的 MAC，或網路使用 IEEE 802.1X 等存取控制。 | 確認沒有其他裝置使用相同的 MAC。802.1X 是用帳號或憑證驗證裝置，複製 MAC 無法通過；請設定 802.1X 或聯絡網路管理員。 |

### 選用：只允許特定燒錄命令免密碼執行

如果需要讓自動化工具執行燒錄工具，請用 `sudo visudo -f /etc/sudoers.d/asixflash` 只授權固定的命令，而不是開放完整的 root 權限。請先把工具安裝到 root 擁有的目錄；sudoers 中的冒號要寫成 `\:`：

```sudoers
youruser ALL=(root) NOPASSWD: /usr/local/libexec/asixflash/programmer rmacaddr
youruser ALL=(root) NOPASSWD: /usr/local/libexec/asixflash/programmer wefuse -m 02\:00\:00\:AB\:CD\:EF -p AX88179B
```

用 `sudo visudo -cf /etc/sudoers.d/asixflash` 檢查語法，完成後請刪除這個檔案。

## 運作原理

網卡的 MAC 位址有兩份：

| 位置 | 用途 | 是否永久 |
|---|---|---|
| 非揮發性記憶體（EEPROM 或 eFuse） | 網卡啟動時載入的預設 MAC | 是，斷電或換電腦後仍保留 |
| 工作暫存器 | 網卡目前實際使用的 MAC | 否，重設後重新載入 |

在作業系統中修改 MAC，只會改到工作暫存器；這些工具修改的是非揮發性記憶體。

- **原版 AX88179（`flash.py`）**：透過 ASIX 自訂的 USB 控制指令，開啟 EEPROM 寫入（`0x07`），把 6 個位元組的 MAC 分成三個 16 位元 word 寫入位址 0（`0x04`），關閉寫入（`0x08`），再重新載入設定（`0x06`）。
- **AX88179B**：設定存放在 32 個 20 位元組的 eFuse 區塊中。ASIX 工具會讀取現有的 MAC 紀錄，產生一筆包含新位址與校驗碼的紀錄，再透過 `ax_usb_nic` 驅動寫入下一個空白區塊。晶片會採用最新的有效紀錄。測試時，修改一次 MAC 用掉一個區塊。

## 致謝與授權

- 原始工具與 EEPROM 協定研究：[jglim/ASIXFlash](https://github.com/jglim/ASIXFlash) 及 [Adding new, undocumented features into a kernel driver](https://jg.sn.sg/ax88179/)。
- AX88179B 相關討論：[jglim/ASIXFlash#3](https://github.com/jglim/ASIXFlash/issues/3)。
- AX88179B 驅動與 eFuse 工具：[ASIX Electronics](https://www.asix.com.tw/en/product/USBEthernet/Super-Speed_USB_Ethernet/AX88179B)；鏡像可參考 [enlyze/ax-usb-nic](https://github.com/enlyze/ax-usb-nic)。

本專案採用 MIT 授權。ASIX 驅動與工具採用 GPL-2.0 授權，**沒有**包含在本 repository 中，請從 ASIX 官方網站下載。

使用風險請自行承擔。修改裝置的 MAC 位址可能受到所在網路的使用政策限制。
