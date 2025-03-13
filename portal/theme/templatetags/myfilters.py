from django import template 

register = template.Library()

@register.filter(name="add_class")
def add_class(field, arg: str):
    return field.as_widget(attrs={"class":" ".join((field.css_classes(), arg))})
