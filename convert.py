#!/usr/bin/env python3
"""
Markdown to Medium-style HTML Converter
Converts markdown files to Medium-style HTML pages with navigation.
"""

import re
import os
import sys
from pathlib import Path

def parse_markdown(md_content):
    """Parse markdown content and convert to HTML."""
    html = md_content
    
    # Escape HTML special characters in code blocks first
    code_blocks = []
    def save_code_block(match):
        lang = match.group(1) or ''
        code = match.group(2)
        # Escape HTML special characters
        code = code.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        code_blocks.append((lang, code))
        return f"CODEBLOCK{len(code_blocks)-1}"
    
    # Extract code blocks
    html = re.sub(r'```(\w*)\n(.*?)```', save_code_block, html, flags=re.DOTALL)
    
    # Convert headers
    html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
    html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
    html = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)
    
    # Convert bold and italic
    html = re.sub(r'\*\*\*(.+?)\*\*\*', r'<strong><em>\1</em></strong>', html)
    html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
    html = re.sub(r'\*(.+?)\*', r'<em>\1</em>', html)
    
    # Convert horizontal rules
    html = re.sub(r'^---+$', '<hr>', html, flags=re.MULTILINE)
    
    # Convert tables
    def convert_table(match):
        lines = match.group(0).strip().split('\n')
        if len(lines) < 2:
            return match.group(0)
        
        # Check if second line is separator
        if not re.match(r'^[\|\-\:\s]+$', lines[1]):
            return match.group(0)
        
        html_table = '<table>\n<thead>\n<tr>'
        # Parse header
        headers = [cell.strip() for cell in lines[0].split('|') if cell.strip()]
        for header in headers:
            html_table += f'<th>{header}</th>'
        html_table += '</tr>\n</thead>\n<tbody>'
        
        # Parse body rows
        for line in lines[2:]:
            if line.strip():
                html_table += '\n<tr>'
                cells = [cell.strip() for cell in line.split('|') if cell.strip() or cell == '']
                # Handle empty cells properly
                row_cells = []
                for cell in line.split('|'):
                    cell = cell.strip()
                    if cell or row_cells:  # Skip leading empty
                        row_cells.append(cell)
                if row_cells and not row_cells[-1]:
                    row_cells = row_cells[:-1]  # Remove trailing empty
                
                for cell in row_cells:
                    html_table += f'<td>{cell}</td>'
                html_table += '</tr>'
        
        html_table += '\n</tbody>\n</table>'
        return html_table
    
    # Match table blocks
    html = re.sub(r'(\|[^\n]+\|\n\|[-\:\|\s]+\|\n(?:\|[^\n]+\|\n?)+)', convert_table, html)
    
    # Convert blockquotes
    def convert_blockquote(match):
        lines = match.group(0).strip().split('\n')
        content = '\n'.join(line.lstrip('>').strip() for line in lines)
        return f'<blockquote>\n{content}\n</blockquote>'
    
    html = re.sub(r'(^\> .+\n?)+', convert_blockquote, html, flags=re.MULTILINE)
    
    # Convert unordered lists
    def convert_ul(match):
        items = match.group(0).strip().split('\n')
        html_list = '<ul>\n'
        for item in items:
            item_content = re.sub(r'^[\s]*[-\*\+]\s+', '', item)
            if item_content:
                html_list += f'<li>{item_content}</li>\n'
        html_list += '</ul>'
        return html_list
    
    html = re.sub(r'(^[\s]*[-\*\+]\s+.+\n?)+', convert_ul, html, flags=re.MULTILINE)
    
    # Convert ordered lists
    def convert_ol(match):
        items = match.group(0).strip().split('\n')
        html_list = '<ol>\n'
        for item in items:
            item_content = re.sub(r'^[\s]*\d+\.\s+', '', item)
            if item_content:
                html_list += f'<li>{item_content}</li>\n'
        html_list += '</ol>'
        return html_list
    
    html = re.sub(r'(^[\s]*\d+\.\s+.+\n?)+', convert_ol, html, flags=re.MULTILINE)
    
    # Convert inline code (after code blocks)
    html = re.sub(r'`([^`]+)`', r'<code>\1</code>', html)
    
    # Convert links
    html = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', html)
    
    # Restore code blocks
    for i, (lang, code) in enumerate(code_blocks):
        html = html.replace(f'CODEBLOCK{i}', f'<pre><code class="language-{lang}">{code}</code></pre>')
    
    # Wrap paragraphs
    paragraphs = html.split('\n\n')
    new_paragraphs = []
    for p in paragraphs:
        p = p.strip()
        if p and not p.startswith('<') and not p.startswith('CODEBLOCK'):
            p = f'<p>{p}</p>'
        new_paragraphs.append(p)
    
    html = '\n\n'.join(new_paragraphs)
    
    # Clean up any remaining CODEBLOCK placeholders
    for i in range(len(code_blocks)):
        if f'CODEBLOCK{i}' in html:
            lang, code = code_blocks[i]
            html = html.replace(f'CODEBLOCK{i}', f'<pre><code class="language-{lang}">{code}</code></pre>')
    
    return html


def extract_title(md_content):
    """Extract title from markdown content."""
    match = re.search(r'^# (.+)$', md_content, re.MULTILINE)
    if match:
        return match.group(1)
    return "Untitled"


def extract_meta(md_content):
    """Extract meta information from markdown content."""
    lines = md_content.split('\n')
    meta_parts = []
    
    for line in lines[:10]:
        if line.startswith('- **') and '**:' in line:
            # Clean up markdown formatting
            clean_line = re.sub(r'\*\*', '', line).strip('- ').strip()
            if clean_line:
                meta_parts.append(clean_line)
    
    if meta_parts:
        return ' | '.join(meta_parts[:3])  # Limit to first 3 meta items
    return ""


def convert_file(input_path, output_path, template_path):
    """Convert a single markdown file to HTML."""
    # Read template
    with open(template_path, 'r', encoding='utf-8') as f:
        template = f.read()
    
    # Read markdown
    with open(input_path, 'r', encoding='utf-8') as f:
        md_content = f.read()
    
    # Extract title and meta
    title = extract_title(md_content)
    meta = extract_meta(md_content)
    
    # Convert content
    content = parse_markdown(md_content)
    
    # Fill template
    html = template.replace('{{title}}', title)
    html = html.replace('{{meta}}', meta)
    html = html.replace('{{content}}', content)
    
    # Write output
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"Converted: {input_path} -> {output_path}")


def main():
    """Main entry point."""
    # Get the directory of this script
    script_dir = Path(__file__).parent
    
    # Files to convert
    files = [
        'phase1-perplexity-computer.md',
        'phase1-claude-cowork.md',
        'phase1-tencent-workbuddy.md',
        'phase1-github-copilot.md',
        'phase1-cursor.md',
        'phase1-devin.md'
    ]
    
    template_path = script_dir / 'template.html'
    
    for filename in files:
        input_path = script_dir / filename
        if input_path.exists():
            output_path = script_dir / filename.replace('.md', '.html')
            convert_file(input_path, output_path, template_path)
        else:
            print(f"Warning: {input_path} not found")
    
    print("\nConversion complete!")


if __name__ == '__main__':
    main()
