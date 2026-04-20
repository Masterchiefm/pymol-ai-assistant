import markdown

_FONT_FAMILY = "'HarmonyOS Sans SC', 'Microsoft YaHei', sans-serif"


class MarkdownRenderer:
    """Markdown渲染器 - 使用markdown库"""

    @staticmethod
    def render(text):
        """将Markdown文本渲染为HTML，适配深色主题"""
        if not text:
            return ""

        md = markdown.Markdown(
            extensions=[
                'tables',
                'fenced_code',
                'nl2br',
                'extra'
            ]
        )

        html = md.convert(text)

        html = MarkdownRenderer._apply_dark_theme(html)

        return html

    @staticmethod
    def _apply_dark_theme(html):
        body_style = ' style="color: #FFFFFF; font-family: {}; line-height: 1.6;"'.format(_FONT_FAMILY)
        html = '<div{}>'.format(body_style) + html + '</div>'
        replacements = {
            '<table>': '<table style="border-collapse: collapse; margin: 12px 0; width: 100%; border: 1px solid #555555;">',
            '<thead>': '<thead>',
            '<tbody>': '<tbody>',
            '<tr>': '<tr>',
            '<th>': '<th style="background-color: #404040; color: #5DADE2; border: 1px solid #555555; padding: 8px 12px; font-weight: bold;">',
            '<td>': '<td style="border: 1px solid #555555; padding: 6px 12px; color: #FFFFFF;">',
            '<code>': '<code style="background-color: #3A3A3A; color: #F5B041; padding: 2px 6px; border-radius: 3px; font-family: Consolas, Monaco, monospace; font-size: 13px;">',
            '<pre>': '<pre style="background-color: #1E1E1E; border-radius: 6px; padding: 10px; margin: 8px 0; overflow-x: auto; font-family: Consolas, Monaco, monospace;">',
            '<blockquote>': '<blockquote style="border-left: 3px solid #5DADE2; margin: 8px 0; padding-left: 12px; color: #CCCCCC; font-style: italic;">',
            '<hr>': '<hr style="border: none; border-top: 1px solid #555555; margin: 12px 0;">',
        }

        for old, new in replacements.items():
            html = html.replace(old, new)

        return html
