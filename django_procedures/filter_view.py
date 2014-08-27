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
from django.db.models.query import Q
import operator

class Filter:
	def filter_queryset(self, queryset, args):
		raise NotImplementedError()

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
		query_field = "{}__{}".format(self.field_name, self.suffix)
		complex_filter = [Q(**{query_field: arg}) for arg in args]

		return queryset.filter(reduce(self.connector, complex_filter))


def _parse_filter(filter_):
	args = []
	elem = None
	quote = False

	i = 0

	def advance(i, string):
		return (i+1, string[i+1])

	while i < len(filter_):
		char = filter_[i]

		if elem is None:
			quote = char == "\""
			elem = "" if quote else char
		else:
			if not quote:
				if char == ",":
					args.append(elem)
					elem = None
				else:
					elem += char
			else:
				if char == "$":
					i, char = advance(i, filter_)
					elem += char
				elif char == "\"":
					while not char == "," and i < len(filter_) - 1:
						i, char = advance(i, filter_)

					args.append(elem)
					elem = None
					quote = False
				else:
					elem += char

		i += 1

	if elem is not None:
		args.append(elem)

	return args

class FilterViewMixin:
	prefix = "filter"
	kwarg_key = "search"
	allowed_filters = {}

	def _get_queryset_filter(self, queryset, url):
		url = url.strip()
		url = url.rstrip("/")

		for filter_ in url.split("/{}/".format(self.prefix)):
			args = _parse_filter(filter_)

			if len(args):
				queryset = self._apply_filter(queryset, args)

		return queryset

	def get_queryset(self):
		# MRO do Python garante que haverá um get_queryset definido aqui se
		# FilterViewMixin for declarado antes da classe base.
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

