import re

from django import template
from django.core.urlresolvers import reverse, get_resolver
from urllib.parse import unquote

import json

register = template.Library()

@register.filter
def classname(obj):
    return obj.__class__.__name__

@register.filter
def fieldsets(view_name):
    return "{}.fieldsets".format(view_name)

@register.filter
def json_ids(object_list):
    return json.dumps([obj.id for obj in object_list])

@register.filter
def getitem(obj, key):
    return obj[key]

@register.filter
def page_number(counter, objects_per_page):
    try:
        return int(counter) // int(objects_per_page) + 1
    except:
        return ''


def template_pair(field_name):
    return (field_name, "{{{{ {}|safe }}}}".format(field_name))

def get_pattern(route):
    resolver = get_resolver(None)

    if ":" in route:
        namespace, route = route.split(":")
        resolver = resolver.namespace_dict[namespace][1]

    url = resolver.reverse_dict.getlist(route)

    if url:
        return url[0][1]
    else:
        return None

NAMED_GROUPS = re.compile(r'\?P<[a-zA-Z]+>')

@register.inclusion_tag("search_widget.html", takes_context=True)
def search(context, search_id, search_route, translate_route, index_route,
        token_list, default_unit, extra_fields=None, expression_index=None,
        generate_search_route=None):
    expression = context.get("search_expression", None)

    action_kwargs = [template_pair(search_id)]

    if extra_fields is not None:
        action_kwargs += [template_pair(field) \
                for field in extra_fields.fields.keys()]

    if generate_search_route is None:
        generate_search_route = search_route

    action = reverse(generate_search_route, kwargs=dict(action_kwargs))

    search_url = get_pattern(search_route)
    search_url = NAMED_GROUPS.sub("", search_url)

    translate_url = reverse(translate_route, args=[""]).rstrip("/")

    index_url = reverse(index_route).rstrip("/")

    return dict(expression=expression, token_list=token_list,
        action=unquote(action), search_id=search_id, search_url=search_url,
        translate_url=translate_url, index_url=index_url,
        default_unit=default_unit, extra_fields=extra_fields,
        expression_index=expression_index,
        this_base=context.get('this_base', ''))

@register.inclusion_tag("available_filters.html", takes_context=True)
def download_templates(context, url_='templates', *templates):
    source = ",".join(templates)
    return dict(source=source, url_=url_)


