from itertools import chain
import markdown as markdown_tool

def flatten_perms(perms_qs):
    bidimensional_perms = [gp.permissions.all() for gp in perms_qs]
    return list(chain.from_iterable(bidimensional_perms))

def markdown_to_html(content) -> str:
    return markdown_tool.markdown(content.decode("utf-8"))
