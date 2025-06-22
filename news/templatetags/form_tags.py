# news/templatetags/form_tags.py
from django import template

register = template.Library()

@register.filter
def add_class(field, css_class):
    """Add a CSS class to a form field's widget."""
    if not field:
        return field
    widget = field.field.widget
    existing_classes = widget.attrs.get('class', '')
    widget.attrs['class'] = f"{existing_classes} {css_class}".strip()
    return field