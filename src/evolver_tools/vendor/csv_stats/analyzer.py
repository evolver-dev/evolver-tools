"""csv-stats core analyzer — pure stdlib, zero dependencies."""

import csv
import math
from collections import Counter


def red(s):    return f"\033[91m{s}\033[0m"
def green(s):  return f"\033[92m{s}\033[0m"
def yellow(s): return f"\033[93m{s}\033[0m"
def cyan(s):   return f"\033[96m{s}\033[0m"
def dim(s):    return f"\033[2m{s}\033[0m"
def bold(s):   return f"\033[1m{s}\033[0m"


def infer_type(values):
    """Infer column type from sample values."""
    nums = []
    for v in values:
        if v == '' or v is None:
            continue
        try:
            nums.append(float(v))
        except (ValueError, TypeError):
            return 'text'
    if len(nums) == 0:
        return 'text'
    all_int = all(n == int(n) for n in nums)
    return 'int' if all_int else 'float'


def numeric_stats(values):
    """Compute numeric statistics."""
    nums = []
    for v in values:
        if v == '' or v is None:
            continue
        try:
            nums.append(float(v))
        except (ValueError, TypeError):
            pass
    if not nums:
        return None
    n = len(nums)
    mean = sum(nums) / n
    variance = sum((x - mean) ** 2 for x in nums) / n
    std = math.sqrt(variance)
    sorted_nums = sorted(nums)

    def percentile(p):
        idx = int(n * p / 100)
        return sorted_nums[min(idx, n - 1)]

    return {
        'count': n, 'missing': len(values) - n,
        'mean': round(mean, 2), 'std': round(std, 2),
        'min': round(min(nums), 2), 'p25': round(percentile(25), 2),
        'p50': round(percentile(50), 2), 'p75': round(percentile(75), 2),
        'max': round(max(nums), 2), 'unique': len(set(nums)),
        'sum': round(sum(nums), 2),
    }


def text_stats(values):
    """Compute text column statistics."""
    non_empty = [v for v in values if v != '' and v is not None]
    lens = [len(str(v)) for v in non_empty]
    return {
        'count': len(values), 'non_empty': len(non_empty),
        'missing': len(values) - len(non_empty),
        'unique': len(set(non_empty)),
        'max_length': max(lens) if lens else 0,
        'min_length': min(lens) if lens else 0,
        'avg_length': round(sum(lens) / len(lens), 1) if lens else 0,
    }


def correlation(x_vals, y_vals):
    """Pearson correlation coefficient."""
    x_nums, y_nums = [], []
    for x, y in zip(x_vals, y_vals):
        if x == '' or y == '' or x is None or y is None:
            continue
        try:
            x_nums.append(float(x))
            y_nums.append(float(y))
        except (ValueError, TypeError):
            pass
    n = len(x_nums)
    if n < 3:
        return None
    mean_x = sum(x_nums) / n
    mean_y = sum(y_nums) / n
    num = sum((x - mean_x) * (y - mean_y) for x, y in zip(x_nums, y_nums))
    denom_x = math.sqrt(sum((x - mean_x) ** 2 for x in x_nums))
    denom_y = math.sqrt(sum((y - mean_y) ** 2 for y in y_nums))
    if denom_x == 0 or denom_y == 0:
        return None
    return round(num / (denom_x * denom_y), 4)


def draw_histogram(values, bins=10, width=30):
    """Draw a simple ASCII histogram."""
    nums = []
    for v in values:
        if v == '' or v is None:
            continue
        try:
            nums.append(float(v))
        except (ValueError, TypeError):
            pass
    if not nums:
        return []
    min_v, max_v = min(nums), max(nums)
    if min_v == max_v:
        return [(f"{min_v:.1f}", len(nums), '█' * width)]
    bucket_size = (max_v - min_v) / bins
    buckets = [0] * bins
    for n in nums:
        idx = min(int((n - min_v) / bucket_size), bins - 1)
        buckets[idx] += 1
    max_count = max(buckets)
    result = []
    for i in range(bins):
        label = f"{min_v + i * bucket_size:.1f}"
        count = buckets[i]
        bar_len = int(count / max_count * width) if max_count > 0 else 0
        result.append((label, count, '█' * bar_len))
    return result


def analyze_csv(filepath, max_rows=None, delimiter=','):
    """Analyze a CSV file and return structured results."""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            reader = csv.reader(f, delimiter=delimiter)
            headers = next(reader, None)
            if not headers:
                return {'error': 'Empty file or missing header row'}
            headers = [h.strip() for h in headers]
            columns = {h: [] for h in headers}
            total_rows = 0
            for row in reader:
                if max_rows and total_rows >= max_rows:
                    break
                total_rows += 1
                for i, h in enumerate(headers):
                    val = row[i].strip() if i < len(row) else ''
                    columns[h].append(val)
    except Exception as e:
        return {'error': str(e), 'file': str(filepath)}

    n_rows = len(next(iter(columns.values())))
    col_stats = {}
    for h in headers:
        vals = columns[h]
        ct = infer_type(vals)
        if ct in ('int', 'float'):
            stats = numeric_stats(vals)
            if stats:
                stats['type'] = ct
                stats['histogram'] = draw_histogram(vals)
            col_stats[h] = stats
        else:
            ts = text_stats(vals)
            ts['type'] = 'text'
            counter = Counter(vals)
            ts['top_values'] = counter.most_common(10)
            col_stats[h] = ts

    numeric_cols = [h for h in headers if col_stats[h] and col_stats[h].get('type') in ('int', 'float')]
    corr_matrix = None
    if len(numeric_cols) >= 2:
        corr_matrix = {}
        for i, c1 in enumerate(numeric_cols):
            for c2 in numeric_cols[i+1:]:
                r = correlation(columns[c1], columns[c2])
                if r is not None:
                    corr_matrix[f"{c1} × {c2}"] = r

    return {
        'file': str(filepath), 'rows': n_rows, 'columns': len(headers),
        'headers': headers, 'col_stats': col_stats,
        'correlations': corr_matrix,
        'max_rows_reached': max_rows and n_rows >= max_rows,
    }


def print_report(result):
    """Print formatted analysis report to stdout."""
    if 'error' in result:
        print("\n" + red('✗ Error: ' + str(result.get('error', ''))))
        return

    print(f"\n{bold('📊 CSV Analysis Report')}")
    print(f"  {dim('File:')} {result['file']}")
    print(f"  {dim('Rows:')} {result['rows']:,}")
    print(f"  {dim('Columns:')} {result['columns']}")
    if result.get('max_rows_reached'):
        print(f"  {yellow('⚠ Sample limit reached')}")
    print()

    for h in result['headers']:
        stats = result['col_stats'].get(h)
        if not stats:
            continue
        print(f"  {bold(h)}")
        if stats['type'] in ('int', 'float'):
            print(f"    {'Type':<12} {green(stats['type'])}")
            print(f"    {'Count':<12} {stats['count']:,}" +
                  (yellow(f' (+{stats["missing"]} missing)') if stats['missing'] else ""))
            print(f"    {'Mean':<12} {stats['mean']:,.2f}")
            print(f"    {'Std Dev':<12} {stats['std']:,.2f}")
            print(f"    {'Min':<12} {stats['min']:,.2f}")
            print(f"    {'P25':<12} {stats['p25']:,.2f}")
            print(f"    {'P50 (Median)':<12} {stats['p50']:,.2f}")
            print(f"    {'P75':<12} {stats['p75']:,.2f}")
            print(f"    {'Max':<12} {stats['max']:,.2f}")
            if stats.get('sum') is not None:
                print(f"    {'Sum':<12} {stats['sum']:,.2f}")
            print(f"    {'Unique':<12} {stats['unique']}")
            if stats.get('histogram'):
                print(f"    {'Distribution':<12}")
                for label, count, bar in stats['histogram']:
                    print(f"      {label:<8} {bar} {count}")
        else:
            missing = stats.get('missing', 0)
            print(f"    {'Type':<12} {cyan('text')}")
            print(f"    {'Total':<12} {stats['count']:,}" +
                  (yellow(f' (+{missing} missing)') if missing else ''))
            print(f"    {'Non-empty':<12} {stats['non_empty']:,}")
            print(f"    {'Unique':<12} {stats['unique']:,}")
            print(f"    {'Max Len':<12} {stats['max_length']} chars")
            print(f"    {'Min Len':<12} {stats['min_length']} chars")
            print(f"    {'Avg Len':<12} {stats['avg_length']} chars")
            if stats.get('top_values'):
                print(f"    {'Top 10':<12}")
                for val, cnt in stats['top_values']:
                    val_str = str(val)[:30]
                    bar_len = int(cnt / max(1, stats['count']) * 20)
                    print(f"      {val_str:<32} {'█' * bar_len} {cnt}")
        print()

    if result.get('correlations'):
        print(f"  {bold('Correlation Matrix')}")
        sorted_corr = sorted(result['correlations'].items(), key=lambda x: abs(x[1]), reverse=True)
        for pair, coef in sorted_corr[:10]:
            color = green if abs(coef) > 0.5 else (yellow if abs(coef) > 0.3 else dim)
            bar_len = int(abs(coef) * 15)
            bar = '█' * bar_len + '░' * (15 - bar_len)
            sign = '+' if coef >= 0 else '−'
            print(f"    {pair:<40} {color(f'{sign}{abs(coef):.4f}')}  {bar}")
        print()

    total_missing = sum(s.get('missing', 0) for s in result['col_stats'].values() if s)
    if total_missing > 0:
        print(f"  {yellow(f'⚠ {total_missing:,} total missing values')}")
    print()
