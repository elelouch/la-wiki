from typing import Dict
from django import template 

register = template.Library()

@register.filter
def add_class(field, arg: str):
    return field.as_widget(attrs={"class":" ".join((field.css_classes(), arg))})

@register.filter
def hash_or_empty(h, key):
    if h and key in h:
        return h[key]
    return []

@register.simple_tag
def btn_get(url, target, trigger):
    attrs= """
        hx-get="{url}"
        hx-target="{target}"
        hx-trigger="{trigger}"
        """

    return attrs.format(
            url=url,
            target=target,
            trigger=trigger,
        )

@register.simple_tag
def btn_delete(url, target, trigger, swap):
    attrs = """
        hx-trigger="{trigger}"
        hx-confirm="Are you sure"
        hx-swap="{swap}"
        hx-target="{target}"
        hx-delete="{url}"
        """
    return attrs.format(
            url=url,
            trigger=trigger,
            swap=swap,
            target=target
        )

