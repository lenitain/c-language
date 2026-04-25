#!/usr/bin/env python3
"""Generate HTML section files from c_tutorial.txt.

Parses C Programming Language textbook into per-section HTML files
with syntax-highlighted code blocks and merged paragraphs.
"""
import re
import os

OUTPUT_DIR = '/home/pilot/.cloned/d1ee2/sections'
INPUT_FILE = '/home/pilot/.cloned/d1ee2/c_tutorial.txt'

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def is_title_like(text):
    """Check if text looks like a section title (short, no sentence punctuation)."""
    if len(text) > 25:
        return False
    if re.search(r'[，。、；：？！？,]', text):
        return False
    # Reject lines with operators or programming symbols
    if re.search(r'&&|\|\||->|==|!=|<=|>=|\+=|-=|\*=|/=', text):
        return False
    # Title has Chinese chars and no digits in the first 3 chars
    if re.search(r'[\u4e00-\u9fff]', text):
        if re.match(r'^.{0,3}\d', text):
            return False
        return True
    # Appendix titles might be English or mixed
    return bool(text.strip()) and not re.match(r'^\d', text)

# ---------------------------------------------------------------------------
# Section Parsing
# ---------------------------------------------------------------------------

def build_section_data(content):
    """Extract valid section numbers and titles from the TOC area."""
    content = content.replace('\f', '')
    valid = set()
    titles = {}

    lines = content.split('\n')
    total = len(lines)

    num_pat = re.compile(r'^(\d+(?:\.\d+)*)\.?\s*$')
    app_pat = re.compile(r'^([AB])\.(\d+(?:\.\d+)*)\s*$')

    i = 0
    while i < total:
        line = lines[i]
        m = num_pat.match(line)
        is_app = False
        if m:
            section_num = m.group(1)
        else:
            m = app_pat.match(line)
            if m:
                section_num = f'{m.group(1)}.{m.group(2)}'
                is_app = True
            else:
                i += 1
                continue

        parts = section_num.split('.')
        if len(parts) < 2 or len(parts) > 3:
            i += 1
            continue

        char_pos = sum(len(l) + 1 for l in lines[:i])
        if char_pos >= content.find('第1章 导言'):
            break

        valid.add(section_num)

        # Extract title: next non-blank line
        title = ''
        for j in range(i + 1, min(i + 4, total)):
            if lines[j].strip():
                title = lines[j].strip()
                break

        title = re.sub(r'\s*\.{5,}\s*\d*\s*$', '', title)
        if title:
            titles[section_num] = title

        i += 1

    return valid, titles


def parse_tutorial(input_file):
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()

    content = content.replace('\f', '')
    content = re.sub(r'\n\d+\n---\n', '\n', content)
    valid_sections, toc_titles = build_section_data(content)

    content_start = content.find('第1章 导言')
    if content_start < 0:
        content_start = 0

    lines = content.split('\n')
    total_lines = len(lines)

    num_pat = re.compile(r'^(\d+(?:\.\d+)*)\.?\s*$')
    num_same_pat = re.compile(r'^(\d+(?:\.\d+)*)\.\s+(.+)$')
    app_pat = re.compile(r'^([AB])\.(\d+(?:\.\d+)*)\s*$')

    matched_indices = []
    # For same-line titles, store (line_index, title)
    matched_same_line = {}  # section_num -> (line_index, title)

    for i, line in enumerate(lines):
        char_pos = sum(len(l) + 1 for l in lines[:i])
        if char_pos < content_start:
            continue

        # Try same-line format first
        sm = num_same_pat.match(line)
        if sm:
            section_num = sm.group(1)
            candidate_title = sm.group(2).strip()
            candidate_title = re.sub(r'\s*\.{5,}\s*\d*\s*$', '', candidate_title)
            if section_num in valid_sections:
                parts = section_num.split('.')
                if 2 <= len(parts) <= 3:
                    if i > 0 and lines[i - 1].strip():
                        continue
                    if is_title_like(candidate_title):
                        matched_same_line[section_num] = (i, candidate_title)
                        matched_indices.append(i)
            continue

        m = num_pat.match(line)
        if m:
            section_num = m.group(1)
        else:
            m = app_pat.match(line)
            if m:
                section_num = f'{m.group(1)}.{m.group(2)}'
            else:
                continue

        if section_num not in valid_sections:
            continue

        parts = section_num.split('.')
        if len(parts) < 2 or len(parts) > 3:
            continue

        if i > 0 and lines[i - 1].strip():
            continue

        matched_indices.append(i)

    sections = []
    for idx, line_idx in enumerate(matched_indices):
        m = num_pat.match(lines[line_idx])
        if m:
            section_num = m.group(1)
        else:
            m = num_same_pat.match(lines[line_idx])
            if m:
                section_num = m.group(1)
            else:
                m = app_pat.match(lines[line_idx])
                if m:
                    section_num = f'{m.group(1)}.{m.group(2)}'
                else:
                    continue

        # Determine title and content start
        orphan_text = ''  # Text between section number and title (likely exercise from prev section)
        if section_num in matched_same_line:
            title = matched_same_line[section_num][1]
            content_start_lidx = line_idx + 1
        else:
            title = ''
            content_start_lidx = line_idx + 1
            skipped = 0
            orphan_lines = []
            title_found = False
            for j in range(line_idx + 1, min(line_idx + 8, total_lines)):
                if not lines[j].strip():
                    skipped += 1
                    continue
                candidate = lines[j].strip()
                candidate = re.sub(r'\s*\.{5,}\s*\d*\s*$', '', candidate)
                if is_title_like(candidate):
                    title = candidate
                    content_start_lidx = j + 1
                    title_found = True
                    break
                # Non-title-like text before title = orphan exercise text
                if not title_found:
                    orphan_lines.append(candidate)
                if skipped >= 2:
                    break
            if orphan_lines:
                orphan_text = '\n'.join(orphan_lines)

        # Use TOC title when available (more reliable than content extraction)
        toc_title = toc_titles.get(section_num, '')
        if toc_title:
            title = toc_title
        elif not title:
            title = toc_title

        content_start_char = sum(len(l) + 1 for l in lines[:content_start_lidx])
        if idx + 1 < len(matched_indices):
            content_end_char = sum(len(l) + 1 for l in lines[:matched_indices[idx + 1]])
        else:
            content_end_char = len(content)

        section_content = content[content_start_char:content_end_char].strip()

        sections.append({
            'number': section_num,
            'title': title,
            'content': section_content,
            'orphan': orphan_text,  # Exercise text that belongs to previous section
        })

    # Post-process: attach orphan text to previous section
    for idx in range(1, len(sections)):
        if sections[idx].get('orphan'):
            sections[idx - 1]['content'] += '\n\n' + sections[idx]['orphan']
            del sections[idx]['orphan']
    for sec in sections:
        sec.pop('orphan', None)

    return sections


# ---------------------------------------------------------------------------
# Content Cleaning
# ---------------------------------------------------------------------------

def clean_content(content):
    """Strip form feeds, page numbers, collapse blank lines. No paragraph merging."""
    content = content.replace('\f', '')
    content = re.sub(r'\n\d{1,3}\n', '\n', content)
    content = re.sub(r'\n\d+\n---\n', '\n', content)
    content = re.sub(r'\n{3,}', '\n\n', content)

    lines = content.split('\n')
    cleaned = []
    for line in lines:
        line = line.rstrip()
        if re.match(r'^\s*\d{1,3}\s*$', line):
            continue
        if line:
            cleaned.append(line)

    return cleaned  # Return list of lines


# ---------------------------------------------------------------------------
# Code / Text Block Detection
# ---------------------------------------------------------------------------

def is_strong_code(line):
    """Line that definitively starts or is part of a code block."""
    s = line.strip()
    if not s:
        return False
    if s.startswith('#'):
        return True
    if s.startswith('/*') or s.startswith('*/'):
        return True
    if s in ('{', '}'):
        return True
    # Function calls/defs without Chinese
    if re.match(r'^[a-zA-Z_][a-zA-Z0-9_\[\]]*\s*\(', s) and not re.search(r'[\u4e00-\u9fff]', s):
        return True
    # Type declarations
    if re.match(r'^(int|char|float|double|void|long|short|unsigned|struct|enum|typedef|static|const|extern|register|auto|volatile)\s+', s):
        return True
    # Broken string start
    if re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*\s*\(\s*"[^"]*$', s):
        return True
    return False
    if s.startswith('#'):
        return True
    if s.startswith('/*') or s.startswith('*/'):
        return True
    if s in ('{', '}'):
        return True
    if re.match(r'^[a-zA-Z_][a-zA-Z0-9_\[\]]*\s*\(', s) and not re.search(r'[\u4e00-\u9fff]', s):
        return True
    if re.match(r'^(int|char|float|double|void|long|short|unsigned|struct|enum|typedef|static|const|extern|register|auto|volatile)\s+', s):
        return True
    return False

def is_code_line(line):
    s = line.strip()
    if not s:
        return False
    if is_strong_code(s):
        return True
    if s.endswith(';'):
        return True
    if s.endswith('*/') and not s.startswith('/*'):
        return True
    if re.match(r'^(if|else|for|while|do|switch|case|default|break|continue|return|goto)\b', s):
        return True
    if re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*\s*=', s):
        return True
    if re.match(r'^"[^"]*"', s) or re.match(r'^"[^"]*$', s) or re.match(r'^[^"]*"$', s):
        return True
    if re.match(r'^(printf|scanf|getchar|putchar|malloc|free|exit)\s*\(', s):
        return True
    if re.match(r'^(cc|a\.out|gcc|make)\b', s):
        return True
    if s in ('...', ');'):
        return True
    return False

def is_text_line(line):
    s = line.strip()
    if not s:
        return False
    if re.search(r'[\u4e00-\u9fff]', s):
        return True
    return False

def detect_blocks(lines):
    blocks = []
    in_code = False
    code_buf = []
    text_buf = []

    def flush_code():
        nonlocal in_code, code_buf
        if code_buf:
            blocks.append(('code', code_buf))
        in_code = False
        code_buf = []

    def flush_text():
        nonlocal text_buf
        if text_buf:
            blocks.append(('text', text_buf))
        text_buf = []

    for line in lines:
        s = line.strip()
        if not s:
            if in_code:
                flush_code()
            else:
                flush_text()
            continue

        if is_strong_code(s):
            flush_text()
            if not in_code:
                in_code = True
                code_buf = []
            code_buf.append(line)
        elif in_code:
            if is_text_line(s) and not is_code_line(s):
                flush_code()
                text_buf.append(line)
            else:
                code_buf.append(line)
        else:
            if is_code_line(s) and not is_text_line(s):
                flush_text()
                code_buf.append(line)
                in_code = True
            else:
                text_buf.append(line)

    flush_code()
    flush_text()
    return blocks


# ---------------------------------------------------------------------------
# HTML Generation
# ---------------------------------------------------------------------------

HTML = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{section_num} {section_title} - C语言教程</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            line-height: 1.9;
            background: #232A2E;
            color: #D3C6AA;
        }}
        .sidebar {{
            position: fixed;
            left: 0;
            top: 0;
            width: 260px;
            height: 100vh;
            background: #1C2126;
            border-right: 1px solid #3A4147;
            overflow-y: auto;
            overflow-x: hidden;
            z-index: 10;
            padding-bottom: 40px;
        }}
        .sidebar-header {{
            padding: 20px 16px 12px 16px;
            font-size: 15px;
            font-weight: 700;
            color: #A7C080;
            border-bottom: 1px solid #2D353B;
            position: sticky;
            top: 0;
            background: #1C2126;
            z-index: 2;
        }}
        .sidebar .chapter {{
            border-bottom: 1px solid #262C31;
        }}
        .sidebar .chapter-header {{
            display: flex;
            align-items: center;
            padding: 10px 16px;
            font-size: 13px;
            font-weight: 600;
            color: #D3C6AA;
            cursor: pointer;
            user-select: none;
            transition: background 0.15s;
        }}
        .sidebar .chapter-header:hover {{
            background: #262C31;
        }}
        .sidebar .chapter-header .arrow {{
            display: inline-block;
            width: 14px;
            font-size: 10px;
            color: #7A8478;
            transition: transform 0.2s;
            margin-right: 6px;
        }}
        .sidebar .chapter-header .arrow.rotated {{
            transform: rotate(-90deg);
        }}
        .sidebar .section-links {{
            overflow: hidden;
            transition: max-height 0.3s ease;
        }}
        .sidebar .section-links.hidden {{
            max-height: 0;
        }}
        .sidebar .section-link {{
            display: block;
            padding: 5px 16px 5px 30px;
            font-size: 12.5px;
            color: #7A8478;
            text-decoration: none;
            border-left: 2px solid transparent;
            transition: all 0.12s;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}
        .sidebar .section-link:hover {{
            color: #D3C6AA;
            background: #262C31;
            border-left-color: #4F585E;
        }}
        .sidebar .section-link.active {{
            color: #A7C080;
            background: #232A2E;
            border-left-color: #A7C080;
            font-weight: 600;
        }}
        .main {{
            margin-left: 260px;
            padding: 40px;
            max-width: 900px;
        }}
        .section-header {{
            border-left: 5px solid #A7C080;
            padding-left: 18px;
            margin-bottom: 36px;
        }}
        .section-number {{
            font-size: 13px;
            color: #A7C080;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1.5px;
        }}
        .section-title {{
            font-size: 30px;
            color: #D3C6AA;
            font-weight: 700;
            margin-top: 8px;
        }}
        .content {{
            font-size: 16px;
            background: #2D353B;
            padding: 36px;
            border-radius: 12px;
            box-shadow: 0 0 20px rgba(0,0,0,0.3);
        }}
        .content p {{
            margin-bottom: 14px;
        }}
        .content pre {{
            background: #343F44;
            color: #D3C6AA;
            padding: 20px;
            border-radius: 8px;
            overflow-x: auto;
            margin: 18px 0;
            font-family: "SF Mono", Consolas, "Liberation Mono", Menlo, monospace;
            font-size: 14px;
            line-height: 1.6;
            border: 1px solid #4F585E;
        }}
        .content pre code {{
            background: transparent;
            color: inherit;
            padding: 0;
        }}
        .content .kw {{ color: #83C092; font-weight: 500; }}
        .content .fn {{ color: #DBBC7F; }}
        .content .str {{ color: #E69875; }}
        .content .cm {{ color: #7A8478; font-style: italic; }}
        .content h2 {{
            font-size: 20px;
            color: #A7C080;
            margin: 28px 0 14px 0;
            border-bottom: 2px solid #4F585E;
            padding-bottom: 10px;
        }}
        .content h3 {{
            font-size: 17px;
            margin: 22px 0 10px 0;
        }}
        ul, ol {{ margin: 12px 0 12px 24px; }}
        li {{ margin-bottom: 8px; }}
        @media (max-width: 800px) {{
            .sidebar {{ display: none; }}
            .main {{ margin-left: 0; }}
        }}
    </style>
</head>
<body>
    <nav class="sidebar">
        <div class="sidebar-header">C 程序设计语言 — 目录</div>
        {sidebar_html}
    </nav>
    <main class="main">
        <div class="section-header">
            <div class="section-number">第 {chapter_display} 章</div>
            <h1 class="section-title">{section_num} {section_title}</h1>
        </div>
        <div class="content">
            {content_body}
        </div>
    </main>
    <script>
        (function() {{
            var chapters = document.querySelectorAll('.chapter');
            chapters.forEach(function(ch) {{
                var links = ch.querySelector('.section-links');
                var arrow = ch.querySelector('.arrow');
                if (!links) return;
                var hasActive = links.querySelector('.section-link.active');
                if (!hasActive) {{
                    links.style.maxHeight = '0px';
                    if (arrow) arrow.classList.add('rotated');
                }} else {{
                    links.style.maxHeight = links.scrollHeight + 'px';
                }}
                var header = ch.querySelector('.chapter-header');
                header.addEventListener('click', function() {{
                    if (links.style.maxHeight === '0px') {{
                        links.style.maxHeight = links.scrollHeight + 'px';
                        if (arrow) arrow.classList.remove('rotated');
                    }} else {{
                        links.style.maxHeight = '0px';
                        if (arrow) arrow.classList.add('rotated');
                    }}
                }});
            }});
            var active = document.querySelector('.section-link.active');
            if (active) {{
                active.scrollIntoView({{ block: 'center' }});
            }}
        }})();
    </script>
</body>
</html>'''


def escape_html(text):
    return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def highlight_syntax(code):
    keywords = [
        'int', 'char', 'float', 'double', 'void', 'long', 'short', 'unsigned', 'signed',
        'const', 'static', 'extern', 'register', 'sizeof', 'struct', 'union', 'enum',
        'typedef', 'auto', 'volatile',
        'if', 'else', 'for', 'while', 'do', 'break', 'continue', 'return', 'goto',
        'switch', 'case', 'default',
    ]
    functions = [
        'main', 'printf', 'scanf', 'getchar', 'putchar', 'strlen', 'strcpy', 'strcmp',
        'malloc', 'free', 'atoi', 'atof', 'feof', 'ferror', 'fopen', 'fclose',
        'fread', 'fwrite', 'fseek', 'getc', 'putc', 'exit',
    ]

    code = escape_html(code)

    code = re.sub(r'("(?:[^"\\]|\\.)*")', r'<span class="str">\1</span>', code)
    code = re.sub(r'(//.*$)', r'<span class="cm">\1</span>', code, flags=re.MULTILINE)
    code = re.sub(r'(/\*[\s\S]*?\*/)', r'<span class="cm">\1</span>', code)

    for kw in keywords:
        code = re.sub(rf'\b({kw})\b', rf'<span class="kw">{kw}</span>', code)
    for fn in functions:
        code = re.sub(rf'\b({fn})\b', rf'<span class="fn">{fn}</span>', code)

    return code


def merge_text_lines(lines):
    """Merge continuation text lines into paragraphs within a text block."""
    if not lines:
        return []
    sentence_end = set('。！？；：)》）"\'…—.')
    merged = []
    buf = []
    for line in lines:
        is_break = bool(re.match(r'^练习\s*\d+', line))
        if is_break:
            if buf:
                merged.append(''.join(buf))
                buf = []
            merged.append(line)
            continue
        if buf:
            last = buf[-1]
            last_char = last[-1] if last else ''
            if last_char and last_char not in sentence_end:
                buf.append(line)
            else:
                merged.append(''.join(buf))
                buf = [line]
        else:
            buf.append(line)
    if buf:
        merged.append(''.join(buf))
    return merged


def render_blocks(blocks):
    parts = []
    for btype, blines in blocks:
        if btype == 'code':
            code_text = '\n'.join(blines)
            code_text = highlight_syntax(code_text)
            parts.append(f'<pre><code>{code_text}</code></pre>')
        else:
            # Merge text lines into paragraphs
            paragraphs = merge_text_lines(blines)
            for para in paragraphs:
                parts.append(f'<p>{escape_html(para)}</p>')
    return '\n'.join(parts)


def build_section_tree(sections):
    """Build a tree: {chapter_key: {title, sections: [(num, title, filename), ...]}}"""
    tree = {}
    chapter_names = {str(i): f'第{i}章' for i in range(1, 9)}
    chapter_names.update({'A': '附录A', 'B': '附录B'})

    for sec in sections:
        parts = sec['number'].split('.')
        ch = parts[0]
        if ch not in tree:
            section_list = sections
            ch_sections = [s for s in section_list if s['number'].split('.')[0] == ch]
            tree[ch] = {
                'title': chapter_names.get(ch, ch),
                'sections': ch_sections,
            }
    return tree


def build_sidebar_html(tree, current_num, toc_titles):
    """Build sidebar navigation HTML."""
    parts = []
    # Sort chapters: 1-8, then A, B
    chapter_order = [str(i) for i in range(1, 9)] + ['A', 'B']

    for ch in chapter_order:
        if ch not in tree:
            continue
        chapter = tree[ch]
        title = chapter['title']
        sections = sorted(chapter['sections'], key=lambda s: _sort_key(s['number']))

        # Determine if this chapter contains current section
        current_ch = current_num.split('.')[0]
        is_active_chapter = (ch == current_ch)

        parts.append(f'<div class="chapter">')
        parts.append(
            f'<div class="chapter-header">'
            f'<span class="arrow">&#9660;</span>{escape_html(title)}'
            f'</div>'
        )

        parts.append(f'<div class="section-links">')

        for sec in sections:
            filename = sec['number'].replace('.', '_') + '.html'
            active_class = ' active' if sec['number'] == current_num else ''
            label = f'{sec["number"]} {sec["title"]}'
            parts.append(
                f'<a class="section-link{active_class}" href="{filename}">'
                f'{escape_html(label)}'
                f'</a>'
            )

        parts.append('</div>')  # section-links
        parts.append('</div>')  # chapter

    return '\n'.join(parts)


def _sort_key(num):
    """Sort section numbers naturally."""
    parts = num.split('.')
    return tuple(int(p) if p.isdigit() else ord(p[0]) * 1000 + int(p[1:]) if len(p) > 1 else ord(p[0]) for p in parts)


def generate_html(section, section_tree, toc_titles):
    parts = section['number'].split('.')
    chapter_display = parts[0]

    sidebar_html = build_sidebar_html(section_tree, section['number'], toc_titles)

    content = clean_content(section['content'])
    lines = content
    blocks = detect_blocks(lines)
    body = render_blocks(blocks)

    html = HTML.format(
        section_num=section['number'],
        section_title=escape_html(section['title']),
        chapter_display=chapter_display,
        sidebar_html=sidebar_html,
        content_body=body,
    )
    return html


# ---------------------------------------------------------------------------
# Entry Point
# ---------------------------------------------------------------------------

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    sections = parse_tutorial(INPUT_FILE)
    tree = build_section_tree(sections)

    for sec in sections:
        html = generate_html(sec, tree, {})
        safe_num = sec['number'].replace('.', '_')
        filename = f'{OUTPUT_DIR}/{safe_num}.html'
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html)

    print(f"Generated {len(sections)} section files")


if __name__ == '__main__':
    main()
