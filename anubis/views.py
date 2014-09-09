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

from functools import partial

class TemplateRetrieverView(APIView):
	allowed_views = {}
	allowed_templates = []
	allowed_methods = {}

	def get(self, request, templates):
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

				response.update({"{}.{}".format(view_name, name): template_body\
					for name, template_body in views.items()})

		return Response(response)



class FilterViewMixin:
	kwarg_key = "search"
	allowed_filters = {}

	def _handle_base_expression(self, queryset, base_expression):
		filter_ = self.allowed_filters[base_expression["field"]]
		args = base_expression["args"]
		return filter_.filter_queryset(queryset, args)

	def _operator_apply(self, queryset, base_expression=None,
		not_expression=None, and_expression=None, or_expression=None):
		if base_expression is not None:
			return self._handle_base_expression(queryset, base_expression)
		elif not_expression is not None:
			return queryset.exclude(id__in=not_expression.values("id"))
		elif and_expression is not None:
			left_qset, right_qset = and_expression
			return left_qset & right_qset
		elif or_expression is not None:
			left_qset, right_qset = or_expression
			return left_qset | right_qset
		else:
			return queryset

	def _get_queryset_filter(self, queryset, url):
		url = url.strip().rstrip("/")
		boolean_expr = BooleanBuilder(url).build()
		aggregator = partial(self._operator_apply, queryset)

		return boolean_expr.traverse(aggregator)

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)

		context["filters"] = self.allowed_filters

		return context

	def get_queryset(self):
		# MRO do Python garante que haverá um get_queryset definido aqui se
		# FilterViewMixin for declarado como class pai antes da classe de View.
		original = super().get_queryset()

		if self.kwarg_key in self.kwargs.keys() and self.kwargs[self.kwarg_key]:
			return self._get_queryset_filter(original,
				self.kwargs[self.kwarg_key])
		else:
			return original.none()

	def _apply_filter(self, queryset, args):
		filter_name = args.pop(0)

		if not filter_name in self.allowed_filters.keys():
			raise ValueError("{} is not an allowed filter." \
				.format(filter_name))

		return self.allowed_filters[filter_name].filter_queryset(queryset, args)

	@classmethod
	def fieldsets(cls):
		return {filter_name: filter_.form.as_p() \
			for filter_name, filter_ in cls.allowed_filters.items()}
