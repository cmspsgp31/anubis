# Copyright (C) 2014, Ugo Pozo 2014, Câmara Municipal de São Paulo

# __init__.py - consolidação dos módulos contidos em django_procedures.

# Este arquivo é parte do software django-procedures.

# django-procedures é um software livre: você pode redistribuí-lo e/ou
# modificá-lo sob os termos da Licença Pública Geral GNU (GNU General Public
# 		License), tal como é publicada pela Free Software Foundation, na
# versão 3 da licença, ou (sua decisão) qualquer versão posterior.

# django-procedures é distribuído na esperança de que seja útil, mas SEM NENHUMA
# GARANTIA; nem mesmo a garantia implícita de VALOR COMERCIAL ou ADEQUAÇÃO PARA
# UM PROPÓSITO EM PARTICULAR. Veja a Licença Pública Geral GNU para mais
# detalhes.

# Você deve ter recebido uma cópia da Licença Pública Geral GNU junto com este
# programa. Se não, consulte <http://www.gnu.org/licenses/>.


from django_procedures import query, operations

__all__ = ['query', 'operations']
