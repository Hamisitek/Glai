from django import template

register = template.Library()

@register.filter
def mul(value, arg):
    """Multiply two numbers"""
    try:
        return int(value) * int(arg)
    except (ValueError, TypeError):
        return 0
