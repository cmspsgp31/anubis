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
				if char == "\\":
					i, char = advance(i, filter_)
					elem += char
				elif char == "\"":
					while not char == "," and i < len(filter_):
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
	allowed_procedures = ()

	def filter_queryset(self, queryset, url):
		assert isinstance(queryset, ProcedureQuerySet)

		url = url.strip()
		url = url.rstrip("/")

		for filter_ in url.split("/{}/".format(self.prefix)):
			args = _parse_filter(filter_)

			if len(args):
				queryset = self._apply_filter(queryset, args)

		return queryset

	def _apply_filter(self, queryset, args):
		procedure_name = args.pop(0)

		if not procedure_name in self.allowed_procedures:
			raise ValueError("{} is not an allowed procedure." \
				.format(procedure_name))

		return queryset.procedure(procedure_name, args)

