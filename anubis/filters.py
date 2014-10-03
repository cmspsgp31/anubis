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
	def __init__(self, identifier):
		self.identifier = identifier
		self.description = identifier
		self._form = None
		self.fields = {}
		self.field_keys = []

	def filter_queryset(self, queryset, args):
		raise NotImplementedError()

	def identify(self, identifier):
		self.identifier = identifier
		return self

	def describe(self, description):
		self.description = description
		return self

	def field(self, field_name, field_label=None, field_cls=forms.CharField,
			**field_kwargs):
		if len(self.field_keys) == 0 and field_label is None:
			field_label = self.description

		field_name = "{}_{:04d}_{}".format(self.identifier,
			len(self.field_keys) + 1, field_name)

		field = field_cls(label=field_label, **field_kwargs)
		self.fields[field_name] = field
		self.field_keys.append(field_name)

		return self

	@property
	def form(self):
		form = FilterForm()

		for field_name in self.field_keys:
			form.fields[field_name] = self.fields[field_name]

		return form

	def bound_form(self, args):
		form = FilterForm({field_name: args[i] \
			for i, field_name in enumerate(self.field_keys)})

		for field_name in self.field_keys:
			form.fields[field_name] = self.fields[field_name]

		return form


class ProcedureFilter(Filter):
	def __init__(self, procedure_name):
		self.procedure_name = procedure_name
		super().__init__(procedure_name)

	def filter_queryset(self, queryset, args):
		assert isinstance(queryset, ProcedureQuerySet)

		return queryset.procedure(self.procedure_name, *args)

class QuerySetFilter(Filter):
	def __init__(self, field_name, suffix="", connector=operator.or_):
		self.field_name = field_name
		super().__init__(field_name)
		self.connector = connector
		self.suffix = suffix

	def filter_queryset(self, queryset, args):
		query_field = self.field_name

		if len(self.suffix) > 0:
			query_field += "__{}".format(self.suffix)

		complex_filter = [Q(**{query_field: arg}) for arg in args]

		return queryset.filter(reduce(self.connector, complex_filter))

class FullTextFilter(Filter):
	def __init__(self, field_name):
		self.field_name = field_name
		super().__init__(field_name)

	def filter_queryset(self, queryset, args):
		arg = " ".join(list(args))
		table = queryset.model._meta.db_table
		query_part = """
			to_tsvector(unaccent("{table}"."{field}")) @@
			plainto_tsquery(unaccent(%s)) \
			""".format(table=table, field=self.field_name)

		filtered = queryset.extra(where=[query_part], params=[arg])

		print(filtered.query)

		return filtered



class TrigramFilter(Filter):
	def __init__(self, field_name, connector=operator.or_):
		self.field_name = field_name
		super().__init__(field_name)
		self.connector = connector

	def filter_queryset(self, queryset, args):
		args = list(args)
		table = queryset.model._meta.db_table
		query_part = "\"{table}\".\"{field}\" %% %s" \
			.format(table=table, field=self.field_name)

		first_arg = args.pop(0)
		filtered = queryset.extra(where=[query_part], params=[first_arg])

		for arg in args:
			filtered = self.connector(filtered,
				queryset.extra(where=[query_part], params=[arg]))

		return filtered


