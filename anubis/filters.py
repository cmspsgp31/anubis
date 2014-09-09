# Copyright (C) 2014, Ugo Pozo
#               2014, Câmara Municipal de São Paulo

# filters.py - definições de filtros padrão para o Anubis.

# Este arquivo é parte do software Anubis.

# Anubis é um software livre: você pode redistribuí-lo e/ou
# modificá-lo sob os termos da Licença Pública Geral GNU (GNU General Public
# 		License), tal como é publicada pela Free Software Foundation, na
# versão 3 da licença, ou (sua decisão) qualquer versão posterior.

# Anubis é distribuído na esperança de que seja útil, mas SEM NENHUMA
# GARANTIA; nem mesmo a garantia implícita de VALOR COMERCIAL ou ADEQUAÇÃO PARA
# UM PROPÓSITO EM PARTICULAR. Veja a Licença Pública Geral GNU para mais
# detalhes.

# Você deve ter recebido uma cópia da Licença Pública Geral GNU junto com este
# programa. Se não, consulte <http://www.gnu.org/licenses/>.

from anubis.query import ProcedureQuerySet
from anubis.forms import FilterForm
from django.db.models.query import Q
from django import forms
from functools import reduce

import operator

class Filter:
	def __init__(self):
		self.description = ""
		self._form = None
		self.fields = {}

	def filter_queryset(self, queryset, args):
		raise NotImplementedError()

	def describe(self, description):
		self.description = description
		return self

	def field(self, field_name, field_label=None, field_cls=forms.CharField,
			**field_kwargs):
		field = field_cls(label=field_label, **field_kwargs)
		self.fields[field_name] = field

		return self

	@property
	def form(self):
		form = FilterForm()

		for field_name, field in self.fields.items():
			form.fields[field_name] = field

		return form

class ProcedureFilter(Filter):
	def __init__(self, procedure_name):
		super().__init__()
		self.procedure_name = procedure_name
		self.description = procedure_name

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

		first_arg = args.pop(0)
		filtered = queryset.extra(where=[query_part], params=[first_arg])
		print(args)

		for arg in args:
			filtered = self.connector(filtered,
				queryset.extra(where=[query_part], params=[arg]))

		print(filtered.query)

		return filtered


