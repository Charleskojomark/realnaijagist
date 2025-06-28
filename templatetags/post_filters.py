from django import template
from django.utils.safestring import mark_safe
import re

register = template.Library()

@register.filter
def add_paragraphs(value):
    """
    Convert double newlines or double <br> tags into paragraphs, preserving existing <p> tags.
    If content already contains <p> tags, return it unchanged.
    If content is plain text or contains <br> tags, wrap segments in <p> tags.
    """
    # Check if content already contains <p> tags
    if '<p>' in value:
        return mark_safe(value)  # Return unchanged if <p> tags exist

    # Replace multiple <br> tags with double newlines for processing
    value = re.sub(r'(<br\s*/?>\s*){2,}', '\n\n', value)
    # Remove single <br> tags to clean up formatting
    value = re.sub(r'<br\s*/?>', ' ', value)
    # Split by double newlines and strip empty segments
    paragraphs = [p.strip() for p in value.split('\n\n') if p.strip()]
    # Wrap each paragraph in <p> tags
    paragraphs = [f'<p>{p}</p>' for p in paragraphs]
    # Join and mark as safe for HTML rendering
    return mark_safe(''.join(paragraphs))