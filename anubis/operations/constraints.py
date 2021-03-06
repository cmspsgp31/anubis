# Copyright (C) 2014, Ugo Pozo
#               2014, Câmara Municipal de São Paulo

# constraints.py - operações de migração de restrições de PostgreSQL.

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

"""
    Operações de migração de restrições de PostgreSQL.
"""

from django.db.migrations.operations.base import Operation


class AddConstraint(Operation):
    reduces_to_sql = True
    reversible = True

    def __init__(self, model, constraint_name, sql):
        self.model = model
        self.table_name = self.model._meta.db_table
        self.constraint_name = "{}_{}".format(self.table_name, constraint_name)
        self.sql = sql

    def state_forwards(self, app_label, state):
        pass

    def database_forwards(self, app_label, schema_editor, from_state,
                          to_state):
        query = """
            alter table if exists \"{table}\"
                add constraint \"{constraint}\" {text};
        """

        query = query.format(table=self.table_name,
                             constraint=self.constraint_name, text=self.sql)

        schema_editor.execute(query)

    def database_backwards(self, app_label, schema_editor, from_state,
                           to_state):
        query = """
            alter table if exists \"{table}\"
                drop constraint if exists \"{constraint}\" cascade;
        """
        query = query.format(table=self.table_name,
                             constraint=self.constraint_name)

        schema_editor.execute(query)

    def describe(self):
        return "Add constraint {} to table {}".format(self.constraint_name,
                                                      self.table_name)


class AddCheckConstraint(AddConstraint):
    reduces_to_sql = True
    reversible = True

    def __init__(self, table_name, constraint_name, comparison):
        sql = "check ( {} )".format(comparison)
        super().__init__(table_name, constraint_name, sql)


class AddStartBeforeEndConstraint(AddCheckConstraint):
    reduces_to_sql = True
    reversible = True

    def __init__(self, table_name, lesser="start_date", greater="end_date"):
        super().__init__(table_name, "start_before_end",
                         '"{}" < "{}"'.format(lesser, greater))


class AddGistConstraint(AddConstraint):
    reduces_to_sql = True
    reversible = True

    def __init__(self, table_name, constraint_name, expressions,
                 condition=None):
        expr = ",".join(["{} with {}".format(expr, oper)
                         for expr, oper in expressions])

        if condition is None:
            where = ""
        else:
            where = " where {}".format(condition)

        sql = "exclude using gist ( {} ){};".format(expr, where)

        super().__init__(table_name, constraint_name, sql)


class AddNoDateRangeOverlappingConstraint(AddGistConstraint):
    reduces_to_sql = True
    reversible = True

    def __init__(self, table_name, restraint_field=None,
                 start_date="start_date", end_date="end_date", coalesce=True,
                 condition=None):

        if coalesce:
            end_date = "coalesce({}, 'infinity'::date)".format(end_date)

        expressions = [("daterange({}, {})".format(start_date, end_date),
                        "&&")]

        if restraint_field is not None:
            expressions.insert(0, (restraint_field, "="))

        super().__init__(table_name, "no_overlapping", expressions, condition)
