# Copyright (C) 2014, Ugo Pozo
#               2014, Câmara Municipal de São Paulo

# views.py - views do Anubis

# Este arquivo é parte do software Anubis.

# Anubis é um software livre: você pode redistribuí-lo e/ou modificá-lo
# sob os termos da Licença Pública Geral GNU (GNU General Public License),
# tal como é publicada pela Free Software Foundation, na versão 3 da
# licença, ou (sua decisão) qualquer versão posterior.

# Anubis é distribuído na esperança de que seja útil, mas SEM NENHUMA
# GARANTIA; nem mesmo a garantia implícita de VALOR COMERCIAL ou ADEQUAÇÃO
# PARA UM PROPÓSITO EM PARTICULAR. Veja a Licença Pública Geral GNU para
# mais detalhes.

# Você deve ter recebido uma cópia da Licença Pública Geral GNU junto com
# este programa. Se não, consulte <http://www.gnu.org/licenses/>.

from rest_framework.views import APIView
from django.template.loaders.app_directories import Loader
from rest_framework.exceptions import NotAcceptable
from rest_framework.response import Response

from anubis.url import BooleanBuilder
from anubis.aggregators import QuerySetAggregator, TokenAggregator

class TemplateRetrieverView(APIView):
	allowed_views = {}
	allowed_templates = []
	allowed_methods = {}

	def get(self, _, templates):
		templates = templates.split(",")
		response = {}

		for template in templates:
			try:
				view_name, view_method = template.split(".")
			except ValueError:
				if not template in self.allowed_templates:
					raise NotAcceptable("Template: {}".format(template))

				loader = Loader()
				name = "{}.html".format(template)
				template_body = loader.load_template_source(name)[0]

				response[template] = template_body
			else:
				if view_name not in self.allowed_views.keys():
					raise NotAcceptable("View: {}".format(view_name))

				view = self.allowed_views[view_name]

				if view_name in self.allowed_methods.keys() and \
						view_method not in self.allowed_methods[view_name]:
					raise NotAcceptable("Method: {}.{}".format(view_name,
						view_method))

				views = getattr(view, view_method)()

				response[view_name] = views
				# response.update({"{}.{}".format(view_name, name): template_body\
				# 	for name, template_body in views.items()})

		return Response(response)



class FilterViewMixin:
	kwarg_key = "search"
	allowed_filters = {}

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.boolean_expression = None

	def _get_queryset_filter(self, queryset):
		aggregator = QuerySetAggregator(queryset, self.allowed_filters)

		return self.boolean_expression.traverse(aggregator)

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)

		context["filters"] = self.allowed_filters
		context["filter_keys"] = ",".join(self.allowed_filters.keys())

		if self.boolean_expression is not None:
			aggregator = TokenAggregator(self.allowed_filters)
			context["search_expression"] = \
				self.boolean_expression.traverse(aggregator)

		for evento in context["evento_list"]:
			print(evento.nome)
			for tag in evento.tags.all():
				print (tag.nome)

		return context

	def kwarg_or_none(self, key):
		if key in self.kwargs.keys() and self.kwargs[key]:
			return self.kwargs[key]
		else:
			return None

	@property
	def kwarg_val(self):
		return self.kwarg_or_none(self.kwarg_key)

	def get(self, *args, **kwargs):
		kwarg = self.kwarg_val

		if kwarg is not None:
			kwarg = kwarg.strip().rstrip("/")
			self.boolean_expression = BooleanBuilder(kwarg).build()

		return super().get(*args, **kwargs)

	def get_queryset(self):
		# MRO do Python garante que haverá um get_queryset definido aqui se
		# FilterViewMixin for declarado como class pai antes da classe de View.
		original = super().get_queryset()

		if self.boolean_expression is not None:
			return self._get_queryset_filter(original)
		else:
			return original.none()

	@classmethod
	def fieldsets(cls):
		return {filter_name: { "description": filter_.description,
			"template": filter_.form.as_p() } \
				for filter_name, filter_ in cls.allowed_filters.items()}
