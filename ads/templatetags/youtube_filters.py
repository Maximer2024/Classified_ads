from django import template
import re

register = template.Library()


@register.filter
def embed_youtube(value):
    if not value:
        return value

    match = re.search(
        r"(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/(?:[^\/]+\/.+\/|(?:v|e(?:mbed)?)\/|.*[?&]v=)|youtu\.be\/)([^\"&?\/ ]{11})",
        value)

    if match:
        return f"https://www.youtube.com/embed/{match.group(1)}"

    return value