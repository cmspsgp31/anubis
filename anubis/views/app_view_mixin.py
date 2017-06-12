# Copyright © 2016, Ugo Pozo
#             2016, Câmara Municipal de São Paulo

# app_view_mixin.py - mixin for providing a view for the basic search interface.

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

"""
This module contains views, mixins and helpers to define views that use
Anubis's facilities to perform searches.
"""

from rest_framework.renderers import JSONRenderer

from django.conf.urls import url
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _

from .state_view_mixin import StateViewMixin
from .caching import CachedSearchMixin

class AppViewMixin(StateViewMixin):
    record_zoom = "record_zoom"
    record_list = "record_list"
    app_theme = "app_theme"
    extra_control = None
    no_user_text = ""

    @classmethod
    def url_search(cls, app_prefix=None, **kwargs):
        if app_prefix is not None:
            app_prefix = "{}_".format(app_prefix)
        else:
            app_prefix = ""

        name = "{}html_search".format(app_prefix)

        search_url = "^{search_slug}/{m}{p}{s}{expr}$".format(**{
            "search_slug": cls.search_slug,
            "m": cls._url_part_model(),
            "p": cls._url_part_page(),
            "s": cls._url_part_sort(),
            "expr": cls._url_part_expr()
        })

        return url(search_url, cls.as_view(**kwargs), name=name)

    @classmethod
    def url_details(cls, app_prefix=None, **kwargs):
        if app_prefix is not None:
            app_prefix = "{}_".format(app_prefix)
        else:
            app_prefix = ""

        name = "{}html_details".format(app_prefix)

        details_url = "^{details_slug}/{m}{id}$".format(**{
            "details_slug": cls.details_slug,
            "m": cls._url_part_model(),
            "id": cls._url_part_details_id()
        })

        return url(details_url, cls.as_view(**kwargs), name=name)

    @classmethod
    def url_search_and_details(cls, app_prefix=None, **kwargs):
        if app_prefix is not None:
            app_prefix = "{}_".format(app_prefix)
        else:
            app_prefix = ""

        name = "{}html_search_and_details".format(app_prefix)

        s_and_d_url = ("^{details_slug}/{m}{id}/"
                       "{search_slug}/{p}{s}{expr}$").format(**{
                           "details_slug": cls.details_slug,
                           "m": cls._url_part_model(),
                           "id": cls._url_part_details_id(),
                           "search_slug": cls.search_slug,
                           "p": cls._url_part_page(),
                           "s": cls._url_part_sort(),
                           "expr": cls._url_part_expr(),
                       })

        return url(s_and_d_url, cls.as_view(**kwargs), name=name)

    def get(self, request, *args, **kwargs):
        self._prepare_attributes()

        context = self.get_context_data()

        return self.render_to_response(context)

    def get_state(self):
        base_state = dict(super().get_state())

        base_state.update({
            "tokenEditor": self.get_token_state(),
            "applicationData": self.get_application_data(),
            "models": self.get_models_meta(),
            "user": self.get_user_data(),
            "templates": self.get_templates(),
       })

        if self.user_serializer is None:
            base_state["noUserText"] = self.no_user_text

        return base_state

    def get_serializer(self, *args, **kwargs):
        kwargs["context"] = self.get_serializer_context()
        return self.get_serializer_class()(*args, **kwargs)

    def get_serializer_context(self):
        return {
            'request': self.request,
            'view': self
        }

    def get_context_data(self, **kwargs):
        if not hasattr(self, 'object_list'):
            self.object_list = []

        context = dict(super().get_context_data(**kwargs))
        full_state = self.get_full_state()

        context["anubis_state"] = JSONRenderer().render(full_state)

        return context

    def get_models_meta(self):
        return {key: {"names": (model._meta.verbose_name.title(),
                                model._meta.verbose_name_plural.title()),
                      "order": self._model_order.index(key)
                     }
                for key, model in self._model_lookup.items()}

    def get_user_data(self):
        if self.user_serializer is None:
            return None

        return self.user_serializer(self.request.user).data \
            if self.request.user.is_authenticated() else {}

    def get_templates(self):
        from django.template.loader import get_template

        def render(template):
            return get_template("{}.js".format(template)).render()

        extra_control = None

        if self.is_multi_modeled:
            if hasattr(self.record_zoom, "items"):
                record_zoom = {model: render(template) for model, template
                               in self.record_zoom.items()}
            else:
                rendered = render(self.record_zoom)
                record_zoom = {model: rendered
                               for model in self._model_lookup.keys()}

            if hasattr(self.record_list, "items"):
                record_list = {model: render(template) for model, template
                               in self.record_list.items()}
            else:
                rendered = render(self.record_list)
                record_list = {model: rendered
                               for model in self._model_lookup.keys()}

            if self.extra_control is not None:
                if hasattr(self.extra_control, "items"):
                    extra_control = {model: render(template)
                                     for model, template
                                     in self.extra_control.items()}
                else:
                    rendered = render(self.extra_control)
                    extra_control = {model: rendered
                                     for model in self._model_lookup.keys()}

        else:
            record_zoom = {"_default": render(self.record_zoom)}
            record_list = {"_default": render(self.record_list)}

            if self.extra_control is not None:
                extra_control = {"_default": render(self.extra_control)}


        return {
            "extraControl": extra_control,
            "record": record_zoom,
            "search": record_list,
            "appTheme": render(self.app_theme)
        }

    def get_token_state(self):
        return {
            "canSearch": True,
            "shouldSearch": False,
            "fieldsets": self.get_fieldsets(),
            "counter": 1000000000,
        }

    def get_application_data(self):
        react_search_route = "{}/{}{}{}{}".format(
            self.search_slug,
            ":model/" if self.is_multi_modeled else "",
            ":page/" if self.is_paginated else "",
            ":sorting/" if self.is_sortable else "",
            "*"
        )

        react_search_html = "{}/{}/{}{}{}{}".format(
            self.base_url if not self.base_url == "/" else "",
            self.search_slug,
            "${model}/" if self.is_multi_modeled else "",
            "${page}/" if self.is_paginated else "",
            "${sorting}/" if self.is_sortable else "",
            "${expr}"
        )

        react_search_api = "{}/{}/{}/{}{}{}{}".format(
            self.base_url if not self.base_url == "/" else "",
            self.api_prefix,
            self.search_slug,
            "${model}/" if self.is_multi_modeled else "",
            "${page}/" if self.is_paginated else "",
            "${sorting}/" if self.is_sortable else "",
            "${expr}"
        )

        react_details_route = "{}/{}{}".format(
            self.details_slug,
            ":model/" if self.is_multi_modeled else "",
            ":id"
        )

        react_details_html = "{}/{}/{}{}".format(
            self.base_url if not self.base_url == "/" else "",
            self.details_slug,
            "${model}/" if self.is_multi_modeled else "",
            "${id}"
        )

        react_details_api = "{}/{}/{}/{}{}".format(
            self.base_url if not self.base_url == "/" else "",
            self.api_prefix,
            self.details_slug,
            "${model}/" if self.is_multi_modeled else "",
            "${id}"
        )

        react_search_and_details_route = "{}/{}{}/{}/{}{}{}".format(
            self.details_slug,
            ":model/" if self.is_multi_modeled else "",
            ":id",
            self.search_slug,
            ":page/" if self.is_paginated else "",
            ":sorting/" if self.is_sortable else "",
            "*"
        )

        react_search_and_details_html = "{}/{}/{}{}/{}/{}{}{}".format(
            self.base_url if not self.base_url == "/" else "",
            self.details_slug,
            "${model}/" if self.is_multi_modeled else "",
            "${id}",
            self.search_slug,
            "${page}/" if self.is_paginated else "",
            "${sorting}/" if self.is_sortable else "",
            "${expr}"
        )

        react_search_and_details_api = "{}/{}/{}/{}{}/{}/{}{}{}".format(
            self.base_url if not self.base_url == "/" else "",
            self.api_prefix,
            self.details_slug,
            "${model}/" if self.is_multi_modeled else "",
            "${id}",
            self.search_slug,
            "${page}/" if self.is_paginated else "",
            "${sorting}/" if self.is_sortable else "",
            "${expr}"
        )

        sorting_default = self.sorting_default
        default_model = self.default_model

        if not self.is_multi_modeled:
            sorting_default = {"_default": self.sorting_default}
            default_model = "_default"
        elif not self.is_sortable:
            sorting_default = dict.fromkeys(self._model_lookup.keys())

        return {
            "title": "Anubis Search Interface",
            "footer": ("© 2016-17, Câmara Municipal de São Paulo, "
                       "Secretaria de Documentação, "
                       "Equipe de Documentação do Legislativo."),
            "baseURL": self.base_url,

            "searchRoute": react_search_route,
            "searchHtml": react_search_html,
            "searchApi": react_search_api,

            "detailsRoute": react_details_route,
            "detailsHtml": react_details_html,
            "detailsApi": react_details_api,

            "searchAndDetailsRoute": react_search_and_details_route,
            "searchAndDetailsHtml": react_search_and_details_html,
            "searchAndDetailsApi": react_search_and_details_api,

            "defaultModel": default_model,
            "defaultFilter": self.get_default_filter(),

            "sortingDefaults": sorting_default,

            "sidebarLinks": {
                "list": self.sidebar_links,
                "title": self.sidebar_links_title,
                "admin": reverse('admin:index'),
                "password": reverse('admin:password_change'),
                "login": reverse('admin:login'),
                "logout": reverse('admin:logout'),
            },

        }

    def get_fieldsets(self):
        return {filter_name: {"description": filter_.description,
                              "fields": [self.render_field(filter_.fields[n]) \
                                         for n in filter_.field_keys],
                              }
                for filter_name, filter_ in self.get_filters().items()}

    def get_default_filter(self):
        if self.default_filter is not None:
            return self.default_filter

        keys = self.get_filters().keys()

        return keys[0]

