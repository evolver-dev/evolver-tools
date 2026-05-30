#!/usr/bin/env python3
"""html2markdown — Convert HTML to Markdown.

Usage: html2markdown < file.html
       cat file.html | html2markdown [--wrap=80]
       html2markdown file.html

Converts HTML to readable Markdown using Python's html.parser.
Handles: headings, links, images, lists, bold/italic, code blocks.
Zero-dependency (stdlib only).
"""

import sys, re
from html.parser import HTMLParser

class HtmlToMarkdown(HTMLParser):
    def __init__(self, wrap=0):
        super().__init__()
        self.result = []
        self.wrap = wrap
        self.in_pre = False
        self.in_code = False
        self.in_list = False
        self.list_depth = 0
        self.list_type = []
        self.skip_newlines = 0
        
    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        attr_dict = dict(attrs)
        
        if tag in ('h1', 'h2', 'h3', 'h4', 'h5', 'h6'):
            level = int(tag[1])
            self.result.append('\n' + '#' * level + ' ')
        elif tag == 'p':
            self.result.append('\n\n')
        elif tag == 'br':
            self.result.append('\n')
        elif tag == 'hr':
            self.result.append('\n\n---\n\n')
        elif tag in ('b', 'strong'):
            self.result.append('**')
        elif tag in ('i', 'em'):
            self.result.append('*')
        elif tag == 'code' and not self.in_pre:
            self.in_code = True
            self.result.append('`')
        elif tag == 'pre':
            self.in_pre = True
            self.result.append('\n```\n')
        elif tag == 'a':
            href = attr_dict.get('href', '')
            self.result.append('[')
            self._link_href = href
        elif tag == 'img':
            alt = attr_dict.get('alt', '')
            src = attr_dict.get('src', '')
            self.result.append(f'![{alt}]({src})')
        elif tag in ('ul', 'ol'):
            self.list_depth += 1
            self.list_type.append('ol' if tag == 'ol' else 'ul')
            self.result.append('\n')
        elif tag == 'li':
            self.result.append('\n')
            indent = '  ' * (self.list_depth - 1)
            prefix = f"{indent}- " if self.list_type and self.list_type[-1] == 'ul' else f"{indent}1. "
            self.result.append(prefix)
        elif tag == 'blockquote':
            self.result.append('\n> ')
        elif tag in ('table', 'tr', 'td', 'th', 'thead', 'tbody'):
            pass  # Skip tables for simplicity
    
    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag in ('h1', 'h2', 'h3', 'h4', 'h5', 'h6'):
            self.result.append('\n')
        elif tag == 'p':
            pass
        elif tag in ('b', 'strong'):
            self.result.append('**')
        elif tag in ('i', 'em'):
            self.result.append('*')
        elif tag == 'code' and not self.in_pre:
            self.in_code = False
            self.result.append('`')
        elif tag == 'pre':
            self.in_pre = False
            self.result.append('\n```\n')
        elif tag == 'a':
            href = getattr(self, '_link_href', '')
            self.result.append(f']({href})')
            self._link_href = ''
        elif tag in ('ul', 'ol'):
            self.list_depth -= 1
            if self.list_type:
                self.list_type.pop()
            self.result.append('\n')
        elif tag == 'li':
            self.result.append('\n')
        elif tag == 'blockquote':
            self.result.append('\n\n')
    
    def handle_data(self, data):
        if self.in_pre:
            self.result.append(data)
        else:
            # Clean whitespace
            data = re.sub(r'\s+', ' ', data)
            self.result.append(data)
    
    def handle_entityref(self, name):
        char_map = {
            'amp': '&', 'lt': '<', 'gt': '>', 'quot': '"',
            'apos': "'", 'nbsp': ' ', 'copy': '©',
        }
        self.result.append(char_map.get(name, f'&{name};'))
    
    def get_markdown(self):
        text = ''.join(self.result)
        # Clean up excessive blank lines
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip() + '\n'

def main():
    args = sys.argv[1:]
    wrap = 0
    files = []

    for a in args:
        if a.startswith('--wrap='):
            wrap = int(a.split('=', 1)[1])
        elif not a.startswith('-'):
            files.append(a)
        elif a in ('-h', '--help'):
            print(__doc__)
            return

    if files:
        for f in files:
            with open(f) as fh:
                html = fh.read()
    else:
        html = sys.stdin.read()

    parser = HtmlToMarkdown(wrap=wrap)
    parser.feed(html)
    print(parser.get_markdown())

if __name__ == '__main__':
    main()
