#!/usr/bin/env python3
"""
web-summary — 网页摘要提取器
从 URL 提取标题、正文、链接。零外部依赖。
"""

import sys
import re
import urllib.request
import urllib.error
import urllib.parse
from html.parser import HTMLParser
from collections import Counter
from datetime import datetime

def red(s): return f"\033[91m{s}\033[0m"
def green(s): return f"\033[92m{s}\033[0m"
def yellow(s): return f"\033[93m{s}\033[0m"
def cyan(s): return f"\033[96m{s}\033[0m"
def dim(s): return f"\033[2m{s}\033[0m"
def bold(s): return f"\033[1m{s}\033[0m"


class PageExtractor(HTMLParser):
    """HTML parser that extracts title, text, and links"""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title = ''
        self._in_title = False
        self._in_script = False
        self._in_style = False
        self._in_a = False
        self._current_link = ''
        self.text_parts = []
        self.links = []
        self.meta_tags = {}

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        attr_dict = dict(attrs)

        if tag == 'title':
            self._in_title = True
        elif tag in ('script', 'style'):
            self._in_script = True
        elif tag == 'a' and 'href' in attr_dict:
            self._in_a = True
            self._current_link = attr_dict['href']
        elif tag == 'meta':
            name = attr_dict.get('name', attr_dict.get('property', '')).lower()
            content = attr_dict.get('content', '')
            if name and content:
                self.meta_tags[name] = content

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag == 'title':
            self._in_title = False
        elif tag in ('script', 'style'):
            self._in_script = False
        elif tag == 'a':
            if self._current_link and hasattr(self, '_last_link_text'):
                self.links.append((self._current_link, self._last_link_text.strip()))
            self._in_a = False
            self._current_link = ''

    def handle_data(self, data):
        if self._in_title:
            self.title += data.strip()
        elif not self._in_script and not self._in_style:
            data = data.strip()
            if data:
                self.text_parts.append(data)
                if self._in_a:
                    self._last_link_text = data

    def handle_entityref(self, name):
        if not self._in_script and not self._in_style:
            self.text_parts.append(f'&{name};')


def fetch_page(url, timeout=15):
    """Fetch a web page"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (compatible; web-summary/1.0)',
        'Accept': 'text/html,application/xhtml+xml',
    }
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            content = resp.read()
            # Try to detect encoding
            charset = resp.headers.get_content_charset()
            if charset:
                text = content.decode(charset, errors='replace')
            else:
                # Try common Chinese encodings
                for enc in ['utf-8', 'gbk', 'gb2312', 'gb18030', 'latin-1']:
                    try:
                        text = content.decode(enc)
                        break
                    except (UnicodeDecodeError, UnicodeError):
                        continue
                else:
                    text = content.decode('utf-8', errors='replace')

            return {
                'url': url,
                'status': resp.status,
                'html': text,
                'size': len(content),
                'content_type': resp.headers.get('Content-Type', ''),
            }
    except urllib.error.HTTPError as e:
        return {'url': url, 'status': e.code, 'error': str(e), 'html': ''}
    except Exception as e:
        return {'url': url, 'status': 0, 'error': str(e), 'html': ''}


def clean_text(text_parts):
    """Join and clean text parts"""
    text = ' '.join(text_parts)
    # Remove repeated whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def extract_keywords(text, top_n=10):
    """Extract likely keywords by frequency"""
    # Simple word frequency
    words = re.findall(r'[a-zA-Z\u4e00-\u9fff]+', text.lower())
    # Filter common stop words
    stop_words = {
        'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
        'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
        'would', 'could', 'should', 'may', 'might', 'shall', 'am',
        'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by', 'from',
        'as', 'into', 'through', 'during', 'before', 'after', 'up',
        'down', 'out', 'off', 'over', 'under', 'again', 'further',
        'then', 'once', 'here', 'there', 'when', 'where', 'why',
        'how', 'all', 'each', 'every', 'both', 'few', 'more', 'most',
        'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own',
        'same', 'so', 'than', 'too', 'very', 'and', 'but', 'or', 'if',
        'because', 'about', 'between', 'while', 'without', 'this',
        'that', 'these', 'those', 'it', 'its', 'he', 'she', 'they',
        'them', 'their', 'my', 'your', 'our', 'we', 'you', 'i', 'me',
    }
    words = [w for w in words if w not in stop_words and len(w) > 1]
    return Counter(words).most_common(top_n)


def resolve_link(base_url, link):
    """Resolve relative URLs"""
    if not link or link.startswith('#') or link.startswith('javascript:'):
        return None
    if link.startswith('http://') or link.startswith('https://'):
        return link
    return urllib.parse.urljoin(base_url, link)


def summarize(url, max_text_len=2000, max_links=30, timeout=15):
    """Fetch and summarize a web page"""
    result = fetch_page(url, timeout)

    if result.get('error'):
        return result

    if not result['html']:
        return result

    # Parse HTML
    parser = PageExtractor()
    try:
        parser.feed(result['html'])
    except Exception:
        pass

    # Extract text
    raw_text = clean_text(parser.text_parts)
    title = parser.title.strip()
    if not title:
        # Try <h1> as fallback title
        h1_match = re.search(r'<h1[^>]*>(.*?)</h1>', result['html'], re.DOTALL)
        if h1_match:
            title = re.sub(r'<[^>]+>', '', h1_match.group(1)).strip()[:100]

    # Get meta description
    meta_desc = parser.meta_tags.get('description', '') or parser.meta_tags.get('og:description', '')

    # Count words
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', raw_text))
    english_words = len(re.findall(r'[a-zA-Z]+', raw_text))

    # Keywords
    keywords = extract_keywords(raw_text)

    # Links
    parsed_url = urllib.parse.urlparse(url)
    base = f"{parsed_url.scheme}://{parsed_url.netloc}"
    internal_links = []
    external_links = []
    for link_url, link_text in parser.links[:max_links]:
        resolved = resolve_link(url, link_url)
        if not resolved:
            continue
        if parsed_url.netloc in resolved:
            internal_links.append((resolved, link_text[:50]))
        else:
            external_links.append((resolved, link_text[:50]))

    # Text preview (first N chars)
    text_preview = raw_text[:max_text_len]
    if len(raw_text) > max_text_len:
        text_preview += '...'

    return {
        'url': url,
        'status': result['status'],
        'title': title,
        'size': result.get('size', 0),
        'meta_description': meta_desc,
        'text_preview': text_preview,
        'total_chinese_chars': chinese_chars,
        'total_english_words': english_words,
        'total_text_len': len(raw_text),
        'keywords': keywords,
        'total_links': len(parser.links),
        'internal_links': internal_links[:15],
        'external_links': external_links[:15],
    }


def print_summary(s):
    """Print formatted summary"""
    if s.get('error'):
        print(f"\n  {red('✗ 错误:')} {s['error']}")
        if s.get('status'):
            print(f"  {dim('状态码:')} {s['status']}")
        return

    print(f"\n  {bold('📄 网页摘要')}")
    print(f"  {dim('─' * 55)}")

    # URL & Status
    print(f"  {dim('URL:')}     {s['url']}")
    status_str = f"{green(s['status'])}" if s['status'] < 400 else f"{red(s['status'])}"
    print(f"  {dim('状态:')}    {status_str}")
    if s.get('size'):
        size_kb = s['size'] / 1024
        print(f"  {dim('大小:')}    {size_kb:.1f} KB")

    print(f"  {dim('─' * 55)}")

    # Title
    if s['title']:
        print(f"  {bold('标题:')}   {cyan(s['title'])}")
    else:
        print(f"  {yellow('标题: (未检测到)')}")

    # Meta description
    if s.get('meta_description'):
        print(f"  {dim('描述:')}   {s['meta_description'][:120]}")

    print(f"  {dim('─' * 55)}")

    # Stats
    print(f"  {bold('统计')}")
    print(f"  {dim('中文字数:')}  {s['total_chinese_chars']:,}")
    print(f"  {dim('英文单词:')}  {s['total_english_words']:,}")
    print(f"  {dim('总字符:')}   {s['total_text_len']:,}")
    print(f"  {dim('链接数:')}   {s['total_links']} ({len(s['internal_links'])} 内部 + {len(s['external_links'])} 外部)")

    print(f"  {dim('─' * 55)}")

    # Keywords
    if s.get('keywords'):
        print(f"  {bold('高频词')}")
        max_kw = max(c for _, c in s['keywords']) if s['keywords'] else 1
        for kw, count in s['keywords'][:15]:
            bar_len = int(count / max_kw * 15)
            bar = '█' * bar_len
            print(f"    {kw:<12} {bar} {count}")

    print(f"  {dim('─' * 55)}")

    # Text preview
    print(f"  {bold('正文预览')}")
    # Simple paragraph detection
    preview = s['text_preview']
    paragraphs = preview.split('. ')
    displayed = 0
    for para in paragraphs:
        if displayed >= 10:
            print(f"  {dim('...')}")
            break
        para = para.strip()
        if len(para) > 5:
            print(f"  {dim('│')} {para[:120]}")
            displayed += 1

    # Links
    print(f"  {dim('─' * 55)}")
    if s['internal_links']:
        print(f"  {bold('内部链接')}")
        for link_url, link_text in s['internal_links'][:8]:
            text = f" ({link_text})" if link_text else ""
            print(f"    {dim('→')} {link_url}{green(text)}")

    if s['external_links']:
        print(f"  {bold('外部链接')}")
        for link_url, link_text in s['external_links'][:8]:
            text = f" ({link_text})" if link_text else ""
            print(f"    {dim('→')} {link_url}{green(text)}")

    print(f"  {dim('─' * 55)}")
    print()


def main():
    import argparse
    parser = argparse.ArgumentParser(description='网页摘要提取器')
    parser.add_argument('url', help='目标 URL')
    parser.add_argument('--text-len', type=int, default=2000, help='正文预览长度 (默认: 2000)')
    parser.add_argument('--json', action='store_true', help='JSON 格式输出')
    parser.add_argument('--timeout', type=int, default=15, help='超时秒数')
    args = parser.parse_args()

    result = summarize(args.url, max_text_len=args.text_len, timeout=args.timeout)

    if args.json:
        import json
        # Remove text preview for cleaner JSON
        output = {k: v for k, v in result.items() if k != 'text_preview'}
        print(json.dumps(output, indent=2, ensure_ascii=False))
    else:
        print_summary(result)



# === Auto-registration metadata ===
TOOL_META = {
    "name": "web-summary",
    "func": "main",
    "desc": 'Web Summary',
}

if __name__ == '__main__':
    main()
