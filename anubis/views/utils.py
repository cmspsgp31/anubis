# Copyright © 2016, Ugo Pozo
#             2016, Câmara Municipal de São Paulo

# utils.py - utility views.

# This file is part of Anubis.

# Anubis is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# Anubis is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

from rest_framework.views import exception_handler as rest_exception_handler
from rest_framework.response import Response

from django.conf import settings

def exception_handler(exc, context):
    response = rest_exception_handler(exc, context)

    if response is None:
        if hasattr(exc, "name") and callable(exc.name):
            name = exc.name()
        else:
            name = exc.__class__.__name__

        response = {
            "detail": str(exc),
            "name": name
        }

        if settings.DEBUG:
            import traceback

            response['traceback'] = traceback.format_tb(exc.__traceback__)

        response = Response(response)
    else:
        response.data["name"] = exc.__class__.__name__

    response.status_code = 500

    return response

