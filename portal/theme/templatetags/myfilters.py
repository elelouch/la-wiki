from django import template 

register = template.Library()

@register.filter
def add_class(field, arg: str):
    return field.as_widget(attrs={"class":" ".join((field.css_classes(), arg))})

@register.filter
def hash_or_empty(h, key):
    if key in h:
        return h[key]
    return []
