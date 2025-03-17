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

@register.simple_tag
def btn_get(url):
    attrs= """
        hx-get={url}
        hx-target=#pivot-section
        hx-trigger=click
        """
    return attrs.format(url=url)

@register.simple_tag
def btn_delete(url):
    attrs = """
        hx-trigger=click consume
        hx-confirm='You sure want to delete the section'
        hx-swap='delete'
        hx-target='closest .subsection'
        hx-delete={url}
        """
    return attrs.format(url=url)

