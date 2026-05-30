#!/usr/bin/env python3
"""
chart-cli — 终端图表生成器
用 Unicode 在终端绘制条形图、折线图、饼图。
"""

import sys
import json
import math
from collections import Counter

# Unicode block characters
BAR_FULL = '█'
BAR_HALF = '▌'
BAR_EMPTY = '░'
H_LINE = '─'
V_LINE = '│'
CORNER_TL = '┌'
CORNER_TR = '┐'
CORNER_BL = '└'
CORNER_BR = '┘'
CROSS = '┼'
TEE_DOWN = '┬'
TEE_UP = '┴'
TEE_RIGHT = '├'
TEE_LEFT = '┤'

# 8-level block for fine-grained bars
BLOCKS = [' ', '▏', '▎', '▍', '▌', '▋', '▊', '▉', '█']

def red(s): return f"\033[91m{s}\033[0m"
def green(s): return f"\033[92m{s}\033[0m"
def yellow(s): return f"\033[93m{s}\033[0m"
def cyan(s): return f"\033[96m{s}\033[0m"
def dim(s): return f"\033[2m{s}\033[0m"
def bold(s): return f"\033[1m{s}\033[0m"

def parse_data(source):
    """Parse data from string or dict"""
    if isinstance(source, list):
        return source
    if isinstance(source, dict):
        return list(source.items())
    # Try parsing as JSON
    try:
        parsed = json.loads(source)
        if isinstance(parsed, list):
            # Handle flat alternating array: ["key1", val1, "key2", val2, ...]
            if parsed and not isinstance(parsed[0], (list, tuple)):
                if len(parsed) % 2 == 0:
                    return [(str(parsed[i]), float(parsed[i+1])) for i in range(0, len(parsed), 2)]
                else:
                    raise ValueError("数组格式应为 [键1, 值1, 键2, 值2, ...] (偶数个元素)")
            return parsed
        if isinstance(parsed, dict):
            return list(parsed.items())
    except json.JSONDecodeError:
        pass
    # Try parsing as key:value lines
    result = []
    # Split by commas first (for inline lists)
    lines = []
    for line in source.strip().split('\n'):
        if ',' in line and not line.startswith('{') and not line.startswith('['):
            # Could be comma-separated pairs
            parts = line.split(',')
            for p in parts:
                p = p.strip()
                if p:
                    lines.append(p)
        else:
            if line.strip():
                lines.append(line.strip())

    for raw_line in lines:
        if ':' in raw_line:
            parts = raw_line.split(':', 1)
            key = parts[0].strip()
            try:
                val = float(parts[1].strip())
                result.append((key, val))
            except ValueError:
                pass
        elif '\t' in raw_line:
            parts = raw_line.split('\t')
            try:
                val = float(parts[-1].strip())
                key = ' '.join(parts[:-1]).strip()
                result.append((key, val))
            except ValueError:
                pass
        else:
            # Try as raw number
            try:
                val = float(raw_line.strip())
                result.append((raw_line.strip(), val))
            except ValueError:
                pass
    return result


def draw_bar_chart(data, width=40, height=12, horizontal=False, sort=False, show_values=True):
    """Draw a bar chart"""
    if not data:
        return "(无数据)"

    if sort:
        data = sorted(data, key=lambda x: x[1], reverse=True)

    labels = [str(d[0])[:20] for d in data]
    values = [float(d[1]) for d in data]

    max_val = max(values) if values else 1
    min_val = min(values)
    lines = []

    if horizontal:
        # Horizontal bar chart
        max_label_len = max(len(l) for l in labels)
        max_label_len = min(max_label_len, 20)

        lines.append(f"  {bold('条形图 (水平)')}")
        lines.append("")

        for i, (label, val) in enumerate(zip(labels, values)):
            bar_width = int((val / max_val) * width) if max_val > 0 else 0
            bar = BAR_FULL * bar_width
            val_str = f" {val}" if show_values else ""
            padded_label = label.ljust(max_label_len)[:max_label_len]
            lines.append(f"  {dim(padded_label)} {dim('│')} {green(bar)}{val_str}")

        lines.append(f"  {dim('─' * (max_label_len + 3 + width))}")
        lines.append(f"  {dim(('0').rjust(max_label_len + 3))} {max_val})")

    else:
        # Vertical bar chart
        max_label_len = max(len(l) for l in labels)
        n_bars = len(labels)

        # Calculate available height for bars (leave room for labels + values)
        bar_area_height = max(5, height - 3)

        lines.append(f"  {bold('条形图 (垂直)')}")
        lines.append("")

        # Draw bars top to bottom
        for row in range(bar_area_height, 0, -1):
            threshold = max_val * (row - 1) / bar_area_height if bar_area_height > 0 else 0

            line_parts = ["  "]
            for val in values:
                if val >= threshold:
                    if val >= max_val * row / bar_area_height:
                        line_parts.append(f" {BAR_FULL} ")
                    else:
                        line_parts.append(f" {BAR_HALF} ")
                else:
                    line_parts.append(f"   ")
            lines.append(''.join(line_parts))

        # Axis line
        lines.append(f"  {'─' * (n_bars * 3 + 1)}")

        # Labels
        line_parts = ["  "]
        for label in labels:
            short = label[:3]
            line_parts.append(f" {short} ")
        lines.append(''.join(line_parts))

        # Value labels
        if show_values:
            line_parts = ["  "]
            for val in values:
                s = str(int(val)) if val == int(val) else f"{val:.1f}"
                line_parts.append(f"{s:>3} ")
            lines.append(''.join(line_parts))

    return '\n'.join(lines)


def draw_line_chart(data, width=50, height=14):
    """Draw a line chart"""
    if not data:
        return "(无数据)"

    # If data is list of (x, y) tuples
    if isinstance(data[0], (list, tuple)) and len(data[0]) >= 2:
        points = [(float(d[0]), float(d[1])) for d in data]
    else:
        # Assume index as x
        points = [(float(i), float(d[1]) if isinstance(d, (list, tuple)) else float(d))
                  for i, d in enumerate(data)]

    if len(points) < 2:
        return "(至少需要2个数据点)"

    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    range_y = max_y - min_y if max_y != min_y else 1
    range_x = max_x - min_x if max_x != min_x else 1

    chart_width = max(20, width - 6)  # Leave room for y-axis labels
    chart_height = max(5, height - 3)

    lines = []
    lines.append(f"  {bold('折线图')}")
    lines.append("")

    # Create the chart grid
    grid = [[' ' for _ in range(chart_width)] for _ in range(chart_height)]

    # Plot points
    for x, y in points:
        col = int((x - min_x) / range_x * (chart_width - 1))
        row = int((max_y - y) / range_y * (chart_height - 1))
        col = min(max(0, col), chart_width - 1)
        row = min(max(0, row), chart_height - 1)
        grid[row][col] = '•'

    # Draw lines between points
    for i in range(len(points) - 1):
        x1, y1 = points[i]
        x2, y2 = points[i+1]
        c1 = int((x1 - min_x) / range_x * (chart_width - 1))
        c2 = int((x2 - min_x) / range_x * (chart_width - 1))
        r1 = int((max_y - y1) / range_y * (chart_height - 1))
        r2 = int((max_y - y2) / range_y * (chart_height - 1))

        # Bresenham-like line drawing
        steps = max(abs(c2 - c1), abs(r2 - r1))
        if steps > 1:
            for t in range(1, steps):
                frac = t / steps
                cx = int(c1 + (c2 - c1) * frac)
                cy = int(r1 + (r2 - r1) * frac)
                cx = min(max(0, cx), chart_width - 1)
                cy = min(max(0, cy), chart_height - 1)
                if grid[cy][cx] == ' ':
                    grid[cy][cx] = '·'

    # Y-axis labels
    y_labels = []
    for i in range(chart_height):
        val = max_y - (range_y * i / (chart_height - 1))
        y_labels.append(f"{val:>6.1f}")

    # Print chart
    for i in range(chart_height):
        label = y_labels[i]
        row_line = ''.join(grid[i])
        lines.append(f"  {dim(label)} {dim(V_LINE)} {cyan(row_line)}")

    # X-axis
    x_label_fmt = f"{min_x:.1f}".rjust(chart_width // 2) + f"{max_x:.1f}".rjust(chart_width // 2)
    lines.append(f"  {dim('      ')} {dim('└')}{dim('─' * chart_width)}")
    lines.append(f"  {dim('      ')}  {x_label_fmt}")

    return '\n'.join(lines)


def draw_pie_chart(data, radius=8):
    """Draw a pie chart using braille/block characters"""
    if not data:
        return "(无数据)"

    total = sum(float(d[1]) for d in data)
    if total == 0:
        return "(总和为零)"

    labels = [str(d[0])[:15] for d in data]
    values = [float(d[1]) for d in data]

    # Calculate angles (in radians, starting from top)
    angles = []
    cumulative = 0
    for val in values:
        angle = (val / total) * 2 * math.pi
        cumulative += angle
        angles.append(cumulative)

    # Round to first angle = 0
    angles = [0] + angles

    # Available colors
    colors = [
        '\033[91m', '\033[93m', '\033[92m', '\033[96m',
        '\033[94m', '\033[95m', '\033[38;5;208m', '\033[38;5;45m',
    ]
    reset = '\033[0m'

    diameter = radius * 2 + 1
    center_x = radius
    center_y = radius

    lines = []
    lines.append(f"  {bold('饼图')}")
    lines.append("")

    # Generate pie
    pie_chars = []
    for y in range(diameter):
        row_chars = []
        for x in range(diameter):
            # Distance from center
            dx = x - center_x
            dy = y - center_y
            dist = math.sqrt(dx * dx + dy * dy)

            if dist < radius - 0.5:
                # Inside: check angle
                angle = math.atan2(dx, -dy)  # Atan2, with top as 0
                if angle < 0:
                    angle += 2 * math.pi

                # Find which segment
                seg_idx = -1
                for i in range(len(angles) - 1):
                    if angles[i] <= angle < angles[i + 1]:
                        seg_idx = i
                        break
                if seg_idx == -1 and angle >= angles[-2]:
                    seg_idx = len(angles) - 2

                if 0 <= seg_idx < len(colors):
                    # Draw filled with dithering
                    # Use different chars for different segments
                    chars = ['█', '▓', '▒', '░']
                    c = colors[seg_idx % len(colors)]
                    row_chars.append(f"{c}{chr(0x2588)}{reset}")
                else:
                    row_chars.append('  ')
            elif dist < radius + 0.5:
                row_chars.append(f"{dim('·')} ")
            else:
                row_chars.append('  ')
        pie_chars.append(''.join(row_chars))

    # Print pie + legend side by side
    legend_lines = []
    for i in range(len(data)):
        c = colors[i % len(colors)]
        pct = values[i] / total * 100
        legend_lines.append(f"  {c}█{reset} {labels[i]:<15} {values[i]:>8}  ({pct:4.1f}%)")

    max_lines = max(len(pie_chars), len(legend_lines))
    for i in range(max_lines):
        left = pie_chars[i] if i < len(pie_chars) else ' ' * (diameter * 2)
        right = legend_lines[i] if i < len(legend_lines) else ''
        print(f"  {left}  {right}")

    return "\n"  # Already printed during drawing


def draw_histogram_chart(data, bins=10, width=40):
    """Draw a histogram from raw values"""
    if not data:
        return "(无数据)"

    values = [float(d) if isinstance(d, (int, float)) else float(d[1]) for d in data]
    if not values:
        return "(无数据)"

    min_v = min(values)
    max_v = max(values)
    if min_v == max_v:
        return f"  所有值相同: {min_v}"

    range_v = max_v - min_v
    bucket_size = range_v / bins
    buckets = [0] * bins

    for v in values:
        idx = min(int((v - min_v) / bucket_size), bins - 1)
        buckets[idx] += 1

    max_count = max(buckets)
    lines = []
    lines.append(f"  {bold('直方图')}")
    lines.append(f"  {dim(f'区间数: {bins}, 总值: {len(values)}')}")
    lines.append("")

    for i in range(bins):
        lo = min_v + i * bucket_size
        hi = lo + bucket_size
        count = buckets[i]
        bar_len = int(count / max_count * width) if max_count > 0 else 0
        bar = BAR_FULL * bar_len

        if i == 0:
            label = f"{lo:.1f}-{hi:.1f}"
        elif i == bins - 1:
            label = f"{lo:.1f}+"
        else:
            label = f"{lo:.1f}"

        pct = count / len(values) * 100
        lines.append(f"  {dim(label):<16} {green(bar)} {count} ({pct:.1f}%)")

    return '\n'.join(lines)


def main():
    import argparse
    parser = argparse.ArgumentParser(description='终端图表生成器')
    parser.add_argument('type', choices=['bar', 'line', 'pie', 'hist'],
                       help='图表类型')
    parser.add_argument('data', nargs='?', help='数据（JSON 或 key:value 格式，或从 stdin 读取）')
    parser.add_argument('-w', '--width', type=int, default=40, help='图表宽度')
    parser.add_argument('-H', '--height', type=int, default=12, help='图表高度')
    parser.add_argument('--horizontal', action='store_true', help='条形图水平模式')
    parser.add_argument('--sort', action='store_true', help='排序（条形图）')
    parser.add_argument('--no-values', action='store_true', help='隐藏数值')
    args = parser.parse_args()

    # Read data
    data_source = args.data
    if not data_source and not sys.stdin.isatty():
        data_source = sys.stdin.read()

    if not data_source:
        print("错误: 请提供数据（参数或 stdin）")
        sys.exit(1)

    data = parse_data(data_source)
    if not data:
        print("错误: 无法解析数据。支持 JSON 或 key:value 格式")
        sys.exit(1)

    if args.type == 'bar':
        print(draw_bar_chart(data, args.width, args.height,
                             args.horizontal, args.sort, not args.no_values))
    elif args.type == 'line':
        print(draw_line_chart(data, args.width, args.height))
    elif args.type == 'pie':
        draw_pie_chart(data, args.radius if hasattr(args, 'radius') else 8)
    elif args.type == 'hist':
        print(draw_histogram_chart(data, 10, args.width))


if __name__ == '__main__':
    main()
