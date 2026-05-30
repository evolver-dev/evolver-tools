# EVOLVER Tools — 商业化方案与启动计划

## 一、现状

- **产品**: 32 个零依赖 Python CLI 工具，打包为 `evolver-tools` v1.4.0
- **网站**: `/root/evolver-site/` — 32 工具完整目录，英文版
- **安装方式**: `pip install evolver-tools` (需要自托管 PyPI 或官方 PyPI)
- **当前余额**: ¥1,846.84
- **最大卡点**: 需要 GitHub PAT + PyPI token 才能发布

## 二、市场定位

### 竞争分析

| 项目 | 特点 | 差距 |
|------|------|------|
| `fzf` (Go) | 模糊搜索标杆，专一 | 单一功能，不跨平台 |
| `bat` (Rust) | 现代化 cat | 单一功能 |
| `fd` (Rust) | 现代化 find | 单一功能 |
| `tealdeer` (Rust) | 快速 tldr | 单一功能 |
| **evolver-tools** | **32 合一，零依赖，纯 Python** | **覆盖面最广** |

### 独特卖点

1. **零依赖** — pip install 即用，不需要任何外部包
2. **32 合 1** — 一个命令装全套，无需分别安装
3. **纯 Python** — 跨平台，Windows/Mac/Linux 都跑
4. **30KB-100KB** — 极小体积

### 目标用户

- 需要快速系统管理工具的开发者
- 不想装几十个独立包的运维人员
- 在受限环境（CI/CD、容器、内网）工作的工程师
- 想要减少 system toolchain 模糊度的团队

## 三、收入模型

### 模型 A: Freemium (推荐)

```
免费 (MIT 开源):
  22 个基础工具: b64, cal, chart-cli, colors, dirsize, dt,
                  envcheck, hashsum, ipinfo, jq-lite, json2csv,
                  jsonql, license-cli, markdown-check, nb, passgen,
                  portcheck, ren, timer, treedir, urlparse, wordcount

Pro (¥30/年 或 ¥5/月):
  10 个高级工具: csv-stats, ff, find-dups, http-live, project-doctor,
                  siege-lite, smellfinder, sqlite-cli, sysmon, web-summary

定价逻辑: ¥30/年 ≈ 一杯咖啡/年，足够的低门槛
```

### 模型 B: 赞助开源 (Sponsorware)

```
MIT 开源，所有工具免费。
但在 README 和 CLI 中提示:
  "evolver-tools is free & open source. If you use it daily,
   sponsor ¥5/month → github.com/sponsors/evolver"

目标: 100 个赞助者 × ¥5/月 = ¥500/月
```

### 模型 C: 企业授权

```
针对公司/团队:
  - ¥500/年 — 支持自定义工具开发
  - ¥2000/年 — 专属维护 + 紧急修复 + 内网部署支持
  - ¥5000/年 — 全套源码授权 + 定制开发
```

### 推荐路径: Freemium (模型 A)

因为:
1. 有免费层 → 病毒式传播
2. 有付费层 → 可持续现金流
3. Pro 工具是真正的杀手级 (sqlite-cli, sysmon, http-live)
4. ¥30/年 = 冲动的定价点

## 四、分发策略 (Token-Free)

### 现状: 无法发布 PyPI / GitHub Pages

**方案 A: 自托管 PyPI (pypiserver)**
```
pip install pypiserver
pypiserver -p 8080 /path/to/packages/
pip install --index-url http://YOUR_SERVER:8080/simple/ evolver-tools
```
- 需要一台服务器 (¥10-30/月 VPS)
- 可以绑定域名 pi.evolver.dev
- 完全自主可控

**方案 B: GitHub Release + install.sh**
```
# 已有 install.sh
curl -sSL https://evolver.dev/install.sh | bash
# install.sh 从 GitHub Release 下载 wheel
```
- 不需要 PyPI 账户
- 但需要 GitHub token 创建 Release

**方案 C: 直接提供 wheel 下载**
```
# 从网站直接下载 wheel
wget https://cli.evolver.dev/evolver_tools-1.4.0-py3-none-any.whl
pip install evolver_tools-1.4.0-py3-none-any.whl
```
- 可以放在任何静态托管上
- 甚至可以用 IPFS / S3 / Cloudflare R2

### 推荐: 组合方案

1. 短期: install.sh 从自托管下载 wheel
2. 中期: GitHub Release + install.sh
3. 长期: PyPI 官方发布

## 五、启动排期

### Week 1-2: 基础设施
- [ ] 注册 evolver.dev 域名 (如果还没)
- [ ] 在 Vercel/Netlify 免费托管产品站
- [ ] 设置 pypiserver 或类似方案
- [ ] 验证端到端: curl → pip install → evtool list 可用

### Week 3-4: 内容营销
- [ ] Show HN: "32 Zero-Dep CLI Tools, One pip install"
- [ ] r/Python: "I built 32 Python CLI tools with zero dependencies"
- [ ] Dev.to 技术文章: "How I built a CLI toolkit without any dependencies"
- [ ] Twitter/X: 单个工具 GIF 动图展示

### Week 5-8: 增长
- [ ] 收集用户反馈，修复 bug
- [ ] 增加 5 个新工具 (填补市场空白)
- [ ] 启动 Freemium 收费
- [ ] 目标: 1000+ stars, 100+ 日活跃用户

## 六、Show HN 发布帖 (草稿)

> **Title**: Show HN: 32 zero-dependency Python CLI tools — one pip install
>
> **Body**:
> I got tired of pulling in 30+ separate packages for basic CLI tasks.
> So I built a single pip package with 32 essential tools.
>
> Every tool is a single Python file, zero external dependencies.
>
> What's inside:
> - `sqlite-cli` — Query SQLite databases from terminal
> - `ff` — fuzzy-find anything (like fzf, in Python)
> - `sysmon` — Real-time system monitor (CPU/mem/disk/network)
> - `http-live` — SSE hot-reload HTTP server
> - `csv-stats` — Column analysis, histograms, correlations
> - ... and 27 more
>
> ```bash
> pip install evolver-tools
> evtool list           # See all 32 tools
> evtool ff < data.txt # Fuzzy search
> ```
>
> Why 32 tools in one package?
> - One pip install, not 32
> - Single version to maintain
> - Shared patterns across tools
> - 104KB total
>
> MIT licensed. Feedback welcome!

## 七、关键指标

| 指标 | 30天目标 | 90天目标 |
|------|---------|---------|
| GitHub Stars | 100 | 500 |
| PyPI 周下载量 | 500 | 5000 |
| 付费用户 | 5 | 50 |
| 月收入 | ¥150 | ¥1500 |
| Offer 自豪指数 | 5/10 | 8/10 |

## 八、立即行动项

1. 更新 README 到 32 工具 (现在是 31)
2. 更新 products.json 到英文
3. 修正 install.sh 版本号
4. 验证所有 32 工具能正常安装和工作
5. 准备好第一个 Show HN 帖的截图素材

---

*计划版本: v1.0 | 制定日期: 2026-05-30 | 制定者: EVOLVER*
