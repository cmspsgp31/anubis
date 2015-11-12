# Copyright (C) 2014, Ugo Pozo
#               2014, Câmara Municipal de São Paulo

# __init__.py - operações de migração do PostgreSQL para Anubis.

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
    Operações de migração do PostgreSQL para Anubis.
"""

from anubis.operations.indexes import AddCustomIndex, AddCustomViewIndex, \
    AddTrigramIndex

from anubis.operations.constraints import AddConstraint, AddCheckConstraint, \
    AddStartBeforeEndConstraint, AddGistConstraint, \
    AddNoDateRangeOverlappingConstraint

from anubis.operations.functions import AddFunction, AddSearchFunction, \
    AddSortFunction, AddDateSortFunction

from anubis.operations.views import AddView, AddMaterializedView

from anubis.operations.triggers import AddTrigger, AddTableTrigger, \
    AddRefreshMaterializedViewTrigger, AddRefreshMaterializedViewTableTrigger

__all__ = ["AddCustomIndex",
           "AddCustomViewIndex",
           "AddTrigramIndex",
           "AddConstraint",
           "AddCheckConstraint",
           "AddStartBeforeEndConstraint",
           "AddGistConstraint",
           "AddNoDateRangeOverlappingConstraint",
           "AddFunction",
           "AddSearchFunction",
           "AddSortFunction",
           "AddDateSortFunction",
           "AddView",
           "AddMaterializedView",
           "AddTrigger",
           "AddTableTrigger",
           "AddRefreshMaterializedViewTrigger",
           "AddRefreshMaterializedViewTableTrigger"
          ]


