# 明天开工：混合 DTB（给主线树补 __symbols__）

## 一句话背景

TB331FC 的 ABL 必须把厂商 dtbo overlay 应用到基础 DTB 上；overlay 通过 __fixups__ 按标签名
引用节点，libufdt 靠基础 DTB 的 __symbols__ 解析。**纯主线 DTB 没有这些符号 → ABL 拒启。**
（附录 H 有决定性实验：原厂 DTB 只删 __symbols__ 就被拒。）

解法：给主线 DTB 补一批"无害占位节点"，让 overlay 能应用成功。

## 已确认的事实

- dtbo 最小必需集合 = 条目 {0, 2}
- 被接受的基础 DTB = "Khaje SoC" 裸树，board-id 0x0，__symbols__ 829 个
- overlay #0 需要 85 个厂商符号；#2 类似
- 判定信号：ACCEPT = 进 900E / REJECT = 回 fastboot 或回落 A 槽
- 全原厂四件套 + 无符号 dtbo = REJECT（所以确实必须要真实 overlay）

## 明天的三步

### 第 1 步：导出 overlay 的全部需求（不碰设备）
```
python tools\mkdtbo.py --src "D:\TB331FC_GSI_Kit\08_一键刷机\fw\dtbo.img" --list
```
再写个小脚本，对 entry 0 和 2 导出：
- 全部 __fixups__ 符号名（target = <&symbol> 型）
- 全部 fragment 的 target-path（按路径型）  <-- 重点：看有没有这类
输出到 dump\overlay_needs.txt

### 第 2 步：生成 abl-stubs 子树
在 build\ref_pmic.dts（或原始 ref.dts）里插入：
```
	abl-stubs {
		sde_te_active: sde_te_active { phandle = <0x1001>; };
		...
	};
```
要点：
- 每个符号一个空节点，**显式给唯一的 phandle（0x1001 起）**，避免和现有硬编码 phandle 冲突
- 用 dtc -@ 编译，让 __symbols__ 覆盖全部符号
- 校验：编译后解析 __symbols__，确认需要的符号一个不少

### 第 3 步：刷入测试（最小改动法，已验证好用）
```
# 1) 把生成的主线 DTB 写进原厂 vendor_boot 的 dtb 段开头（其余字节不动）
python -c "..."    # 见本次会话里的做法：d[0xB19000:0xB19000+len(dtb)] = dtb，截到 0xC57000
# 2) 刷 vendor_boot_b + 原厂 dtbo_b（45 条）+ 原厂 boot/init_boot/vbmeta
fastboot flash vendor_boot_b build\vb_stubs.img
fastboot flash dtbo_b "D:\TB331FC_GSI_Kit\08_一键刷机\fw\dtbo.img"
fastboot --set-active=b ; fastboot reboot
```
判定：900E = 通过（ABL 放行了！），回 fastboot = 还差东西。

## 设备状态（截至收工）
- current-slot: a，运行 HyperOS 2.0，A 槽从未被写入
- slot-retry-count:a=7, b=6，slot-unbootable:b=no
- B 槽当前是原厂镜像（可随时覆盖）

## 安全规程
- 每次测试前 `fastboot --set-active=b`（重置 retry）
- 测完若失败，`fastboot --set-active=a` 让设备回到 Android
- 若进 900E：拔 USB → 长按电源 30-40 秒 → 按住音量下插 USB

## 现成工具
tools\mkdtbo.py       dtbo 容器挑选/重建（已验证）
tools\mkv4.py         v4 三分区打包（段顺序已修正）
tools\fdt_tree.py     FDT 根结构对比
tools\hdr_diff.py     与原厂逐字段 diff
tools\ablcheck.py     刷前离线校验
tools\scanlog.py      分区内容扫描
