# Copyright (C) 2014, Ugo Pozo
#               2014, Câmara Municipal de São Paulo

# operations.py - operações de migração customizadas para o ROBOKits.

# Este arquivo é parte do software ROBOKits.

# ROBOKits é um software livre: você pode redistribuí-lo e/ou modificá-lo
# sob os termos da Licença Pública Geral GNU (GNU General Public License),
# tal como é publicada pela Free Software Foundation, na versão 3 da
# licença, ou (sua decisão) qualquer versão posterior.

# ROBOKits é distribuído na esperança de que seja útil, mas SEM NENHUMA
# GARANTIA; nem mesmo a garantia implícita de VALOR COMERCIAL ou ADEQUAÇÃO
# PARA UM PROPÓSITO EM PARTICULAR. Veja a Licença Pública Geral GNU para
# mais detalhes.

# Você deve ter recebido uma cópia da Licença Pública Geral GNU junto com
# este programa. Se não, consulte <http://www.gnu.org/licenses/>.

from django.db.migrations.operations.base import Operation

class LoadExtension(Operation):
	reduces_to_sql = True
	reversible = True

	def __init__(self, name):
		self.name = name

	def state_forwards(self, app_label, state):
		pass

	def database_forwards(self, app_label, schema_editor, from_state, to_state):
		schema_editor.execute("create extension if not exists %s" % self.name)

	def database_backwards(self, app_label, schema_editor, from_state, to_state):
		schema_editor.execute("drop extension %s" % self.name)

	def describe(self):
		return "Creates extension %s" % self.name


class AddConstraint(Operation):
	reduces_to_sql = True
	reversible = True

	def __init__(self, table_name, constraint_name, sql):
		self.table_name = table_name
		self.constraint_name = "{}_{}".format(table_name, constraint_name)
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


class AddFunction(Operation):
	reduces_to_sql = True
	reversible = True

	def __init__(self, table_name, function_name, arguments,
			return_value, function_body):
		self.table_name = table_name
		self.arguments = ", ".join(arguments)
		self.function_name = "{}_{}".format(table_name, function_name)
		self.return_value = return_value
		self.function_body = function_body

	def get_full_name(self):
		return "{}({})".format(self.function_name, self.arguments)

	def get_full_body(self):
		sql = """
			create or replace function {full_name}
			returns {return_value} as $$
			begin
				{function_body}
			end;
			$$ language plpgsql;
		"""

		return sql.format \
			( full_name=self.get_full_name()
			, return_value=self.return_value
			, function_body=self.function_body
			)

	def state_forwards(self, app_label, state):
		pass

	def database_forwards(self, app_label, schema_editor, from_state, to_state):
		body = self.get_full_body()
		# print(body)
		schema_editor.execute(body)

	def database_backwards(self, app_label, schema_editor, from_state,
			to_state):

		schema_editor.execute("drop function {};".format(self.get_full_name()))

	def describe(self):
		return "Creates function {}.".format(self.get_full_name())

class AddSearchFunction(AddFunction):
	reduces_to_sql = True
	reversible = True

	def __init__(self, table_name, function_name, arguments, query):
		return_value = "table(id int)"
		function_body = "return query {}".format(query)

		super().__init__(table_name, function_name, arguments, return_value,
			function_body)





