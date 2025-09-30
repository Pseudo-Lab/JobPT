import os
import re
import html
import unicodedata
import matplotlib.pyplot as plt
from matplotlib import font_manager


def normalize_text(text):
    if not text:
        return ""
    normalized = unicodedata.normalize('NFC', str(text))
    normalized = normalized.replace('\r\n', '\n').replace('\r', '\n')
    return normalized


def detect_language(text):
    if not text:
        return 'en'

    normalized = normalize_text(text)
    hangul_count = sum(1 for ch in normalized if '\uac00' <= ch <= '\ud7a3')
    latin_count = sum(1 for ch in normalized if ch.isascii() and ch.isalpha())

    if hangul_count == 0 and latin_count == 0:
        return 'en'

    if hangul_count >= 50 and hangul_count >= latin_count:
        return 'ko'
    if hangul_count >= latin_count * 2 and hangul_count >= 20:
        return 'ko'
    if hangul_count > 0 and latin_count == 0:
        return 'ko'
    return 'en'


def configure_plot_fonts(language):
    if language != 'ko':
        return (None, None)

    preferred_fonts = [
        'Malgun Gothic',
        'MalgunGothic',
        'AppleGothic',
        'NanumGothic',
        'NanumBarunGothic',
        'Noto Sans CJK KR',
        'Noto Sans KR'
    ]

    candidate_paths = [
        r'C:\\Windows\\Fonts\\malgun.ttf',
        r'C:\\Windows\\Fonts\\malgunbd.ttf',
        '/System/Library/Fonts/AppleSDGothicNeo.ttc',
        '/System/Library/Fonts/AppleGothic.ttf',
        '/Library/Fonts/AppleSDGothicNeo.ttf',
        '/usr/share/fonts/truetype/nanum/NanumGothic.ttf',
        '/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc',
        '/usr/share/fonts/truetype/noto/NotoSansKR-Regular.otf'
    ]

    previous_family = plt.rcParams.get('font.family')
    font_prop = None

    available_fonts = {font.name for font in font_manager.fontManager.ttflist}
    for font_name in preferred_fonts:
        if font_name in available_fonts:
            plt.rcParams['font.family'] = [font_name]
            plt.rcParams['axes.unicode_minus'] = False
            font_prop = font_manager.FontProperties(family=font_name)
            return (previous_family, font_prop)

    for path in candidate_paths:
        if os.path.exists(path):
            try:
                font_manager.fontManager.addfont(path)
                font_prop = font_manager.FontProperties(fname=path)
                plt.rcParams['font.family'] = [font_prop.get_name()]
                plt.rcParams['axes.unicode_minus'] = False
                return (previous_family, font_prop)
            except Exception:
                continue

    plt.rcParams['axes.unicode_minus'] = False
    return (previous_family, None)


def restore_plot_fonts(previous_settings):
    previous_family, _ = previous_settings if previous_settings else (None, None)
    if previous_family is not None:
        plt.rcParams['font.family'] = previous_family


def render_markdown(text):
    if not text:
        return ''

    try:
        import markdown
        extensions = ['extra', 'sane_lists', 'codehilite', 'nl2br']
        return markdown.markdown(text, extensions=extensions)
    except Exception:
        pass

    try:
        import markdown2
        extras = ['fenced-code-blocks', 'tables', 'strike', 'code-friendly', 'cuddled-lists']
        return markdown2.markdown(text, extras=extras)
    except Exception:
        pass

    return basic_markdown_to_html(text)


def basic_markdown_to_html(text):
    lines = text.splitlines()
    html_lines = []
    in_list = False
    in_code = False
    code_language = ''
    table_buffer = []

    def close_list():
        nonlocal in_list
        if in_list:
            html_lines.append('</ul>')
            in_list = False

    def close_code():
        nonlocal in_code
        if in_code:
            html_lines.append('</code></pre>')
            in_code = False

    def flush_table():
        nonlocal table_buffer
        if not table_buffer:
            return
        rows = [row.strip() for row in table_buffer if row.strip()]
        table_buffer = []
        if not rows:
            return

        header = rows[0]
        separator = rows[1] if len(rows) > 1 else ''
        data_rows = rows[2:] if re.match(r'^\|?\s*:?-+:?\s*(\|\s*:?-+:?\s*)+\|?$', separator) else rows[1:]

        def split_row(row):
            return [cell.strip() for cell in row.strip('|').split('|')]

        html_lines.append('<table>')
        html_lines.append('<thead><tr>')
        for cell in split_row(header):
            html_lines.append(f'<th>{inline_markdown(html.escape(cell))}</th>')
        html_lines.append('</tr></thead>')
        if data_rows:
            html_lines.append('<tbody>')
            for data_row in data_rows:
                if set(data_row) <= {'|', '-', ':', ' '}:
                    continue
                html_lines.append('<tr>')
                for cell in split_row(data_row):
                    html_lines.append(f'<td>{inline_markdown(html.escape(cell))}</td>')
                html_lines.append('</tr>')
            html_lines.append('</tbody>')
        html_lines.append('</table>')

    for raw_line in lines:
        line = raw_line.rstrip('\n')

        if in_code:
            if line.strip().startswith('```'):
                close_code()
            else:
                html_lines.append(html.escape(raw_line))
            continue

        stripped = line.strip()

        if stripped.startswith('```'):
            close_list()
            flush_table()
            in_code = True
            code_language = stripped[3:].strip()
            class_attr = f' class="language-{html.escape(code_language)}"' if code_language else ''
            html_lines.append(f'<pre><code{class_attr}>')
            continue

        if stripped in {'---', '***', '___'}:
            close_list()
            flush_table()
            html_lines.append('<hr>')
            continue

        if looks_like_table_row(stripped):
            table_buffer.append(stripped)
            continue
        else:
            flush_table()

        if not stripped:
            close_list()
            html_lines.append('<br>')
            continue

        if stripped.startswith('### '):
            close_list()
            html_lines.append(f"<h3>{html.escape(stripped[4:])}</h3>")
            continue
        if stripped.startswith('## '):
            close_list()
            html_lines.append(f"<h2>{html.escape(stripped[3:])}</h2>")
            continue
        if stripped.startswith('# '):
            close_list()
            html_lines.append(f"<h1>{html.escape(stripped[2:])}</h1>")
            continue

        if stripped.startswith(('- ', '* ')):
            if not in_list:
                html_lines.append('<ul>')
                in_list = True
            content = stripped[2:]
            html_lines.append(f"<li>{inline_markdown(html.escape(content))}</li>")
            continue

        close_list()
        html_lines.append(f"<p>{inline_markdown(html.escape(line))}</p>")

    close_code()
    close_list()
    flush_table()
    return '\n'.join(html_lines)


def looks_like_table_row(line):
    if '|' not in line:
        return False
    parts = line.strip('|').split('|')
    return len(parts) > 1


def inline_markdown(text):
    """Handle simple inline markdown such as bold and italics."""
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
    text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
    return text


def extract_score(response_text):
    patterns = [
        r'Score:\s*(\d+(?:\.\d+)?)\s*points',
        r'Score:\s*(\d+(?:\.\d+)?)',
        r'score of\s*(\d+(?:\.\d+)?)',
        r'rated at\s*(\d+(?:\.\d+)?)',
        r'(\d+(?:\.\d+)?)/100',
        r'(\d+(?:\.\d+)?)\s*out of\s*100',
        r'점수[:\s]*(\d+(?:\.\d+)?)',
        r'(\d+(?:\.\d+)?)\s*점'
    ]

    normalized_text = normalize_text(response_text)

    for pattern in patterns:
        match = re.search(pattern, normalized_text, re.IGNORECASE)
        if match:
            try:
                score_value = float(match.group(1))
                return max(0, min(100, int(round(score_value))))
            except ValueError:
                continue

    return 50


def advanced_preprocessing(text):
    text = normalize_text(text)
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)

    return text.strip()


def extract_resume_sections(text, section_patterns):
    compiled_patterns = {
        name: re.compile(pattern, re.IGNORECASE)
        for name, pattern in section_patterns.items()
    }

    sections = {}
    current_section = 'header'
    sections[current_section] = []

    lines = text.split('\n')
    for line in lines:
        matched = False
        for section_name, pattern in compiled_patterns.items():
            if pattern.search(line):
                current_section = section_name
                sections[current_section] = []
                matched = True
                break

        if not matched:
            sections[current_section].append(line)

    for section in sections:
        sections[section] = '\n'.join(sections[section]).strip()

    return sections