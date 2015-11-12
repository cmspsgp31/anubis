# Copyright (C) 2014, Ugo Pozo
#               2014, Câmara Municipal de São Paulo

# indexes.py - operações de migração de índices de PostgreSQL.

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
    Operações de migração de índices de PostgreSQL.
"""

from django.db.migrations.operations.base import Operation

class AddCustomIndex(Operation):
    reduces_to_sql = True
    reversible = True

    def __init__(self, model, index_name, sql):
        self.model = model
        self.table_name = self.model._meta.db_table
        self.index_name = "{}_{}".format(self.table_name, index_name)
        self.sql = sql

    def state_forwards(self, app_label, state):
        pass

    def database_forwards(self, app_label, schema_editor, from_state,
                          to_state):
        query = """
            create index {index} on {table} using {text};
        """

        query = query.format(table=self.table_name, index=self.index_name,
                             text=self.sql)

        schema_editor.execute(query)

    def database_backwards(self, app_label, schema_editor, from_state,
                           to_state):
        query = """
            drop index if exists {index} cascade;
        """
        query = query.format(index=self.index_name)

        schema_editor.execute(query)

    def describe(self):
        return "Add index {} to table {}".format(self.index_name,
                                                 self.table_name)


class AddCustomViewIndex(AddCustomIndex):
    reduces_to_sql = True
    reversible = True

    def __init__(self, model, view_name, index_name, sql):
        super().__init__(model, index_name, sql)
        self.table_name = "{}_{}".format(self.table_name, view_name)
        self.index_name = "{}_{}".format(self.table_name, index_name)

    def describe(self):
        return "Add index {} to view {}".format(self.index_name,
                                                self.table_name)


class AddTrigramIndex(AddCustomIndex):
    reduces_to_sql = True
    reversible = True

    def __init__(self, model, field_name):
        index_name = "{}_trgm_index".format(field_name)
        sql = "gist ({} gist_trgm_ops)".format(field_name)

        super().__init__(model, index_name, sql)

    def describe(self):
        return "Add trigram index {} to table {}".format(self.index_name,
                                                         self.table_name)
