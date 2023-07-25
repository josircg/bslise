from django.template import Library
from django.template.defaultfilters import stringfilter, truncatewords
from django.utils.html import strip_tags

register = Library()


@register.filter(is_safe=True)
@stringfilter
def truncate_summary(value, arg):
    """Remove all tags/whitespaces and return a truncated text"""
    if isinstance(value, str):
        value = strip_tags(value).replace('&nbsp;', '')
        value = ' '.join([s for s in value.splitlines() if s])

    return truncatewords(value, arg)
