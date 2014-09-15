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
def search(context, template_key, route, form_name, translate_route,
		extra_forms=None):
	expr = context.get("search_expression", None)
	action = reverse(route,
		kwargs={form_name: "{{{{ {}|safe }}}}".format(form_name)})
	route = reverse(route, kwargs={form_name: ""}).lstrip("/")
	translate_route = reverse(translate_route, args=[""]).rstrip("/")

	return dict(expr=expr, template_key=template_key, action=unquote(action),
		form_name=form_name, route=route, translate_route=translate_route,
		extra_forms=extra_forms)

@register.inclusion_tag("available_filters.html", takes_context=True)
def download_templates(context, *templates):
	source = ",".join(templates)
	return dict(source=source)


