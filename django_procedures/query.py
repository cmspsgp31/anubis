# Copyright (C) 2014, Ugo Pozo 2014, Câmara Municipal de São Paulo

# query.py - extensões para queries do Django.

# Este arquivo é parte do software django-procedures.

# django-procedures é um software livre: você pode redistribuí-lo e/ou
# modificá-lo sob os termos da Licença Pública Geral GNU (GNU General Public
# License), tal como é publicada pela Free Software Foundation, na
# versão 3 da licença, ou (sua decisão) qualquer versão posterior.

# django-procedures é distribuído na esperança de que seja útil, mas SEM NENHUMA
# GARANTIA; nem mesmo a garantia implícita de VALOR COMERCIAL ou ADEQUAÇÃO PARA
# UM PROPÓSITO EM PARTICULAR. Veja a Licença Pública Geral GNU para mais
# detalhes.

# Você deve ter recebido uma cópia da Licença Pública Geral GNU junto com este
# programa. Se não, consulte <http://www.gnu.org/licenses/>.

from django.db import models
from django.db.models import query
from django.db import connection, connections
from operator import itemgetter

def extend_manager(qs_cls):
	methods = [m for m in dir(qs_cls) if not m in dir(ProcedureQuerySet)]

	class ExtendedManager(ProcedureManager):
		_extended_methods = methods
		_queryset_class = qs_cls

		def get_queryset(self):
			return self._queryset_class(self.model, using=self._db)

		def __getattr__(self, attr):
			if attr in self._extended_methods:
				queryset = self.get_queryset()
				return getattr(queryset, attr)
			else:
				raise AttributeError()

	return ExtendedManager()

def call_procedure(procname):
	def wrapper(self, *args):
		return self.procedure(procname, *args)

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

class ProcedureQuerySet(query.QuerySet):
	def _get_connection(self):
		if self.db is not None:
			conn = connections[self.db]
		else:
			conn = connection

		return conn

	def procedure(self, procname, *args):
		connection = self._get_connection()
		cursor = connection.cursor()

		procname = "{}_{}".format(self.model._meta.db_table, procname)
		procname = connection.ops.quote_name(procname)

		args = list(args)

		qm = ["%s"] * len(args)
		qm = ", ".join(qm)

		query = "select * from {}({});".format(procname, qm)

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

		qm = ["%s"] * len(args)
		qm = ", ".join(qm)

		query = "select * from {}({});".format(procname, qm)

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

		qm = ["%s"] * len(args)
		qm = ", ".join(qm)

		query = "select * from {}({});".format(procname, qm)

		cursor.execute(query, args)

		return cursor.fetchone()[0]
		

class ProcedureManager(models.Manager):
	def get_queryset(self):
		return ProcedureQuerySet(self.model, using=self._db)

	def procedure(self, procname, *args):
		return self.get_queryset().procedure(procname, *args)

	def unchainable_procedure(self, procname, *args):
		return self.get_queryset().unchainable_procedure(procname, *args)

	def single_valued_procedure(self, procname, *args):
		return self.get_queryset().single_valued_procedure(procname, *args)

