# Copyright (C) 2014, Ugo Pozo
#               2014, Câmara Municipal de São Paulo

# triggers.py - operações de migração de gatilhos de PostgreSQL.

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
    Operações de migração de gatilhos de PostgreSQL.
"""

from django.db.migrations.operations.base import Operation

class AddTrigger(Operation):
    reduces_to_sql = True
    reversible = True

    class On:
        UPDATE = 1 << 0
        INSERT = 1 << 1
        DELETE = 1 << 2
        ALL = UPDATE | INSERT | DELETE

        _list = [("update", UPDATE),
                 ("insert", INSERT),
                 ("delete", DELETE)
                ]

    def __init__(self, model, name, commands, **kwargs):
        self.model = model
        self.table_name = self.model._meta.db_table
        self.name = "{}_{}_trigger".format(self.table_name, name)
        self.function_name = "{}_{}_fn()".format(self.table_name, name)
        self._events = kwargs.get("on", self.On.ALL)
        self.commands = commands
        self.when = "after" if kwargs.get("after", True) else "before"
        self.row_level = "for each row" if kwargs.get("row_level", False) \
                                        else ""
        self.condition = "" if kwargs.get("condition", None) is None \
                            else "when ( {} )".format(kwargs["condition"])

    @property
    def events(self):
        events = [event for event, mask in self.On._list
                  if self._events & mask]

        return " or ".join(events)

    def _sql(self):
        sql = """
            create function {function_name} returns trigger
            language 'plpgsql' as $$
            begin
                {commands}
                return null;
            end
            $$;

            create trigger {name} {when} {events} on "{table}" {row_level} execute procedure {function_name};
        """.format(function_name=self.function_name, commands=self.commands,
                   name=self.name, when=self.when, events=self.events,
                   table=self.table_name, row_level=self.row_level)

        return sql

    def state_forwards(self, app_label, state):
        pass

    def database_forwards(self, app_label, schema_editor, from_state,
                          to_state):
        schema_editor.execute(self._sql())

    def database_backwards(self, app_label, schema_editor, from_state,
                           to_state):
        sql = """
            drop trigger if exists {name} on {table} cascade;
            drop function if exists {function_name};
        """.format(name=self.name, function_name=self.function_name,
                   table=self.table_name)

        schema_editor.execute(sql)

    def describe(self):
        return "Creates trigger {} and corresponding function {}." \
               .format(self.name, self.function_name)


class AddTableTrigger(AddTrigger):
    reduces_to_sql = True
    reversible = True

    def __init__(self, table_name, name, commands, **kwargs):
        self.model = None
        self.table_name = table_name
        self.name = "{}_{}_trigger".format(self.table_name, name)
        self.function_name = "{}_{}_fn()".format(self.table_name, name)
        self._events = kwargs.get("on", AddTrigger.On.ALL)
        self.commands = commands
        self.when = "after" if kwargs.get("after", True) else "before"
        self.row_level = "for each row" if kwargs.get("row_level", False) \
                                        else ""
        self.condition = "" if kwargs.get("condition", None) is None \
                            else "when ( {} )".format(kwargs["condition"])


class AddRefreshMaterializedViewTrigger(AddTrigger):
    reduces_to_sql = True
    reversible = True

    def __init__(self, trigger_model, materialized_view_model,
                 materialized_view_name):
        view_name = "{}_{}".format(materialized_view_model._meta.db_table,
                                   materialized_view_name)

        commands = "refresh materialized view {};".format(view_name)

        super().__init__(trigger_model, "refresh_{}".format(view_name),
                         commands)


class AddRefreshMaterializedViewTableTrigger(AddTableTrigger):
    reduces_to_sql = True
    reversible = True

    def __init__(self, trigger_table, materialized_view_model,
                 materialized_view_name):
        view_name = "{}_{}".format(materialized_view_model._meta.db_table,
                                   materialized_view_name)

        commands = "refresh materialized view {};".format(view_name)

        super().__init__(trigger_table, "refresh_{}".format(view_name),
                         commands)
