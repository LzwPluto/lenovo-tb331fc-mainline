# 小新 Pad 2024 (TB331FC / SM6225) 主线 Linux WiFi (WCN3990) 适配与打通技术总结

> **状态**：✅ **完全打通（已验证扫描、WPA2/3握手、DHCP获取IP、外网Ping、DNS解析、APK包管理）**  
> **内核版本**：`6.14.0-rc5-next-20250306` (arm64)  
> **网卡芯片**：高通 `WCN3990`（内置于 SoC 射频配套架构）  
> **驱动模块**：`ath10k_snoc` + `ath10k_core`  
> **底层通信**：Qualcomm IPC Router (`QRTR`) + `GLINK` + `SMD`  

---

## 一、高通 WCN3990 主线 WiFi 架构真相

在骁龙 685 (SM6225 / Khaje / Bengal 系列) 上，主线 Linux 的 WCN3990 并非由内核驱动直接操作物理寄存器唤醒，而是依赖一套复杂的**多协处理器与总线协同系统**：

```
[Linux Kernel]                    [IPC Bus]                  [Remote Processors / Daemons]
+-------------------+             +------------+             +-------------------------------+
| ath10k_snoc.ko    | <---QMI---> |            | <---QRTR--> | Modem (remoteproc0 / MPSS)    |
| (QMI Client 0x45) |             |            |             |   - 运行 wlan_pd 保护域        |
+-------------------+             |            |             +-------------------------------+
                                  |    QRTR    |             | rmtfs (-r -P -s)              |
+-------------------+             |  IPCRTR    | <---QMI---> |   - 挂载 modemst1,2 / fsg     |
| qcom_smd_qrtr.ko  | <==GLINK==> | (af_qrtr)  |             +-------------------------------+
+-------------------+             |            |             | tqftpserv (-d)                |
                                  |            | <---TFTP--> |   - 传输 wlanmdsp.mbn 固件    |
+-------------------+             |            |             +-------------------------------+
| User Tools        |             |            |             | pd-mapper                     |
| iw / wpa_supp     |             |            | <---QMI---> |   - 解析 modemuw.jsn 映射     |
+-------------------+             +------------+             +-------------------------------+
```

---

## 二、攻克的四大核心技术卡点与根因剖析

### 1. 结构体内存对齐与空指针崩溃（Offset Misalignment）
* **现象**：加载外部编译的 `ath10k_snoc.ko` 时，内核在 `ath10k_ce_alloc_pipe` 处发生段错误空指针崩溃。
* **根因**：当前运行内核编译时 `# CONFIG_ATH10K_DEBUGFS is not set`，而编译外部模块的 WSL `.config` 开启了 `CONFIG_ATH10K_DEBUGFS=y`。这导致 `struct ath10k` 中的调试字段改变了结构体大小，造成 `ar->ce_priv` 偏移错位 8 字节，引发指针解引用崩溃。
* **解决**：提取实机 `/proc/config.gz` 对齐 WSL 源码配置，重新运行 `make modules_prepare`，编译出严格匹配的 `ath10k_snoc.ko`。

### 2. Modem 硬件看门狗崩溃（Watchdog Timeout）
* **现象**：Modem (`remoteproc0`) 每次启动运行约 40 秒后，必报硬件看门狗硬崩溃：
  ```text
  qcom_q6v5_pas 6080000.remoteproc: fatal error received: dog_hal_common.c:173:DOG detects stalled initialization
  remoteproc remoteproc0: crash detected in modem: type fatal error
  ```
* **根因**：
  1. 开机时 `qrtr-smd` 模块未加载，导致 Modem 的通信通道 `6080000.remoteproc:glink-edge.IPCRTR` 无驱动绑定，QRTR 处于孤岛状态。
  2. Modem 启动初期在等待用户态 `rmtfs` 响应 NVRAM 分区（`modemst1`、`modemst2`、`fsg`）。由于总线不通，Modem 握手超时被内部看门狗强行复位。
* **解决**：
  1. 将 `qrtr-smd` 加入 `/etc/modules`，确保开机第一时刻总线可用。
  2. 启动静态编译的 `/usr/bin/rmtfs -r -P -s`，对接物理分区 `/dev/disk/by-partlabel/`。Modem 握手成功后，连续运行超过 30 分钟零崩溃。

### 3. 最关键的隐形盲区：保护域映射缺失（`pd-mapper` 与 `modemuw.jsn`）
* **现象**：Modem 稳定运行后，`ath10k_snoc` 依然静默卡在等待 `WLFW (service=0x45)`，总线上迟迟不出服务。内核打印：
  ```text
  PDM: no support for the platform, userspace daemon might be required.
  ```
* **根因**：
  在原厂固件中，WLAN 固件运行在 Modem 的保护域（Protection Domain）`wlan_pd` 内。
  Modem 启动时会通过 QRTR 询问服务定位器（Service Registry / 0x42 号服务），寻找 `wlan_pd` 的实例 ID。没有 `pd-mapper` 守护进程提供解答，Modem 根本不会启动 `wlan_pd`，也不会请求 `wlanmdsp.mbn`，更不会向主机宣告 `WLFW` 服务！
* **解决**：
  1. 交叉编译静态 `pd-mapper` 放入 `/usr/bin/pd-mapper`。
  2. 提取原厂全部 6 个 `.jsn` 配置文件（特别是包含 `"subdomain": "wlan_pd", "service": "wlan/fw"` 的 `modemuw.jsn`），放置到 `/lib/firmware/qcom/sm6225/LENOVO/TB128FU/`。
  3. `pd-mapper` 启动后，Modem 成功收到响应，立即拉起 `wlan_pd`，并于 `tqftpserv` 加载 `wlanmdsp.mbn`，最终在 QRTR 宣告 `service=0x45 (WLFW)`！

### 4. 精简系统缺失无线连接工具链
* **现象**：`wlan0` 网卡生成后，执行 `iw` 报错 `command not found`。
* **解决**：
  下载 Alpine 官方 AArch64 原生包，部署完整工具链：
  * `/usr/sbin/iw`（依赖 `libnl3` 系列）
  * `/sbin/wpa_supplicant` 与 `/sbin/wpa_cli`
  * `/etc/wpa_supplicant/wpa_supplicant.conf`

---

## 三、部署资产与文件路径清单

### 1. 固件资产
| 资产文件 | 板端目标路径 | 作用 |
|---|---|---|
| `wlanmdsp.mbn` | `/lib/firmware/wlanmdsp.mbn`<br>`/lib/firmware/qcom/sm6225/LENOVO/TB128FU/wlanmdsp.mbn` | WLAN 协处理器固件二进制 |
| `firmware-5.bin` | `/lib/firmware/ath10k/WCN3990/hw1.0/` | WCN3990 容器固件（60字节） |
| `board-2.bin` | `/lib/firmware/ath10k/WCN3990/hw1.0/lenovo-tb128fu/` | 34个频段校准配置打包镜像 |
| `modem.mdt` + `modem.b00~b23` | `/lib/firmware/qcom/sm6225/LENOVO/TB128FU/` | Modem 主固件（含 symlink `modem.mbn -> modem.mdt`） |
| `modemuw.jsn` 等 6 个 `.jsn` | `/lib/firmware/qcom/sm6225/LENOVO/TB128FU/`<br>`/lib/firmware/` | 保护域描述表，指导拉起 `wlan_pd` |

### 2. 守护进程与系统工具
| 二进制工具 | 路径 | 来源/编译方式 |
|---|---|---|
| `rmtfs` | `/usr/bin/rmtfs` | `https://github.com/andersson/rmtfs`（静态编译） |
| `tqftpserv` | `/usr/bin/tqftpserv` | `https://github.com/andersson/tqftpserv`（静态编译） |
| `pd-mapper` | `/usr/bin/pd-mapper` | `https://github.com/andersson/pd-mapper`（静态编译，去 lzma 依赖） |
| `qrtr-lookup` | `/usr/bin/qrtr-lookup` | `https://github.com/andersson/qrtr`（静态编译） |
| `wpa_supplicant` | `/sbin/wpa_supplicant` | Alpine 官方原生包 |
| `iw` | `/usr/sbin/iw` | Alpine 官方原生包 |

---

## 四、开机自动启动脚本与配置

### 1. 启动服务配置 `/etc/local.d/qualcomm.start`
```sh
#!/bin/sh
# 1. 确保目录与底层总线
mkdir -p /tmp /var/log /var/run/wpa_supplicant
modprobe qrtr-smd 2>/dev/null
sleep 0.5

# 2. 启动三大核心守护进程
/usr/bin/rmtfs -r -P -s > /tmp/rmtfs.log 2>&1 &
/usr/bin/tqftpserv -d > /tmp/tqftp.log 2>&1 &
/usr/bin/pd-mapper > /tmp/pd-mapper.log 2>&1 &
sleep 1

# 3. 确保 Modem 和 ADSP 启动
echo start > /sys/class/remoteproc/remoteproc0/state 2>/dev/null
echo start > /sys/class/remoteproc/remoteproc1/state 2>/dev/null
sleep 1

# 4. 加载 WiFi 主驱动
modprobe ath10k_snoc 2>/dev/null

# 5. 自动连接预设热点
(
    sleep 5
    if ip link show wlan0 >/dev/null 2>&1; then
        ip link set wlan0 up
        /sbin/wpa_supplicant -B -i wlan0 -c /etc/wpa_supplicant/wpa_supplicant.conf
        sleep 4
        /sbin/udhcpc -i wlan0 -b
    fi
) &
```

### 2. 热点配置 `/etc/wpa_supplicant/wpa_supplicant.conf`
```text
ctrl_interface=/var/run/wpa_supplicant
update_config=1

network={
    ssid="lzw"
    psk="lzw2007131"
    key_mgmt=WPA-PSK
}
```

---

## 五、实机实测验证数据

### 1. 扫描验证（周边 AP 全部识别）
```text
BSS 92:6d:0b:c6:30:2e(on wlan0) -- associated
    SSID: lzw
BSS f0:9b:b8:32:14:40(on wlan0)
    SSID: stu-xdwlan
BSS 50:4f:3b:ca:52:92(on wlan0)
    SSID: Xiaomi
```

### 2. DHCP IP 获取
```text
3: wlan0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue state UP
    inet 10.118.183.161/24 brd 10.118.183.255 scope global wlan0
```

### 3. 外网通信与 DNS 实测
* **Ping 公共 DNS (`223.5.5.5`)**：3 报文全收，延时 58~63ms，0% 丢包。
* **Ping 百度域名 (`baidu.com`)**：3 报文全收，DNS 瞬时解析，0% 丢包。
* **`apk update` 在线更新**：成功拉取清华镜像源 `28570 distinct packages available`。
