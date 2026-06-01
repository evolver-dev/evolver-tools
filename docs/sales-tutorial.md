# 从零到报告：只用命令行分析销售数据

> 一个真实场景，只用 `evtool` 命令，不用 Python、R、Excel。

## 场景

你有一个 `sales_2026.csv` 文件，记录了今年前5个月的销售数据：

```
Date,Region,Product,Units,Revenue,Cost
2026-01-15,APAC,Widget A,120,2400,1200
2026-01-15,EMEA,Widget B,85,2125,1020
...
```

你想知道：哪个地区利润最高？哪个产品卖得最好？趋势如何？

## 安装

```bash
pip install evolver-tools
```

零依赖，3秒装完。

## 第一步：看看数据长什么样

```bash
evtool csv-preview sales_2026.csv
```

```
Rows: 1,234 | Columns: 6
+------------+--------+-----------+-------+---------+-------+
| Date       | Region | Product   | Units | Revenue | Cost  |
+------------+--------+-----------+-------+---------+-------+
| 2026-01-15 | APAC   | Widget A  | 120   | 2400    | 1200  |
| 2026-01-15 | EMEA   | Widget B  | 85    | 2125    | 1020  |
| ...        | ...    | ...       | ...   | ...     | ...   |
+------------+--------+-----------+-------+---------+-------+
```

## 第二步：统计概况

```bash
evtool csv-stats sales_2026.csv
```

```
Column: Revenue
  Count: 1,234
  Mean: 1,875.42
  Min: 120.00
  Max: 9,800.00
  Std: 1,234.56

Column: Units
  Count: 1,234
  Mean: 78.5
  Min: 1
  Max: 500
```

## 第三步：按地区分析利润

```bash
# 加一列利润
evtool csv-eval sales_2026.csv --expr "Revenue - Cost" --name Profit | \
  evtool csv-group --by Region --agg Profit:sum --agg Revenue:sum --agg Cost:sum | \
  evtool csv-sort --by Profit:sum --desc
```

```
+--------+-------------+--------------+------------+
| Region | Profit:sum  | Revenue:sum  | Cost:sum   |
+--------+-------------+--------------+------------+
| APAC   | 456,789.00  | 912,345.00   | 455,556.00 |
| AMER   | 345,678.00  | 789,012.00   | 443,334.00 |
| EMEA   | 234,567.00  | 567,890.00   | 333,323.00 |
+--------+-------------+--------------+------------+
```

APAC 利润最高！

## 第四步：找明星产品

```bash
evtool csv-filter sales_2026.csv --column Units --gt 200 | \
  evtool csv-group --by Product --agg Units:count --agg Units:sum | \
  evtool csv-sort --by Units:sum --desc
```

```
+-----------+-------------+-----------+
| Product   | Units:count | Units:sum |
+-----------+-------------+-----------+
| Widget A  | 45          | 12,345    |
| Widget B  | 38          | 9,876     |
| Gadget X  | 22          | 5,432     |
+-----------+-------------+-----------+
```

Widget A 是销量冠军。

## 第五步：看月度趋势

```bash
evtool csv-select sales_2026.csv --column Date --column Revenue | \
  evtool csv-filter --column Revenue --gt 0 | \
  evtool csv-eval --expr "Date[:7]" --name Month | \
  evtool csv-group --by Month --agg Revenue:sum --agg Revenue:mean | \
  evtool csv-sort --by Month
```

```
+---------+--------------+---------------+
| Month   | Revenue:sum  | Revenue:mean  |
+---------+--------------+---------------+
| 2026-01 | 567,890.00   | 1,234.00      |
| 2026-02 | 612,345.00   | 1,456.00      |
| 2026-03 | 723,456.00   | 1,678.00      |
| 2026-04 | 834,567.00   | 1,890.00      |
| 2026-05 | 956,789.00   | 2,100.00      |
+---------+--------------+---------------+
```

收入逐月增长，趋势向好。

## 第六步：利润分布可视化

```bash
evtool csv-eval sales_2026.csv --expr "Revenue - Cost" --name Profit | \
  evtool csv-chart --column Profit --type histogram --bins 10
```

```
Profit Distribution (10 bins, n=1,234):
[0 - 200)     ████████████████░░░░  156
[200 - 400)   ████████████████████  234
[400 - 600)   ████████████████████  245
[600 - 800)   ██████████████░░░░░░  178
[800 - 1000)  ████████████░░░░░░░░  145
[1000 - 1200) ████████░░░░░░░░░░░░  98
[1200 - 1400) ██████░░░░░░░░░░░░░░  78
[1400 - 1600) ████░░░░░░░░░░░░░░░░  56
[1600 - 1800) ███░░░░░░░░░░░░░░░░░  32
[1800 - 2000) ██░░░░░░░░░░░░░░░░░░  12
```

大部分订单利润在 200-600 之间，分布相当健康。

## 第七步：生成最终报告

```bash
evtool csv-eval sales_2026.csv --expr "Revenue - Cost" --name Profit | \
  evtool csv-group --by Region --agg Profit:sum --agg Revenue:sum --agg Cost:sum --agg Units:mean | \
  evtool csv-sort --by Profit:sum --desc > region_report.csv

evtool csv-preview region_report.csv
```

你已经得到了一个PDF级的分析报告——所有命令纯文本可复现，没有GUI，没有鼠标。

## 不只是数据分析

这是 254 个工具中的一小部分。还有：

- **网络诊断**: `evtool dns-lookup`, `evtool port-scan`, `evtool ssl-check`
- **系统监控**: `evtool system-info`, `evtool disk-usage`, `evtool cpu-stats`
- **开发工具**: `evtool passgen`, `evtool qrcode`, `evtool hash-file`
- **文本处理**: `evtool regex-find`, `evtool dedup-lines`, `evtool text-stats`
- **日常工具**: `evtool weather-cli`, `evtool crypto-price`, `evtool translate`
- **……共254个**

## 安装

```bash
pip install evolver-tools
```

不用装 jq、csvkit、figlet、htop 等一堆包了。254 个工具，一个命名空间，零冲突。

---

**GitHub**: https://github.com/evolver-dev/evolver-tools  
**完整文档**: https://evolver-dev.github.io/evolver-tools/  
**无需安装试玩**: `curl -sL https://evolver-dev.github.io/evolver-tools/try.sh | bash`
