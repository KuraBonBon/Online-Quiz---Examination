from django import template

register = template.Library()

@register.filter
def ordinal(value):
    """
    Converts an integer to its ordinal representation.
    Examples:
    1 becomes 1st
    2 becomes 2nd 
    3 becomes 3rd
    4 becomes 4th
    """
    try:
        value = int(value)
    except (ValueError, TypeError):
        return value
    
    if 10 <= value % 100 <= 20:
        suffix = 'th'
    else:
        suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(value % 10, 'th')
    
    return f"{value}{suffix}"

@register.filter
def pluralize_custom(count, word):
    """
    Custom pluralize filter that handles the count and word.
    """
    if count == 1:
        return f"{count} {word}"
    else:
        return f"{count} {word}s"
