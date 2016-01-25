# Copyright (C) 2014, Ugo Pozo 2014, Câmara Municipal de São Paulo

# query.py - extensões para queries do Anubis.

# Este arquivo é parte do software Anubis.

# Anubis é um software livre: você pode redistribuí-lo e/ou
# modificá-lo sob os termos da Licença Pública Geral GNU (GNU General Public
# License), tal como é publicada pela Free Software Foundation, na
# versão 3 da licença, ou (sua decisão) qualquer versão posterior.

# Anubis é distribuído na esperança de que seja útil, mas SEM NENHUMA
# GARANTIA; nem mesmo a garantia implícita de VALOR COMERCIAL ou ADEQUAÇÃO PARA
# UM PROPÓSITO EM PARTICULAR. Veja a Licença Pública Geral GNU para mais
# detalhes.

# Você deve ter recebido uma cópia da Licença Pública Geral GNU junto com este
# programa. Se não, consulte <http://www.gnu.org/licenses/>.

from collections import OrderedDict
from operator import itemgetter

from anubis.sql_aggregators import ProcedureOrderingAnnotation
from django.db import connection as base_connection, connections
from django.db import models
from django.db.models.query import QuerySet
from django.db.models.expressions import Ref, F


class ProcedureQuerySet(QuerySet):
    """Class to provide a procedure aware QuerySet (and, with the
    :meth:`as_manager` method, a Manager) to Djang models.

    Example:
        Use this class as follows to enable procedure queries on your models::

            from django.db.models import Model, CharField
            from anubis.query import ProcedureQuerySet

            class MyModel(Model):
                myText = CharField()

                class QuerySet(ProcedureQuerySet):
                    pass

                objects = QuerySet.as_manager()
    """

    order_by_procedure_column = "anubis_index"

    def _get_connection(self):
        if self.db is not None:
            conn = connections[self.db]
        else:
            conn = base_connection

        return conn

    @staticmethod
    def _test_order_direction(source, dest):
        if source.startswith("-"):
            source = source[1:]
            dest = "-{}".format(dest)
        elif source.startswith("+"):
            source = source[1:]
            dest = "+{}".format(dest)

        return source, dest

    def order_by_procedure(self, procname, *args, field='id', extra_fields=None,
                           **kwargs):
        aggregate = self.procedure_aggregate(procname, *args, **kwargs)
        return self.order_by_aggregates(aggregate, field=field,
                                        extra_fields=extra_fields)

    def order_by_aggregates(self, *aggregates, field="id", extra_fields=None):
        annotation = OrderedDict([
            ("{}_{}".format(agg.default_alias, i), agg)
            for i, agg in enumerate(aggregates)
        ])

        fields = list(annotation.keys())
        fields = [Ref(f, annotation[f]) for f in fields]

        if extra_fields is not None:
            fields += [F(f) for f in extra_fields]
        else:
            fields.append(F(field))

        return self.annotate(**annotation).order_by(*fields)

    def procedure_aggregate(self, procname, *args, **kwargs):
        """Helper method for generating ordering annotations.

        Returns:
            anubis.sql_aggregators.ProcedureOrderingAnnotation: An ordering
                annotation with the correct procedure name (including table
                name).
        """
        procname = "{}_{}".format(self.model._meta.db_table, procname)

        return ProcedureOrderingAnnotation(procname, *args, **kwargs)

    def procedure(self, procname, *args):
        """This method calls a procedure from the database.

        This method calls a procedure from the database. It expects the
        procedure to be name in the format "[table_name]_[procname]", and that
        it returns an array of primary keys. This is for composability with
        other queryset methods. For procedures that return arbitrary values,
        use :meth:`unchainable_procedure`.

        Note:
            Don't **ever** pass untreated user input values (or any values that
            cannot be implicitly trusted) to `procname`. Its value is not
            treated in anyway and **can be used for SQL-injection attacks**. If
            you must get the `procname` dinamically, set up a list of allowed
            names and check against that before calling this function.

        Args:
            procname (str): The name of the procedure, minus the starting
                "[table_name]_" prefix. **This value is not treated and can be
                used for SQL injection attacks**. Never pass untreated user
                input or any values that cannot be implicitly trusted to it.
            *args: Arguments to be passed to the procedure. These values will
                be passed as binding parameters in the SQL query, so they should
                be safe (but don't quote me on this).

        Returns:
            ProcedureQuerySet: A queryset containing the records whose primary
            keys match the ones in the array returned by the database stored
            procedure.
        """
        connection = self._get_connection()
        cursor = connection.cursor()

        procname = "{}_{}".format(self.model._meta.db_table, procname)
        procname = connection.ops.quote_name(procname)

        args = list(args)

        arg_marks = ["%s"] * len(args)
        arg_marks = ", ".join(arg_marks)

        query = "select * from {}({});".format(procname, arg_marks)

        cursor.execute(query, args)
        ids = [i[0] for i in cursor.fetchall()]

        return self.filter(id__in=ids)

    def unchainable_procedure(self, procname, *args):
        """Returns a result that is not a record and can't be chained"""
        connection = self._get_connection()
        cursor = connection.cursor()

        procname = "{}_{}".format(self.model._meta.db_table, procname)
        procname = connection.ops.quote_name(procname)

        args = list(args)

        arg_marks = ["%s"] * len(args)
        arg_marks = ", ".join(arg_marks)

        query = "select * from {}({});".format(procname, arg_marks)

        cursor.execute(query, args)

        result = [{k: v for k, v in zip(map(itemgetter(0), cursor.description),
                                        row)} for row in cursor.fetchall()]

        return result

    def single_valued_procedure(self, procname, *args):
        """Returns a single valued result."""
        connection = self._get_connection()
        cursor = connection.cursor()

        procname = "{}_{}".format(self.model._meta.db_table, procname)
        procname = connection.ops.quote_name(procname)

        args = list(args)

        arg_marks = ["%s"] * len(args)
        arg_marks = ", ".join(arg_marks)

        query = "select * from {}({});".format(procname, arg_marks)

        cursor.execute(query, args)

        return cursor.fetchone()[0]


def call_procedure(procname):
    def wrapper(self, *args):
        return self.procedure(procname, *args)

    wrapper.__name__ = procname

    return wrapper


def call_order_by_procedure(procname):
    def wrapper(self, *args, field='id', extra_fields=None):
        return self.order_by_procedure(procname, *args, field=field,
                                       extra_fields=extra_fields)

    wrapper.__name__ = procname

    return wrapper


def call_unchainable_procedure(procname):
    def wrapper(self, *args):
        return self.unchainable_procedure(procname, *args)

    wrapper.__name__ = procname

    return wrapper


def call_single_valued_procedure(procname):
    def wrapper(self, *args):
        return self.single_valued_procedure(procname, *args)

    wrapper.__name__ = procname

    return wrapper
