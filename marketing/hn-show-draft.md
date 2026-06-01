# Show HN 发布策略 + 草稿

> 研究日期: 2026-05-30
> 数据来源: HN Algolia — Show HN CLI 工具热度分析

---

## 核心策略

### 策略 A: 单工具逐个突破（推荐）
**理由**: HN 前 15 名高赞 CLI 帖子全部是单工具。没有 "23 tools in one" 上榜。

| 排名 | 类型 | 分数 |
|------|------|------|
| 1 | 单功能（网页存档） | 640 |
| 2 | 单功能（自托管） | 452 |
| 3 | 单功能（端口杀进程） | 153 |
| 4 | 单功能（PDF 编辑） | 176 |
| 5 | 工具箱（Rich-CLI） | 126 |

**结论**: 值得先推 2-3 个最强的单工具，建立口碑后再推集合包。

### 策略 B: 集合包发 Dev.to
集合包模式适合 Dev.to 的长文 + 列表格式。

---

## 最强单工具候选（按 HN 吸引度排序）

### 1. sysmon — 终端系统监控仪
**标题**: Show HN: I made a real-time system monitor for the terminal (like htop, but with curses and 0 dependencies)
**HN 吸引理由**: 运维工具是 HN 热门领域，实时终端 UI 容易出视觉效果（截图/GIF）
**热度预期**: ~100-200 pts

### 2. siege-lite — HTTP 压力测试
**标题**: Show HN: Siege Lite – a lightweight HTTP load tester in pure Python (no external deps)
**HN 吸引理由**: 开发者的日常工具，竞争者少（siege/ab 都有依赖问题）
**热度预期**: ~80-150 pts

### 3. find-dups — 重复文件查找
**标题**: Show HN: Find-dups – SHA256-based duplicate file finder (pure Python, 0 deps)
**HN 吸引理由**: 实用工具，人人都会遇到
**热度预期**: ~60-120 pts

---

## 发布日历

| 周 | 动作 | 目标 |
|----|------|------|
| 1 | Push to GitHub + enable Pages | 公开展示 |
| 2 | Show HN: sysmon | ~100+ pts |
| 3 | Dev.to: "23 CLI tools in one pip install" | ~5K+ views |
| 4 | Show HN: siege-lite | ~80+ pts |
| 5 | Collect feedback, iterate | — |
| 6 | Show HN: evolver-tools (full bundle) | ~50+ pts |

---

## Show HN 主标题候选

**sysmon (首选推出)**:
1. "Show HN: I built a real-time system monitor for the terminal (pure Python, 0 deps)"
2. "Show HN: sysmon – htop-like system monitor, zero dependencies, pip install"
3. "Show HN: Sysmon – a curses-based system monitor that works everywhere Python does"

**evolver-tools (后续推出)**:
1. "Show HN: 23 zero-dependency CLI tools, one pip install"
2. "Show HN: I made a Swiss Army knife of CLI utilities – 23 tools, 0 deps"

---

## 发布清单

- [ ] GitHub 仓库创建 + Pages 启用 (需要 Owner: GitHub PAT token)
- [ ] 为 sysmon 录制 ASCII 视频 demo (manim 或终端录像)
- [ ] 写 HN 帖子正文（见下方模板）
- [ ] 确认帖子发布时间（建议周二-周四 UTC 13-15 点）

---

## HN 帖子模板

```
Title: Show HN: I built a real-time system monitor for the terminal (pure Python)

Hey HN!

I got tired of installing htop/btop on every new server and dealing with
missing dependencies. So I built sysmon — a real-time system monitor that
works everywhere Python 3 does.

Features:
- Real-time CPU, memory, disk, and network monitoring
- Process list with kill support
- Full curses TUI
- Zero external dependencies (std lib only!)

Install:
  pip install evolver-tools

Or standalone:
  pip install sysmon

Then just:
  evtool sysmon

It's about 200 lines of Python, MIT licensed.

GitHub: https://github.com/evolver/evolver-tools
Docs: https://cli.evolver.dev

Would love feedback!
```

---

## Dev.to 博客标题候选

1. "23 Python CLI Tools I Built in a Weekend (Zero Dependencies)"
2. "How I Built a Swiss Army Knife of CLI Utilities"
3. "The Ultimate Python CLI Toolkit: 23 Tools, 0 Dependencies"
