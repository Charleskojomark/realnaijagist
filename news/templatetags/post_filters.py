from django import template
from django.utils.safestring import mark_safe
import re

register = template.Library()

@register.filter
def add_paragraphs(value):
    """
    Convert double newlines (\n\n or \r\n\r\n) or double <br> tags into paragraphs,
    preserving existing <p> tags, single <br> tags, and all whitespace within paragraphs.
    Handle single-block content by wrapping it in a <p> tag.
    """
    print(f"Raw input content: {value!r}")  # Debug: Log raw input

    # Check if content already contains <p> tags
    if '<p>' in value:
        print("Found existing <p> tags, returning unchanged")
        return mark_safe(value)

    # Normalize double <br> tags to \n\n
    value = re.sub(r'(<br\s*/?>\s*){2,}', '\n\n', value)
    # Normalize Windows-style \r\n\r\n to \n\n
    value = re.sub(r'\r\n\r\n', '\n\n', value)
    # Split by double newlines, preserving all content
    paragraphs = [p for p in value.split('\n\n') if p]
    
    # If no paragraphs detected, treat as single paragraph
    if not paragraphs:
        paragraphs = [value] if value else []
    
    print(f"Paragraphs after split: {paragraphs!r}")  # Debug: Log split paragraphs

    # Wrap each paragraph in <p> tags, preserving internal <br> tags and whitespace
    paragraphs = [f'<p>{p}</p>' for p in paragraphs]
    result = ''.join(paragraphs)
    print(f"Output content: {result!r}")  # Debug: Log final output
    return mark_safe(result)