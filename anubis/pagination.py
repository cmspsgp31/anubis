# Copyright (C) 2014, Ugo Pozo
#               2014, Câmara Municipal de São Paulo

# pagination.py - paginação automatizada para API Views.

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


class ContextSerializerMixin:
    _original_object_name = "data"

    @property
    def data(self):
        extra_data = self.context.get("extra_data", None)
        original_data = super().data

        if extra_data is not None:
            data = dict(extra_data)
            data.update({self._original_object_name: original_data})
        else:
            data = original_data

        return data
