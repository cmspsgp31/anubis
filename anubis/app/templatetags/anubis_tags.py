from django import template

register = template.Library()

@register.inclusion_tag("search_widget.html", takes_context=True)
def search(context, key):
	expr = context.get("search_expression", None)
	return dict(expr=expr, filters_key=key)

@register.inclusion_tag("available_filters.html", takes_context=True)
def register_filters(context, view):
	return dict(source="{}.fieldsets".format(view))


