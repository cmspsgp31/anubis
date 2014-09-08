# Copyright (C) 2014, Ugo Pozo
#               2014, Câmara Municipal de São Paulo

# filter_view.py - Django View que suporta filtros arbitrários.

# Este arquivo é parte do software django_procedures.

# django_procedures é um software livre: você pode redistribuí-lo e/ou
# modificá-lo sob os termos da Licença Pública Geral GNU (GNU General Public
# 		License), tal como é publicada pela Free Software Foundation, na
# versão 3 da licença, ou (sua decisão) qualquer versão posterior.

# django_procedures é distribuído na esperança de que seja útil, mas SEM NENHUMA
# GARANTIA; nem mesmo a garantia implícita de VALOR COMERCIAL ou ADEQUAÇÃO PARA
# UM PROPÓSITO EM PARTICULAR. Veja a Licença Pública Geral GNU para mais
# detalhes.

# Você deve ter recebido uma cópia da Licença Pública Geral GNU junto com este
# programa. Se não, consulte <http://www.gnu.org/licenses/>.

from django_procedures.query import ProcedureQuerySet
from django_procedures.url import BooleanBuilder
from django.db.models.query import Q
from functools import reduce, partial

import operator

class Filter:
	def __init__(self):
		self.description = ""
		self.form = None

	def filter_queryset(self, queryset, args):
		raise NotImplementedError()

	def describe(self, description):
		self.description = description
		return self

	def with_form(self):
		return self

class ProcedureFilter(Filter):
	def __init__(self, procedure_name):
		super().__init__()
		self.procedure_name = procedure_name

	def filter_queryset(self, queryset, args):
		assert isinstance(queryset, ProcedureQuerySet)

		return queryset.procedure(self.procedure_name, *args)

class QuerySetFilter(Filter):
	def __init__(self, field_name, suffix="", connector=operator.or_):
		super().__init__()
		self.field_name = field_name
		self.connector = connector
		self.suffix = suffix

	def filter_queryset(self, queryset, args):
		query_field = self.field_name

		if len(self.suffix) > 0:
			query_field += "__{}".format(self.suffix)

		complex_filter = [Q(**{query_field: arg}) for arg in args]

		return queryset.filter(reduce(self.connector, complex_filter))

class TrigramFilter(Filter):
	def __init__(self, field_name, connector=operator.or_):
		super().__init__()
		self.field_name = field_name
		self.connector = connector

	def filter_queryset(self, queryset, args):
		query_part = "\"{field}\" %% %s".format(field=self.field_name)

		queryset = queryset.extra(where=[query_part], params=args[:1])
		print(queryset.query)

		return queryset

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

	def convertFilterToModel(self, target_model):
		pass

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

