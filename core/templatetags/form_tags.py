from django import template
from django.utils.safestring import SafeString

register = template.Library()

@register.filter(name='add_class')
def add_class(value, css_class):
    """
    Add a CSS class to a form field or widget
    Usage: {{ form.field|add_class:"my-class" }}
    """
    if hasattr(value, 'as_widget'):
        # This is a form field
        return value.as_widget(attrs={"class": css_class})
    elif isinstance(value, SafeString):
        # This is likely a radio button's tag
        # Extract the existing HTML and add the class
        html = str(value)
        if 'class="' in html:
            # If there's already a class attribute, append our class
            html = html.replace('class="', f'class="{css_class} ')
        else:
            # If there's no class attribute, add one
            html = html.replace('<input ', f'<input class="{css_class}" ')
        return SafeString(html)
    else:
        # Return unchanged if we don't know how to handle it
        return value 