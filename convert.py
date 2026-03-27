#!/usr/bin/env python3
"""
Markdown to Medium-style HTML Converter
Converts markdown files to clean, Medium-style HTML pages
"""

import re
import sys
from pathlib import Path

def escape_html(text):
    """Escape HTML special characters"""
    return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

def parse_inline(text):
    """Parse inline markdown: bold, italic, code, links"""
    # Code (must be first)
    text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
    # Bold and italic
    text = re.sub(r'\*\*\*([^*]+)\*\*\*', r'<strong><em>\1</em></strong>', text)
    text = re.sub(r'___([^_]+)___', r'<strong><em>\1</em></strong>', text)
    # Bold
    text = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'__([^_]+)__', r'<strong>\1</strong>', text)
    # Italic
    text = re.sub(r'\*([^*]+)\*', r'<em>\1</em>', text)
    text = re.sub(r'_([^_]+)_', r'<em>\1</em>', text)
    # Links
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', text)
    return text

def markdown_to_html(md_content):
    """Convert markdown to HTML"""
    lines = md_content.split('\n')
    html_lines = []
    i = 0
    
    in_code_block = False
    code_block_content = []
    code_block_lang = ''
    
    in_table = False
    table_rows = []
    
    in_list = False
    list_type = None
    list_items = []
    
    while i < len(lines):
        line = lines[i]
        
        # Code blocks
        if line.startswith('```'):
            if in_code_block:
                # End code block
                code_html = '\n'.join(code_block_content)
                code_html = escape_html(code_html)
                html_lines.append(f'<pre><code class="language-{code_block_lang}">{code_html}</code></pre>')
                code_block_content = []
                code_block_lang = ''
                in_code_block = False
            else:
                # Start code block
                in_code_block = True
                code_block_lang = line[3:].strip() or 'text'
            i += 1
            continue
        
        if in_code_block:
            code_block_content.append(line)
            i += 1
            continue
        
        # Empty line
        if not line.strip():
            if in_list:
                if list_type == 'ul':
                    html_lines.append('<ul>' + ''.join(list_items) + '</ul>')
                else:
                    html_lines.append('<ol>' + ''.join(list_items) + '</ol>')
                list_items = []
                in_list = False
                list_type = None
            if in_table and table_rows:
                html_lines.append(render_table(table_rows))
                table_rows = []
                in_table = False
            i += 1
            continue
        
        # Tables
        if '|' in line and not line.startswith('#') and not line.startswith('-'):
            in_table = True
            table_rows.append(line)
            i += 1
            continue
        elif in_table and not line.strip().startswith('|'):
            html_lines.append(render_table(table_rows))
            table_rows = []
            in_table = False
        
        # Headers
        if line.startswith('# '):
            title = parse_inline(line[2:])
            html_lines.append(f'<h1>{title}</h1>')
            i += 1
            continue
        elif line.startswith('## '):
            title = parse_inline(line[3:])
            html_lines.append(f'<h2>{title}</h2>')
            i += 1
            continue
        elif line.startswith('### '):
            title = parse_inline(line[4:])
            html_lines.append(f'<h3>{title}</h3>')
            i += 1
            continue
        elif line.startswith('#### '):
            title = parse_inline(line[5:])
            html_lines.append(f'<h4>{title}</h4>')
            i += 1
            continue
        
        # Horizontal rule
        if line.strip() == '---' or line.strip() == '***':
            html_lines.append('<hr>')
            i += 1
            continue
        
        # Blockquote
        if line.startswith('>'):
            quote_lines = []
            while i < len(lines) and lines[i].startswith('>'):
                quote_lines.append(lines[i][1:].strip())
                i += 1
            quote_text = ' '.join(quote_lines)
            quote_text = parse_inline(quote_text)
            html_lines.append(f'<blockquote><p>{quote_text}</p></blockquote>')
            continue
        
        # Lists
        if line.strip().startswith('- ') or line.strip().startswith('* '):
            if not in_list or list_type != 'ul':
                if in_list:
                    if list_type == 'ol':
                        html_lines.append('<ol>' + ''.join(list_items) + '</ol>')
                    else:
                        html_lines.append('<ul>' + ''.join(list_items) + '</ul>')
                    list_items = []
                in_list = True
                list_type = 'ul'
            item_text = line.strip()[2:]
            item_text = parse_inline(item_text)
            list_items.append(f'<li>{item_text}</li>')
            i += 1
            continue
        
        if re.match(r'^\d+\.\s', line.strip()):
            if not in_list or list_type != 'ol':
                if in_list:
                    if list_type == 'ul':
                        html_lines.append('<ul>' + ''.join(list_items) + '</ul>')
                    else:
                        html_lines.append('<ol>' + ''.join(list_items) + '</ol>')
                    list_items = []
                in_list = True
                list_type = 'ol'
            item_text = re.sub(r'^\d+\.\s', '', line.strip())
            item_text = parse_inline(item_text)
            list_items.append(f'<li>{item_text}</li>')
            i += 1
            continue
        
        # Regular paragraph
        if line.strip():
            text = parse_inline(line)
            html_lines.append(f'<p>{text}</p>')
        
        i += 1
    
    # Close any open blocks
    if in_list:
        if list_type == 'ul':
            html_lines.append('<ul>' + ''.join(list_items) + '</ul>')
        else:
            html_lines.append('<ol>' + ''.join(list_items) + '</ol>')
    if in_table and table_rows:
        html_lines.append(render_table(table_rows))
    if in_code_block:
        code_html = '\n'.join(code_block_content)
        code_html = escape_html(code_html)
        html_lines.append(f'<pre><code class="language-{code_block_lang}">{code_html}</code></pre>')
    
    return '\n'.join(html_lines)

def render_table(rows):
    """Render markdown table to HTML"""
    if len(rows) < 2:
        return ''
    
    # Parse header
    headers = [cell.strip() for cell in rows[0].split('|') if cell.strip()]
    
    # Skip separator row
    data_rows = rows[2:] if len(rows) > 2 else []
    
    html = '<table>\n<thead>\n<tr>'
    for header in headers:
        header = parse_inline(header)
        html += f'<th>{header}</th>'
    html += '</tr>\n</thead>\n<tbody>\n'
    
    for row in data_rows:
        cells = [cell.strip() for cell in row.split('|') if cell.strip() or cell == '']
        # Handle empty cells properly
        cells = [cell for cell in row.split('|')]
        cells = [cell.strip() for cell in cells[1:-1] if cells[0] == '' or True]
        cells = [cell for cell in row.split('|')[1:-1]]
        cells = [cell.strip() for cell in cells]
        
        if cells:
            html += '<tr>'
            for cell in cells:
                cell = parse_inline(cell)
                html += f'<td>{cell}</td>'
            html += '</tr>\n'
    
    html += '</tbody>\n</table>'
    return html

def generate_html_page(title, content_html, current_page):
    """Generate full HTML page with Medium-style design"""
    
    nav_links = [
        ('index.html', '首页'),
        ('FINAL_REPORT.html', '综合报告'),
        ('phase2-geospatial.html', 'Phase 2: 地理空间'),
        ('phase2-geospatial-analysis.html', 'Phase 2: 分析'),
        ('phase3-market.html', 'Phase 3: 市场'),
        ('phase3-market-scan.html', 'Phase 3: 扫描'),
        ('CONTRACT.html', '合同'),
    ]
    
    nav_html = ''
    for href, text in nav_links:
        active = ' class="active"' if href == current_page else ''
        nav_html += f'<li><a href="{href}"{active}>{text}</a></li>'
    
    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - Geo + AI Research</title>
    <link href="https://fonts.googleapis.com/css2?family=Merriweather:ital,wght@0,300;0,400;0,700;1,400&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/github.min.css">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/languages/python.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/languages/sql.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/languages/json.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/languages/bash.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/languages/javascript.min.js"></script>
    <style>
        :root {{
            --font-serif: 'Merriweather', Georgia, serif;
            --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            --color-text: #292929;
            --color-text-secondary: #757575;
            --color-border: #e6e6e6;
            --color-bg: #ffffff;
            --color-bg-secondary: #fafafa;
            --color-accent: #1a8917;
            --color-accent-hover: #0f730c;
            --max-width: 740px;
            --nav-height: 60px;
        }}

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: var(--font-serif);
            font-size: 18px;
            line-height: 1.8;
            color: var(--color-text);
            background: var(--color-bg);
            -webkit-font-smoothing: antialiased;
        }}

        /* Navigation */
        .navbar {{
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            height: var(--nav-height);
            background: var(--color-bg);
            border-bottom: 1px solid var(--color-border);
            z-index: 1000;
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0 24px;
        }}

        .nav-brand {{
            font-family: var(--font-sans);
            font-weight: 700;
            font-size: 20px;
            color: var(--color-text);
            text-decoration: none;
        }}

        .nav-menu {{
            display: flex;
            gap: 24px;
            list-style: none;
        }}

        .nav-menu a {{
            font-family: var(--font-sans);
            font-size: 14px;
            font-weight: 500;
            color: var(--color-text-secondary);
            text-decoration: none;
            transition: color 0.2s;
        }}

        .nav-menu a:hover {{
            color: var(--color-text);
        }}

        .nav-menu a.active {{
            color: var(--color-accent);
        }}

        .nav-toggle {{
            display: none;
            background: none;
            border: none;
            cursor: pointer;
            padding: 8px;
        }}

        .nav-toggle span {{
            display: block;
            width: 24px;
            height: 2px;
            background: var(--color-text);
            margin: 5px 0;
            transition: 0.3s;
        }}

        /* Main Content */
        .main-content {{
            max-width: var(--max-width);
            margin: 0 auto;
            padding: calc(var(--nav-height) + 48px) 24px 80px;
        }}

        /* Typography */
        h1 {{
            font-family: var(--font-sans);
            font-size: 42px;
            font-weight: 700;
            line-height: 1.2;
            margin-bottom: 24px;
            letter-spacing: -0.02em;
        }}

        h2 {{
            font-family: var(--font-sans);
            font-size: 28px;
            font-weight: 600;
            line-height: 1.3;
            margin-top: 48px;
            margin-bottom: 20px;
            letter-spacing: -0.01em;
        }}

        h3 {{
            font-family: var(--font-sans);
            font-size: 22px;
            font-weight: 600;
            line-height: 1.4;
            margin-top: 36px;
            margin-bottom: 16px;
        }}

        h4 {{
            font-family: var(--font-sans);
            font-size: 18px;
            font-weight: 600;
            line-height: 1.4;
            margin-top: 28px;
            margin-bottom: 12px;
        }}

        p {{
            margin-bottom: 24px;
        }}

        a {{
            color: var(--color-accent);
            text-decoration: underline;
            text-underline-offset: 3px;
        }}

        a:hover {{
            color: var(--color-accent-hover);
        }}

        /* Lists */
        ul, ol {{
            margin-bottom: 24px;
            padding-left: 32px;
        }}

        li {{
            margin-bottom: 8px;
        }}

        /* Blockquote */
        blockquote {{
            border-left: 3px solid var(--color-text);
            padding-left: 24px;
            margin: 32px 0;
            font-style: italic;
            color: var(--color-text-secondary);
        }}

        blockquote p:last-child {{
            margin-bottom: 0;
        }}

        /* Code */
        code {{
            font-family: 'SF Mono', Monaco, monospace;
            font-size: 15px;
            background: var(--color-bg-secondary);
            padding: 2px 6px;
            border-radius: 4px;
            color: var(--color-text);
        }}

        pre {{
            background: var(--color-bg-secondary);
            padding: 20px 24px;
            border-radius: 8px;
            overflow-x: auto;
            margin: 24px 0;
            border: 1px solid var(--color-border);
        }}

        pre code {{
            background: none;
            padding: 0;
            font-size: 14px;
            line-height: 1.6;
        }}

        /* Tables */
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 32px 0;
            font-size: 15px;
        }}

        th, td {{
            padding: 12px 16px;
            text-align: left;
            border-bottom: 1px solid var(--color-border);
        }}

        th {{
            font-family: var(--font-sans);
            font-weight: 600;
            background: var(--color-bg-secondary);
            font-size: 14px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}

        tr:hover {{
            background: var(--color-bg-secondary);
        }}

        /* Horizontal Rule */
        hr {{
            border: none;
            height: 1px;
            background: var(--color-border);
            margin: 48px 0;
        }}

        /* Strong and Emphasis */
        strong {{
            font-weight: 700;
        }}

        em {{
            font-style: italic;
        }}

        /* Images */
        img {{
            max-width: 100%;
            height: auto;
            border-radius: 4px;
            margin: 24px 0;
        }}

        /* Article Meta */
        .article-meta {{
            font-family: var(--font-sans);
            font-size: 14px;
            color: var(--color-text-secondary);
            margin-bottom: 32px;
        }}

        /* Responsive */
        @media (max-width: 768px) {{
            .nav-menu {{
                display: none;
                position: absolute;
                top: var(--nav-height);
                left: 0;
                right: 0;
                background: var(--color-bg);
                flex-direction: column;
                padding: 16px 24px;
                border-bottom: 1px solid var(--color-border);
                gap: 16px;
            }}

            .nav-menu.active {{
                display: flex;
            }}

            .nav-toggle {{
                display: block;
            }}

            h1 {{
                font-size: 32px;
            }}

            h2 {{
                font-size: 24px;
            }}

            h3 {{
                font-size: 20px;
            }}

            body {{
                font-size: 17px;
            }}

            table {{
                font-size: 13px;
            }}

            th, td {{
                padding: 8px 12px;
            }}
        }}

        /* Print Styles */
        @media print {{
            .navbar {{
                display: none;
            }}

            .main-content {{
                padding-top: 24px;
            }}

            body {{
                font-size: 12pt;
                line-height: 1.5;
            }}

            h1 {{
                font-size: 24pt;
            }}

            h2 {{
                font-size: 18pt;
            }}

            a {{
                text-decoration: none;
                color: var(--color-text);
            }}
        }}
    </style>
</head>
<body>
    <nav class="navbar">
        <a href="index.html" class="nav-brand">Geo + AI Research</a>
        <button class="nav-toggle" onclick="toggleMenu()">
            <span></span>
            <span></span>
            <span></span>
        </button>
        <ul class="nav-menu" id="navMenu">
            {nav_html}
        </ul>
    </nav>

    <main class="main-content">
        <h1>{title}</h1>
        {content_html}
    </main>

    <script>
        function toggleMenu() {{
            document.getElementById('navMenu').classList.toggle('active');
        }}

        // Highlight current page in nav
        const currentPage = window.location.pathname.split('/').pop() || 'index.html';
        document.querySelectorAll('.nav-menu a').forEach(link => {{
            if (link.getAttribute('href') === currentPage) {{
                link.classList.add('active');
            }}
        }});

        // Initialize syntax highlighting
        hljs.highlightAll();
    </script>
</body>
</html>'''

def convert_file(input_path, output_path):
    """Convert a single markdown file to HTML"""
    with open(input_path, 'r', encoding='utf-8') as f:
        md_content = f.read()
    
    # Extract title from first h1 or use filename
    title_match = re.search(r'^# (.+)$', md_content, re.MULTILINE)
    title = title_match.group(1) if title_match else Path(input_path).stem
    
    # Convert markdown to HTML
    content_html = markdown_to_html(md_content)
    
    # Generate full page
    current_page = Path(output_path).name
    full_html = generate_html_page(title, content_html, current_page)
    
    # Write output
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(full_html)
    
    print(f"Converted: {input_path} -> {output_path}")

def main():
    """Main entry point"""
    base_dir = Path('/Users/joez/.openclaw-coder/workspace/memory/projects/geo-ai-research')
    
    files_to_convert = [
        'phase2-geospatial.md',
        'phase2-geospatial-analysis.md',
        'phase3-market.md',
        'phase3-market-scan.md',
        'FINAL_REPORT.md',
        'CONTRACT.md',
    ]
    
    for md_file in files_to_convert:
        input_path = base_dir / md_file
        output_path = base_dir / md_file.replace('.md', '.html')
        
        if input_path.exists():
            convert_file(input_path, output_path)
        else:
            print(f"Warning: {input_path} not found")
    
    print("\nConversion complete!")

if __name__ == '__main__':
    main()
