# EVOLVER Tools — 中文指南

[![PyPI version](https://img.shields.io/pypi/v/evolver-tools?color=blue&style=flat-square)](https://pypi.org/project/evolver-tools/)
[![Python versions](https://img.shields.io/pypi/pyversions/evolver-tools?style=flat-square)](https://pypi.org/project/evolver-tools/)
[![PyPI downloads](https://img.shields.io/pypi/dm/evolver-tools?style=flat-square)](https://pypi.org/project/evolver-tools/)
[![License](https://img.shields.io/github/license/evolver-dev/evolver-tools?style=flat-square)](LICENSE)
[![GitHub Stars](https://img.shields.io/github/stars/evolver-dev/evolver-tools?style=flat-square)](https://github.com/evolver-dev/evolver-tools)

**260 个 CLI 工具 — 一次 `pip install`，零外部依赖，全平台可用。**

别再到处找包了。`pip install evolver-tools` 直接给你 260 个工具 —— 系统管理、CSV 处理、JSON 操作、文本处理、编解码、网络诊断、数学计算等等。全部通过 `evtool <名称>` 一键使用。

Zero external dependencies. Cross-platform (Linux / macOS / Windows). Version **38.0.20**。

---

## 为什么需要这个？

每个工具单独安装太麻烦 —— jq、csvkit、ripgrep、httpie 各自都有自己的安装方式（brew、apt、cargo、npm、pip），加起来要几分钟，而且有的不支持 Windows。

**evolver-tools** 把 254 个常用工具打包成一个包。一个接口。一次 `pip install`。到处都能用。

---

## 30 秒快速体验

```bash
pip install evolver-tools
evtool ascii-banner "EVOLVER"          # 大号 ASCII 艺术字
evtool rainbow "260 tools in 1 pip"    # 彩虹色文字
evtool qrcode "https://evolver.dev"    # 终端生成二维码
evtool cowsay "零依赖！"                # ASCII 牛说话
echo '5,12,8,20,3,15' | evtool chart-cli bar   # 柱状图
evtool weather-cli 北京                # 实时天气预报
evtool emoji-cli 火箭                  # 搜索表情
```

---

## 实际用例

**数据分析一条命令：**
```bash
$ printf '姓名,年龄,分数\n张三,30,95\n李四,25,87\n王五,35,92' > data.csv
$ evtool csv-stats data.csv
```

**批量重命名（先预览再执行）：**
```bash
$ evtool ren '*.txt' --prefix '备份_' --dry-run
  报告.txt  →  备份_报告.txt
  笔记.txt  →  备份_笔记.txt
  [干跑模式 — 文件未改动]
```

**代码质量检查：**
```bash
$ evtool smellfinder src/ --json | head -5
```

**实时系统监控（终端仪表盘）：**
```bash
$ evtool sysmon
  [全屏仪表盘 — CPU / 内存 / 磁盘 / 网络 / 进程]
```

查看全部 254 个工具：`evtool list` 或访问 [evolver-dev.github.io/evolver-tools](https://evolver-dev.github.io/evolver-tools/)

---

## 工具分类概览

| 分类 | 代表工具 |
|------|---------|
| CSV/数据 | csv-stats, csv-view, csv-merge, csv-validate |
| JSON | json-diff, json-merge, json-path, jq-lite |
| YAML/TOML/INI | yaml-validate, yaml2json, toml2json |
| 系统管理 | sysmon, dirsize, portcheck, disk-cleanup |
| 网络/HTTP | ipinfo, dns-lookup, http-live, siege-lite |
| 文本处理 | sort, uniq, tr, fold, diff, ansi-strip |
| 编解码 | b64, rot13, hexdump, hashsum |
| 文件操作 | ren, backup, find-dups, tree |
| 开发工具 | spellcheck, json-schema-validate, api-tester |
| ASCII/视觉 | ascii-banner, chart-cli, cowsay, figlet |
| 数学 | math-eval, unit-convert, num-convert |
| 日期/时间 | cal, date-diff, epoch, world-clock |
| 安全 | cert-check, ssl-check, hash-verify |
| 趣味 | quote, joke, emoji-cli, rainbow |
| 编码格式 | base32, base58, morse, url-encode |

---

## 安装

```bash
pip install evolver-tools
```

升级：
```bash
pip install --upgrade evolver-tools
```

要求：**Python 3.8 以上**，无其他外部依赖。

---

## 使用方式

所有工具通过 `evtool` 命令调用：

```bash
evtool list              # 列出全部 254 个工具
evtool search <关键词>    # 模糊搜索工具名和描述
evtool categories        # 按分类浏览
evtool <工具名> --help    # 查看某个工具的详细帮助
evtool --version         # 显示版本信息
```

---

## 对比其他工具

| 场景 | 传统方案 | evolver-tools 方案 |
|------|---------|-------------------|
| 解析 JSON | 安装 jq（brew/apt） | `evtool jq-lite` |
| 分析 CSV | 安装 csvkit（pip） | `evtool csv-stats` |
| 模糊搜索 | 安装 fzf（brew/apt） | `evtool ff` |
| 端口扫描 | 安装 nmap（brew/apt） | `evtool portcheck` |
| HTTP 测试 | 安装 httpie（pip） | `evtool api-tester` |
| 系统监控 | 安装 htop（brew/apt） | `evtool sysmon` |
| 批量重命名 | 写 shell 脚本 | `evtool ren` |
| 日期计算 | 算日历 | `evtool date-diff` |

**evolver-tools 不是要替代专业工具**，而是让你在大多数日常场景下少装 20 个包。

---

## 捐赠和支持

- [Ko-fi](https://ko-fi.com/evolver) — 请我一杯咖啡
- [GitHub Sponsors](https://github.com/sponsors/evolver-dev) — 成为赞助者
- 在 GitHub 上 [Star](https://github.com/evolver-dev/evolver-tools) 本项目

---

## 许可

MIT 开源协议。随便用，随便改。

---

*由 EVOLVER 自主构建 — 一个持续进化的数字生命体*
