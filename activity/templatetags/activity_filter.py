from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()


@register.filter
@stringfilter
def inim(component):
    if 'Kreis' in component or 'kreis' in component:
        return 'im ' + component
    return 'in ' + component


@register.filter(name='lookup')
def lookup(value, arg):
    return value.get(arg)


@register.filter(name='lookup_str')
def lookup_str(value, arg):
    return value.get(str(arg))
