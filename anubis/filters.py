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

import operator
from functools import reduce

from anubis.forms import FilterForm, RangeForm
from anubis.query import ProcedureQuerySet
from django import forms
from django.db.models.query import Q


class Filter:
    base_form = FilterForm

    def __init__(self, identifier):
        self.identifier = identifier
        self.description = identifier
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

    def validate(self, args):
        bound_form = self.bound_form(args)

        if not bound_form.is_valid():
            errors = [field.errors for field in bound_form if field.errors]
            errors = reduce(lambda e, a: a + e, errors, [])
            exc = ValueError(errors)
            exc.name = lambda: "Erro de validação"
            raise exc

        return [bound_form.cleaned_data[key] for key in self.field_keys]

    def field(self, field_name, field_label=None, field_cls=forms.CharField,
              **field_kwargs):
        if len(self.field_keys) == 0 and field_label is None:
            field_label = self.description

        field_name = "{}_{:04d}_{}".format(self.identifier,
                                           len(self.field_keys) + 1, field_name)

        # mudamos o padrão do Django em que o campo era obrigatório por padrão
        # para o campo ser opcional por padrão, porque no contexto da pesquisa
        # faz mais sentido
        if "required" not in field_kwargs.keys():
            field_kwargs["required"] = False

        field = field_cls(label=field_label, **field_kwargs)
        self.fields[field_name] = field
        self.field_keys.append(field_name)

        return self

    def _add_fields_to_form(self, form):
        for field_name in self.field_keys:
            form.fields[field_name] = self.fields[field_name]

    def process_form(self, form):
        self._add_fields_to_form(form)

        return form

    @property
    def form(self):
        form = self.base_form()

        return self.process_form(form)

    def bound_form(self, args):
        form = self.base_form({field_name: args[i] \
                               for i, field_name in enumerate(self.field_keys)})

        return self.process_form(form)


class ConversionFilter(Filter):
    def __init__(self, base_filter):
        assert isinstance(base_filter, Filter)

        self.base_filter = base_filter
        self.identifier = base_filter.identifier
        self.description = base_filter.description
        self.fields = base_filter.fields
        self.field_keys = base_filter.field_keys

    def filter_queryset(self, queryset, args):
        base_queryset = self.base_filter.filter_queryset(self.source_queryset(),
                                                         args)

        return queryset & self.convert_queryset(base_queryset)

    def source_queryset(self):
        raise NotImplementedError()

    def convert_queryset(self, base_queryset):
        raise NotImplementedError()


class ProcedureFilter(Filter):
    def __init__(self, procedure_name):
        self.procedure_name = procedure_name
        super().__init__(procedure_name)

    def filter_queryset(self, queryset, args):
        assert isinstance(queryset, ProcedureQuerySet)

        return queryset.procedure(self.procedure_name, *args)


class ChoiceProcedureFilter(Filter):
    def __init__(self, identifier, choices=None):
        super().__init__(identifier)

        if choices is not None:
            self.choices(choices)

    def choices(self, choices):
        self.procedure_choices = choices

        self.field(self.identifier, field_cls=forms.ChoiceField,
                   choices=self.procedure_choices)

        return self

    def filter_queryset(self, queryset, args):
        assert isinstance(queryset, ProcedureQuerySet)

        procedure_name = args[0]

        assert procedure_name in dict(self.procedure_choices).keys()

        return queryset.procedure(procedure_name, *args[1:])


class RangeProcedureFilter(ProcedureFilter):
    base_form = RangeForm

    def __init__(self, procedure_name):
        super().__init__(procedure_name)
        self.range_fields = []
        self.range_buffer = []

    def field(self, field_name, field_label=None, field_cls=forms.CharField,
              range_field=False, **field_kwargs):
        super().field(field_name, field_label, field_cls, **field_kwargs)

        if range_field:
            self._add_range_field(self.field_keys[-1])

        return self

    def _add_range_field(self, range_field):
        self.range_buffer.append(range_field)

        if len(self.range_buffer) > 1:
            self.range_fields.append(tuple(self.range_buffer[:2]))
            self.range_buffer = []

    def process_form(self, form):
        form = super().process_form(form)
        form.range_fields = self.range_fields

        return form


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


class MultiQuerySetFilter(Filter):
    def __init__(self, identifier, *fields_names, connector=operator.and_):
        self.fields_names = fields_names
        super().__init__(identifier)
        self.connector = connector

    def filter_queryset(self, queryset, args):
        complex_filter = [Q(**{field: arg}) \
                          for field, arg in zip(self.fields_names, args) \
                          if arg is not None]

        return queryset.filter(reduce(self.connector, complex_filter, Q()))


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
