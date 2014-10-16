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
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from rest_framework.exceptions import NotAcceptable
from rest_framework.response import Response

from anubis.url import BooleanBuilder
from anubis.aggregators import QuerySetAggregator, TokenAggregator
from anubis.filters import Filter, ConversionFilter

from functools import reduce

class TemplateRetrieverView(APIView):
	allowed_views = {}
	allowed_templates = []
	allowed_methods = {}

	@staticmethod
	def reformat_template(original):
		return original.replace("forloop", "loop").replace("elif", "elseif")

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

				response[template] = self.reformat_template(template_body)
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

class TranslationView(APIView):
	allowed_filters = {}

	def get(self, _, query):
		query = query.strip().rstrip("/")
		expression = BooleanBuilder(query).build()

		aggregator = TokenAggregator(self.allowed_filters)
		tokenized = expression.traverse(aggregator)

		return Response(dict(expression=tokenized))

class MultiModelMeta(type):
	@property
	def allowed_filters(cls):
		return cls._fieldset_filters

	def __new__(mcs, cls_name, bases, dct):
		model_filters = {}
		fieldset_filters = {}

		if "_allowed_filters" in dct.keys():
			filters_source = dct["_allowed_filters"]
			common_filters = {}

			for name, obj in filters_source.items():
				if isinstance(obj, Filter):
					common_filters[name] = obj
					base_filter = obj
				else:
					base_filter = obj[0][1]
					for model_name, filter_ in obj:
						if isinstance(filter_, type) and \
								issubclass(filter_, ConversionFilter):
							filter_ = filter_(base_filter)

						model_filters.setdefault(model_name, {})[name] = filter_

				fieldset_filters[name] = base_filter

			for model_name in model_filters.keys():
				model_filters[model_name].update(common_filters)
		else:
			for base_cls in bases:
				if hasattr(base_cls, "_model_filters"):
					model_filters = base_cls._model_filters

				if hasattr(base_cls, "_fieldset_filters"):
					fieldset_filters = base_cls._fieldset_filters

		dct["_model_filters"] = model_filters
		dct["_fieldset_filters"] = fieldset_filters

		return super().__new__(mcs, cls_name, bases, dct)


class MultiModelMixin(metaclass=MultiModelMeta):
	model_parameter = None
	model_lookup = {}

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

		self._model = None

	@property
	def allowed_filters(self):
		try:
			return self._model_filters[self.kwargs[self.model_parameter]]
		except KeyError:
			return self.__class__.allowed_filters

	@property
	def model(self):
		if self._model is None:
			model_key = self.kwargs[self.model_parameter]
			self._model = self.model_lookup[model_key]

		return self._model

	@model.setter
	def model(self, value):
		self._model = value

class FilterViewMixin:
	expression_parameter = "search"
	allowed_filters = {}
	page_parameter = "page"
	objects_per_page = None
	pagination_cumulative = False

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.boolean_expression = None
		self.current_page = None
		self.current_page_object = None
		self.paginator = None

	def _get_queryset_filter(self, queryset):
		aggregator = QuerySetAggregator(queryset, self.allowed_filters)

		return self.boolean_expression.traverse(aggregator)

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)

		context["filters"] = self.allowed_filters
		context["filter_keys"] = ",".join(self.allowed_filters.keys())
		context["search_text"] = self.kwarg_or_empty(self.expression_parameter)

		if self.boolean_expression is not None:
			aggregator = TokenAggregator(self.allowed_filters)
			context["search_expression"] = \
				self.boolean_expression.traverse(aggregator)

		context["current_page"] = self.current_page
		context["current_page_object"] = self.current_page_object
		context["paginator"] = self.paginator

		return context

	def kwarg_or_none(self, key):
		if key in self.kwargs.keys() and self.kwargs[key]:
			return self.kwargs[key]
		else:
			return None

	def kwarg_or_empty(self, key):
		if key in self.kwargs.keys() and self.kwargs[key]:
			return self.kwargs[key]
		else:
			return ""

	@property
	def kwarg_val(self):
		return self.kwarg_or_none(self.expression_parameter)

	def get(self, *args, **kwargs):
		kwarg = self.kwarg_val

		if kwarg is not None:
			kwarg = kwarg.strip().rstrip("/")

			try:
				self.boolean_expression = BooleanBuilder(kwarg).build()
			except ValueError:
				error = ValueError("Confira sua expressão e verifique se não \
					esqueceu algum conector, por exemplo.")
				error.name = lambda : "Erro de Sintaxe"
				raise error

		return super().get(*args, **kwargs)

	def get_serializer_context(self):
		if self.objects_per_page is not None:
			return \
				{ "current_page": self.current_page
				, "total_pages": self.paginator.num_pages
				, "last_page": self.paginator.num_pages == self.current_page
				}

		return super().get_serializer_context()

	def get_queryset(self):
		# MRO do Python garante que haverá um get_queryset definido aqui se
		# FilterViewMixin for declarado como class pai antes da classe de View.
		original = super().get_queryset()

		if self.boolean_expression is not None:
			queryset = self._get_queryset_filter(original)
		else:
			queryset = original.none()

		if self.objects_per_page is not None:
			queryset = self.get_queryset_on_page(queryset)

		return queryset

	def get_queryset_on_page(self, queryset):
		self.current_page = self.kwarg_or_none(self.page_parameter)
		self.paginator = Paginator(list(queryset), self.objects_per_page)

		if self.current_page is None or self.current_page == 0:
			self.current_page = 1
		else:
			self.current_page = int(self.current_page)

		if self.current_page > self.paginator.num_pages:
			self.current_page = self.paginator.num_pages

		if self.pagination_cumulative:
			pages = range(1, self.current_page + 1)
		else:
			pages = [self.current_page]

		def fold(qset, page):
			self.current_page_object = self.paginator.page(page)
			qset += list(self.current_page_object.object_list)
			return qset

		return reduce(fold, pages, [])

	@classmethod
	def fieldsets(cls):
		return {filter_name: { "description": filter_.description,
			"template": filter_.form.as_p(),
			"arg_count": len(filter_.field_keys) } \
				for filter_name, filter_ in cls.allowed_filters.items()}

class NoCacheMixin:
	def get(self, *args, **kwargs):
		response = super().get(*args, **kwargs)

		response['Cache-Control'] = "no-cache, no-store, must-revalidate"
		response['Pragma'] = "no-cache"
		response['Expires'] = "0"

		return response
