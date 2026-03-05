"""
自定义模板过滤器 - Markdown 扩展
用于在前端模板中解析 Markdown 语法
"""
from django import template
from django.template.defaultfilters import stringfilter
import markdown as md

register = template.Library()

@register.filter()
@stringfilter
def markdown(value):
    """
    将 Markdown 文本转换为 HTML
    集成扩展：
    - extra: 支持表格、脚注等
    - codehilite: 代码高亮
    - toc: 自动生成目录
    - nl2br: 换行符自动转 <br>
    """
    return md.markdown(value, extensions=[
        'markdown.extensions.extra',
        'markdown.extensions.codehilite',
        'markdown.extensions.toc',
        'markdown.extensions.nl2br',
    ])