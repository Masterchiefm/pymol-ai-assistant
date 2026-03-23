import re


class MarkdownRenderer:
    """简单的Markdown渲染器 - 支持基本语法"""

    @staticmethod
    def render(text):
        """将Markdown文本渲染为HTML"""
        if not text:
            return ""

        html = text

        html = MarkdownRenderer._escape_html(html)

        html = MarkdownRenderer._render_code_blocks(html)
        html = MarkdownRenderer._render_inline_code(html)
        html = MarkdownRenderer._render_bold(html)
        html = MarkdownRenderer._render_italic(html)
        html = MarkdownRenderer._render_headers(html)
        html = MarkdownRenderer._render_lists(html)
        html = MarkdownRenderer._render_links(html)
        html = MarkdownRenderer._render_blockquotes(html)
        html = MarkdownRenderer._render_horizontal_rules(html)
        html = MarkdownRenderer._render_line_breaks(html)

        return html

    @staticmethod
    def _escape_html(text):
        """转义HTML特殊字符"""
        return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

    @staticmethod
    def _render_code_blocks(text):
        """渲染代码块 ```code```"""
        def replace_code_block(match):
            code = match.group(1)
            code = code.rstrip()
            return '<div style="background-color: #1E1E1E; border-radius: 6px; padding: 10px; margin: 8px 0; overflow-x: auto;"><code style="font-family: Consolas, Monaco, monospace; font-size: 13px; color: #D4D4D4;">%s</code></div>' % code

        return re.sub(r'```(\n?)([\s\S]*?)```', replace_code_block, text)

    @staticmethod
    def _render_inline_code(text):
        """渲染行内代码 `code`"""
        def replace_inline_code(match):
            code = match.group(1)
            return '<code style="background-color: #3A3A3A; color: #F5B041; padding: 2px 6px; border-radius: 3px; font-family: Consolas, Monaco, monospace; font-size: 13px;">%s</code>' % code

        return re.sub(r'`([^`]+)`', replace_inline_code, text)

    @staticmethod
    def _render_bold(text):
        """渲染粗体 **text** 或 __text__"""
        def replace_bold(match):
            return '<b>%s</b>' % match.group(1)

        text = re.sub(r'\*\*([^*]+)\*\*', replace_bold, text)
        text = re.sub(r'__([^_]+)__', replace_bold, text)
        return text

    @staticmethod
    def _render_italic(text):
        """渲染斜体 *text* 或 _text_"""
        def replace_italic(match):
            return '<i>%s</i>' % match.group(1)

        text = re.sub(r'\*([^*]+)\*', replace_italic, text)
        text = re.sub(r'_([^_]+)_', replace_italic, text)
        return text

    @staticmethod
    def _render_headers(text):
        """渲染标题 # Heading"""
        def replace_header(match):
            level = len(match.group(1))
            content = match.group(2).strip()
            font_size = max(16, 24 - level * 2)
            return '<h%d style="color: #5DADE2; font-size: %dpx; font-weight: bold; margin: 12px 0 8px 0;">%s</h%d>' % (level, font_size, content, level)

        return re.sub(r'^(#{1,6})\s+(.+)$', replace_header, text, flags=re.MULTILINE)

    @staticmethod
    def _render_lists(text):
        """渲染无序列表 - item 和有序列表 1. item"""
        lines = text.split('\n')
        result = []
        in_ul = False
        in_ol = False

        for line in lines:
            ul_match = re.match(r'^[-*]\s+(.+)$', line)
            ol_match = re.match(r'^\d+\.\s+(.+)$', line)

            if ul_match:
                if not in_ul:
                    if in_ol:
                        result.append('</ol>')
                        in_ol = False
                    result.append('<ul style="margin: 8px 0; padding-left: 20px;">')
                    in_ul = True
                result.append('<li style="color: #FFFFFF; margin: 4px 0;">%s</li>' % ul_match.group(1))
            elif ol_match:
                if not in_ol:
                    if in_ul:
                        result.append('</ul>')
                        in_ul = False
                    result.append('<ol style="margin: 8px 0; padding-left: 20px;">')
                    in_ol = True
                result.append('<li style="color: #FFFFFF; margin: 4px 0;">%s</li>' % ol_match.group(1))
            else:
                if in_ul:
                    result.append('</ul>')
                    in_ul = False
                if in_ol:
                    result.append('</ol>')
                    in_ol = False
                result.append(line)

        if in_ul:
            result.append('</ul>')
        if in_ol:
            result.append('</ol>')

        return '\n'.join(result)

    @staticmethod
    def _render_links(text):
        """渲染链接 [text](url)"""
        def replace_link(match):
            link_text = match.group(1)
            url = match.group(2)
            return '<a href="%s" style="color: #5DADE2; text-decoration: underline;">%s</a>' % (url, link_text)

        return re.sub(r'\[([^\]]+)\]\(([^)]+)\)', replace_link, text)

    @staticmethod
    def _render_blockquotes(text):
        """渲染引用 > text"""
        def replace_blockquote(match):
            content = match.group(1)
            return '<blockquote style="border-left: 3px solid #5DADE2; margin: 8px 0; padding-left: 12px; color: #CCCCCC; font-style: italic;">%s</blockquote>' % content

        return re.sub(r'^>\s+(.+)$', replace_blockquote, text, flags=re.MULTILINE)

    @staticmethod
    def _render_horizontal_rules(text):
        """渲染水平分割线 --- 或 ***"""
        return re.sub(r'^(-{3,}|\*{3,})$', '<hr style="border: none; border-top: 1px solid #555555; margin: 12px 0;">', text, flags=re.MULTILINE)

    @staticmethod
    def _render_line_breaks(text):
        """渲染换行"""
        return text.replace('\n', '<br>')
