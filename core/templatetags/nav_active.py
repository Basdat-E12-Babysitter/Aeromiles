from django import template
from django.urls import reverse, NoReverseMatch

register = template.Library()


@register.simple_tag(takes_context=True)
def nav_active(context, url_name, *args, **kwargs):
    """Return 'active' if the current request matches the given url name.

    Usage: {% nav_active 'dashboard:member' %}
    Falls back to comparing resolver_match.view_name if reverse fails.
    """
    request = context.get('request')
    if not request:
        return ''

    # Try reverse to get the URL path and compare
    try:
        path = reverse(url_name, args=args, kwargs=kwargs)
        if request.path == path or request.path.startswith(path):
            return 'active'
    except NoReverseMatch:
        # fallback: compare view_name
        resolver = getattr(request, 'resolver_match', None)
        if resolver and resolver.view_name == url_name:
            return 'active'
    return ''
