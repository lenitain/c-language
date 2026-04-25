#!/usr/bin/env python3
"""Regenerate all section HTML files using the improved generate_html logic."""

from generate_html import parse_tutorial, generate_html
import os

OUTPUT_DIR = '/home/pilot/.cloned/d1ee2/sections'
INPUT_FILE = '/home/pilot/.cloned/d1ee2/c_tutorial.txt'

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    sections = parse_tutorial(INPUT_FILE)

    for sec in sections:
        html = generate_html(sec)
        safe_num = sec['number'].replace('.', '_')
        filename = f'{OUTPUT_DIR}/{safe_num}.html'
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html)

    print(f"Generated {len(sections)} section files")

if __name__ == '__main__':
    main()
