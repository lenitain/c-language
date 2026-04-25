#!/usr/bin/env python3
import re

def parse_tutorial(input_file):
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()

    content = re.sub(r'\n\d+\n---\n', '\n', content)

    sections = []
    section_pattern = re.compile(r'^(\d+(?:\.\d+)*)\.\s*(.+?)\s*$', re.MULTILINE)
    matches = list(section_pattern.finditer(content))

    for i, match in enumerate(matches):
        section_num = match.group(1)
        section_title = match.group(2).strip()
        start_pos = match.end()
        end_pos = matches[i+1].start() if i+1 < len(matches) else len(content)
        section_content = content[start_pos:end_pos].strip()

        section_title = re.sub(r'\s*\.\.{5,}\s*\d*\s*$', '', section_title)

        parts = section_num.split('.')
        # Accept chapter sections (1.1, 2.3) and subsections (1.5.1, 1.5.2, 4.11.1, 4.11.2)
        if len(parts) >= 2 and len(parts) <= 3:
            sections.append({
                'number': section_num,
                'title': section_title,
                'content': section_content
            })

    return sections

def clean_content(content):
    content = re.sub(r'\n\d+\n---\n', '\n', content)
    content = re.sub(r'\n\d+\n', '\n', content)
    content = re.sub(r'\n{3,}', '\n\n', content)
    lines = content.split('\n')
    cleaned_lines = []
    for line in lines:
        line = re.sub(r'^(\d+)\s*$', '', line)
        line = line.rstrip()
        if line:
            cleaned_lines.append(line)
    return '\n'.join(cleaned_lines)

def is_code_line(line):
    patterns = [
        r'^\s*#\s*include',
        r'^\s*#\s*define',
        r'^\s*#\s*if',
        r'^\s*#\s*else',
        r'^\s*#\s*endif',
        r'^\s*main\s*\(',
        r'^\s*int\s+main\s*\(',
        r'^\s*void\s+main\s*\(',
        r'^\s*printf\s*\(',
        r'^\s*scanf\s*\(',
        r'^\s*if\s*\(',
        r'^\s*else\s*\{',
        r'^\s*for\s*\(',
        r'^\s*while\s*\(',
        r'^\s*do\s*\{',
        r'^\s*return\s+',
        r'^\s*\{',
        r'^\s*\}',
        r'^\s*/\*',
        r'^\s*\*/',
        r'^\s*\*\s',
        r'^\s*//',
        r'^\s*int\s+[a-zA-Z_]',
        r'^\s*char\s+[a-zA-Z_]',
        r'^\s*float\s+[a-zA-Z_]',
        r'^\s*double\s+[a-zA-Z_]',
        r'^\s*void\s+[a-zA-Z_]',
        r'^\s*long\s+[a-zA-Z_]',
        r'^\s*short\s+[a-zA-Z_]',
        r'^\s*struct\s+[a-zA-Z_]',
        r'^\s*typedef\s+',
        r'^\s*enum\s+[a-zA-Z_]',
        r'^\s*[a-zA-Z_][a-zA-Z0-9_]*\s*=\s*[^{}]',
        r'^\s*[a-zA-Z_][a-zA-Z0-9_]*\s*\(\s*[a-zA-Z_*]',
        r'^\s*\"[^\"]*\"',
        r'^\s*cc\s+',
        r'^\s*a\.out',
        r'^\s*\$',
        r'^\s*>\s*',
        r'^\s*<\s*',
    ]
    for p in patterns:
        if re.match(p, line):
            return True
    return False

def escape_html(text):
    return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

def highlight_syntax(code):
    keywords = ['int', 'char', 'float', 'double', 'void', 'long', 'short', 'unsigned', 'signed', 'const', 'static', 'extern', 'register', 'sizeof', 'struct', 'union', 'enum', 'typedef', 'auto', 'volatile', 'if', 'else', 'for', 'while', 'do', 'break', 'continue', 'return', 'goto', 'switch', 'case', 'default']
    functions = ['main', 'printf', 'scanf', 'getchar', 'putchar', 'strlen', 'strcpy', 'strcmp', 'malloc', 'free', 'atoi', 'atof', 'feof', 'ferror', 'fopen', 'fclose', 'fread', 'fwrite', 'fseek', 'getc', 'putc', 'exit']

    code = escape_html(code)

    code = re.sub(r'("(?:[^"\\]|\\.)*")', r'<span class="str">\1</span>', code)
    code = re.sub(r'(//.*$)', r'<span class="cm">\1</span>', code, flags=re.MULTILINE)
    code = re.sub(r'(/\*[\s\S]*?\*/)', r'<span class="cm">\1</span>', code)

    for kw in keywords:
        code = re.sub(rf'\b({kw})\b', rf'<span class="kw">{kw}</span>', code)
    for fn in functions:
        code = re.sub(rf'\b({fn})\b', rf'<span class="fn">{fn}</span>', code)

    return code

def generate_html(section):
    parts = section['number'].split('.')
    chapter = parts[0]

    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{section['number']} {section['title']} - C语言教程</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            line-height: 1.9;
            color: #333;
            max-width: 850px;
            margin: 0 auto;
            padding: 40px 20px;
            background: #fafafa;
        }}
        .section-header {{
            border-left: 5px solid #00599A;
            padding-left: 18px;
            margin-bottom: 36px;
        }}
        .section-number {{
            font-size: 13px;
            color: #00599A;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1.5px;
        }}
        .section-title {{
            font-size: 30px;
            color: #1a1a1a;
            font-weight: 700;
            margin-top: 8px;
        }}
        .content {{
            font-size: 16px;
            background: white;
            padding: 36px;
            border-radius: 12px;
            box-shadow: 0 2px 12px rgba(0,0,0,0.08);
        }}
        .content p {{
            margin-bottom: 14px;
            color: #D3C6AA;
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
            color: #D3C6AA;
            margin: 22px 0 10px 0;
        }}
        ul, ol {{ margin: 12px 0 12px 24px; }}
        li {{ margin-bottom: 8px; }}
        .note {{
            background: #2D353B;
            border-left: 4px solid #A7C080;
            padding: 14px 18px;
            margin: 18px 0;
            border-radius: 0 8px 8px 0;
        }}
        body {{
            background: #232A2E;
        }}
        .content {{
            background: #2D353B;
            box-shadow: 0 0 20px rgba(0,0,0,0.3);
        }}
        .section-header {{
            border-left-color: #A7C080;
        }}
        .section-number {{
            color: #A7C080;
        }}
        .section-title {{
            color: #D3C6AA;
        }}
    </style>
</head>
<body>
    <div class="section-header">
        <div class="section-number">第 {chapter} 章</div>
        <h1 class="section-title">{section['number']} {section['title']}</h1>
    </div>
    <div class="content">
'''

    content = clean_content(section['content'])
    lines = content.split('\n')
    in_code = False
    code_lines = []

    for line in lines:
        if is_code_line(line):
            if not in_code:
                in_code = True
                code_lines = []
            code_lines.append(line)
        else:
            if in_code:
                code_text = '\n'.join(code_lines)
                code_text = highlight_syntax(code_text)
                html += f'<pre><code>{code_text}</code></pre>\n'
                in_code = False
                code_lines = []
            html += f'<p>{escape_html(line)}</p>\n'

    if in_code:
        code_text = '\n'.join(code_lines)
        code_text = highlight_syntax(code_text)
        html += f'<pre><code>{code_text}</code></pre>\n'

    html += '''    </div>
</body>
</html>'''
    return html

def main():
    import os
    os.makedirs('/home/pilot/.cloned/d1ee2/sections', exist_ok=True)
    sections = parse_tutorial('/home/pilot/.cloned/d1ee2/c_tutorial.txt')

    for section in sections:
        html = generate_html(section)
        safe_num = section['number'].replace('.', '_')
        filename = f"/home/pilot/.cloned/d1ee2/sections/{safe_num}.html"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html)

    print(f"Generated {len(sections)} section files")

if __name__ == '__main__':
    main()
