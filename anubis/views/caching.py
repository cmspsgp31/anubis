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

from django.core.cache import caches

class NoCacheMixin:
    def get(self, *args, **kwargs):
        response = super().get(*args, **kwargs)

        response['Cache-Control'] = "no-cache, no-store, must-revalidate"
        response['Pragma'] = "no-cache"
        response['Expires'] = "0"

        return response

class CachedSearchMixin:
    """Caches searches.


    Attributes:
        cache (str): Which cache to use. Set to :const:`None` to disable caching
            even if the view inherits from this class. Defaults to `"default"`.
    """

    cache = "default"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.is_cacheable = not self.cache is None
        self.is_api = False
        self.cache_key = None

    def _prepare_attributes(self):
        super()._prepare_attributes()

        self.is_cacheable = self.is_cacheable \
            and self.boolean_expression is not None \
            and not self.request.user.is_authenticated() # never cache auth'ed
                                                         # results

        if not self.is_cacheable:
            return

        key_builder = [self.expression_parameter]

        if self.is_paginated:
            key_builder.append(self.page_parameter)

        if self.is_multi_modeled:
            key_builder.append(self.model_parameter)

        if self.is_sortable:
            key_builder.append(self.sorting_parameter)

        self.cache_key = ":".join([self.kwargs.get(k, "") for k in key_builder])

    def list(self, request, *args, **kwargs):
        self.is_api = True

        return super().list(request, *args, **kwargs)

    def get_full_state(self):
        if not self.is_cacheable:
            return super().get_full_state()

        key = "api:" + self.cache_key if self.is_api else self.cache_key

        cache = caches[self.cache]

        cached_value = cache.get(key, None)

        if cached_value is None:
            state = super().get_full_state()

            cache.set(key, dict(state))
        else:
            state = dict(cached_value)

        return state





