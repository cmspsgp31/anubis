from django import template
from django.core.urlresolvers import reverse
from urllib.parse import unquote

register = template.Library()

@register.filter
def classname(obj):
	return obj.__class__.__name__

@register.filter
def fieldsets(view_name):
	return "{}.fieldsets".format(view_name)

@register.filter
def getitem(obj, key):
	return obj[key]

@register.inclusion_tag("search_widget.html", takes_context=True)
def search(context, search_id, search_route, translate_route, index_route,
		token_list, default_unit, extra_fields=None):
	expression = context.get("search_expression", None)
	action = reverse(search_route,
		kwargs={search_id: "{{{{ {}|safe }}}}".format(search_id)})
	search_url = reverse(search_route, kwargs={search_id: ""}).lstrip("/")
	translate_url = reverse(translate_route, args=[""]).rstrip("/")
	index_url = reverse(index_route).rstrip("/")

	return dict(expression=expression, token_list=token_list,
		action=unquote(action), search_id=search_id, search_url=search_url,
		translate_url=translate_url, index_url=index_url,
		default_unit=default_unit, extra_fields=extra_fields)

@register.inclusion_tag("available_filters.html", takes_context=True)
def download_templates(context, url_='templates', *templates):
	source = ",".join(templates)
	return dict(source=source, url_=url_)


