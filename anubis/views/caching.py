# Copyright © 2016, Ugo Pozo
#             2016, Câmara Municipal de São Paulo

# caching.py - caching related views.

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

class NoCacheMixin:
    def get(self, *args, **kwargs):
        response = super().get(*args, **kwargs)

        response['Cache-Control'] = "no-cache, no-store, must-revalidate"
        response['Pragma'] = "no-cache"
        response['Expires'] = "0"

        return response

