from django import template

register = template.Library()

@register.filter
def split(value, arg):
    """Split a string by the given separator"""
    return value.split(arg)

@register.filter
def chr_filter(value):
    """Convert an integer to its corresponding ASCII character"""
    try:
        return chr(int(value))
    except (ValueError, TypeError):
        return ''

@register.filter
def in_list(value, arg_list):
    """Check if value is in a list"""
    if isinstance(arg_list, str):
        # If it's a string, split it by comma
        arg_list = arg_list.split(',')
    return value in arg_list
