# Copyright © 2016, Ugo Pozo
#             2016, Câmara Municipal de São Paulo

# state_view_mixin.py - a mixin for views that perform searches.

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
This module contains the StateViewMixin, a mixin designed for creating API views
that perform searches on the database.
"""

from collections import OrderedDict
from functools import reduce

from rest_framework.response import Response
from rest_framework import serializers as rest_serializers
from rest_framework.decorators import api_view
from rest_framework.renderers import JSONRenderer

from django.conf.urls import url
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.core.exceptions import ImproperlyConfigured
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _
from django import forms

from anubis.aggregators import QuerySetAggregator, ListAggregator
from anubis.filters import ConversionFilter
from anubis.url import BooleanBuilder
from anubis.forms import FieldSerializer

class StateViewMixin:
    """A mixin that performs a search and adds the result to the view context.

    This mixin reads from a supposedly pre-filled :attr:`kwargs` attribute,
    performs a search on the database based on the supplied configuration and
    search parameters provided, and attaches the result to the view context.
    It's designed to be used as a mixin for either the Django's generic
    :class:`ListView` or Django Rest Framework's generic :class:`ListAPIView`
    - hence why it's a mixin and not a child class. Both of these classes will
    fill the kwargs argument accordingly.

    Specifically, :class:`StateViewMixin` should be explicitly used only with a
    :class:`ListAPIView`. If you're building an HTML view, this class's child
    :class:`AppViewMixin` will contain information that can prove to be
    more useful.

    :ivar is_paginated: Tells whether the search is to be paginated.
    :vartype is_paginated: bool

    :ivar is_multi_modeled: Tells whether the search acts in multiple models.
    :vartype bool:

    :ivar is_sortable: Tell whether the search can be sorted.
    :vartype bool:

    :ivar boolean_expression: Represents the requested search, if there is one.
    :vartype Optional[rest_framework.serializers.ModelSerializer]:


    Attributes:
        base_url (str): Base URL for the application. Should either start with
            a slash or with a protocol reference (i.e., "http://..."). It should
            **not** end with a slash, though, and to reference the root URL you
            should leave this attribute **empty**.
        model: This attribute can either be a :class:`dict` for multi-model
            searches or a direct reference to the Django model in single-model
            searches. In a single-model setting, you can access the model class
            from either `self.models['_default']` or `self.model`. In a
            multi-model setting, `self.model` will point to the model of the
            current search after `self.kwargs` is processed.
        serializers: This attribute can either be a :class:`dict` for
            multi-model searches or a 2-tuple of serializers, where the
            first serializer applies to searches and the second to details. In
            a multi-modeled enviroment, keys are to be the same as those in the
            :attr:`model` attribute, and values are the aforementioned 2-tuple
            of serializers.
        default_model (Optional[str]): In non-search requests in multi-modeled
            views there is no pre-selected model, which causes Django's
            :method:`ListView.get_queryset` to go haywire. Use this property to
            define a default model for searching, which also will be
            pre-selected in the search interface. The value of this property is
            the key of the default model inside the :attr:`model` dictionary.
        model_parameter (str): The parameter *name* (from Django URL matching)
            which contains the key of the model in the :class:`dict` on the
            :attr:`model` attribute. Ignored in single-model searches.
        expression_parameter (str): The parameter *name* (from Django URL
            matching) which contains the boolean expression with which to build
            a :class:`QuerySet` to search the database.
        filters (Dict[str, anubis.filters.Filter]): Allowed filters to perform
            searches. In a multi-model environment, there should be another
            level of nesting, and the top-level keys refers to the model keys.
        objects_per_page (Optional[int]): The number of objects per page of
            search. If it's set to :const:`None`, turns pagination off.
        page_parameter (str): The parameter *name* (from Django URL matching)
            which contains the number of the page to retrieve. If
            :attr:`objects_per_page` is set to :const:`None`, this attribute is
            ignored.
        user_serializer (Optional[rest_framework.serializers.Serializer]):
            Serializer for the user model. Set this to :const:`None` if you
            want to disable user related functionality.
        details_parameter (str): The parameter *name* (from Django URL
            matching) which contains the ID of the record being displayed.
            The Anubis' search interface will display this as a modal dialog
            above the search results (if there are any).
        details_slug (str): A slug to put on URLs when retrieving details.
        search_slug (str): A slug to put on URLs when performing searches.
        sorting_options (List[str]): A list of possible sorting options. Pass
            :const:`None` to disallow sorting.
        default_filter (str): The default filter to perform a search if text
            is entered on the filter selector area and a search is performed.
            If :const:`None`, defaults to the first key of the first model.
    """

    base_url = ""
    api_prefix = "api"

    model = None
    default_model = None
    model_parameter = "model"

    serializers = None

    expression_parameter = "search"
    filters = {}
    default_filter = None

    objects_per_page = None
    page_parameter = "page"

    details_parameter = "details"
    details_slug = "details"

    search_slug = "search"

    sorting_options = None
    sorting_parameter = "sorted_by"
    sorting_default = None

    sidebar_links = []
    sidebar_links_title = "More links"

    actions = None

    group_by = None


    class _UserSerializer(rest_serializers.ModelSerializer):
        profile_link = rest_serializers.SerializerMethodField()

        class Meta:
            model = User
            fields = ('username', 'first_name', 'last_name', 'email',
                      'profile_link')

        def get_profile_link(self, obj):
            return reverse('admin:auth_user_change', args=[obj.id])



    user_serializer = _UserSerializer

    @classmethod
    def autocomplete_model(cls, model, filter_, describe=None):
        model_name = model.__name__.lower()

        if describe is None:
            describe = str

        @api_view(['GET'])
        def view(request, needle):
            queryset = filter_.filter_queryset(model.objects.all(), [needle])

            return Response([[record.id, describe(record)]
                             for record in queryset])

        url_string = (r"^{api_prefix}/anubis_autocomplete/{model_name}/"
                      r"(?P<needle>.*)").format(**{
                          "api_prefix": cls.api_prefix,
                          "model_name": model_name,
                      })

        url_name = "anubis_autocomplete_{model_name}" \
            .format(model_name=model_name)

        return url(url_string, view, name=url_name)

    @classmethod
    def autocomplete_url(cls, app, model):
        model_name = model.__name__.lower()
        url_name = "{app}:anubis_autocomplete_{model_name}" \
            .format(app=app, model_name=model_name)

        return reverse(url_name, kwargs={'needle': ""})

    @classmethod
    def _is_multi_modeled(cls):
        return not isinstance(cls.model, type)

    @classmethod
    def _is_paginated(cls):
        return cls.objects_per_page is not None

    @classmethod
    def _is_sortable(cls):
        return cls.sorting_options is not None

    @classmethod
    def _url_part_details_id(cls):
        return r'(?P<{}>[^/,"]+)'.format(cls.details_parameter)

    @classmethod
    def _url_part_model(cls):
        if cls._is_multi_modeled():
            models = "|".join(dict(cls.model).keys())
            return r"(?P<{}>{})/".format(cls.model_parameter, models)
        else:
            return ""

    @classmethod
    def _url_part_page(cls):
        if cls._is_paginated():
            return r"(?P<{}>\d+)/".format(cls.page_parameter)
        else:
            return ""

    @classmethod
    def _url_part_sort(cls):
        if cls._is_sortable():
            if cls._is_multi_modeled():
                options = [option[0] \
                           for options in cls.sorting_options.values() \
                           for option in options]
            else:
                options = [option[0] for option in cls.sorting_options]

            sorting = "|".join(set(options))
            return r"(?P<{}>[+-]({}))/".format(cls.sorting_parameter, sorting)
        else:
            return ""

    @classmethod
    def _url_part_expr(cls):
        return r"(?P<{}>.*)".format(cls.expression_parameter)

    @classmethod
    def url_search(cls, app_prefix=None,  **kwargs):
        if app_prefix is not None:
            app_prefix = "{}_".format(app_prefix)
        else:
            app_prefix = ""

        name = "{}api_search".format(app_prefix)

        search_url = "^{api_prefix}/{search_slug}/{m}{p}{s}{expr}$".format(**{
            "api_prefix": cls.api_prefix,
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

        name = "{}api_details".format(app_prefix)

        details_url = "^{api_prefix}/{details_slug}/{m}{id}$".format(**{
            "api_prefix": cls.api_prefix,
            "details_slug": cls.details_slug,
            "m": cls._url_part_model(),
            "id": cls._url_part_details_id()
        })

        return url(details_url, cls.as_view(**kwargs), name=name)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.is_paginated = self._is_paginated()
        self.is_multi_modeled = self._is_multi_modeled()
        self.is_sortable = self._is_sortable()
        self.boolean_expression = None
        self.action_result = None
        self.pagination_data = None

        self._sorting = {
            "by": None,
            "ascending": True
        }

        if self.is_multi_modeled:
            self._model_order = [model for model, _ in self.model]
            self._model_lookup = dict(self.model)
            self.model = None

            self._serializer_lookup = self.serializers
            self.serializers = None
        else:
            self._model_order = ["_default"]
            self._model_lookup = {'_default': self.model}
            self._model_key = "_default"

    def get(self, request, *args, **kwargs):
        self._prepare_attributes()

        return super().get(request, *args, **kwargs)

    def post(self, *args, **kwargs):
        self._prepare_attributes()

        self.perform_actions()

        return super().get(*args, **kwargs)

    def perform_actions(self):
        action_name = self.request.POST.get('action_name', None)
        action = self.actions.get(action_name, None)

        self.action_result = {
            'success': False,
            'result': None,
            'error': None
        }

        if action is None:
            self.action_result['error'] = "Action not found - {}" \
                .format(action_name)
            return

        if 'permissions' in action.keys() and action['permissions'] is not None:
            if not self.request.user.is_authenticated():
                self.action_result['error'] = "Usuário não autenticado."
                return

            if not all([self.request.user.has_perm(p)
                        for p in action['permissions']]):
                self.action_result['error'] = ("Usuário não possui as "
                                               "permissões necessárias.")
                return

        if self.is_multi_modeled and not self._model_key in action['models']:
            self.action_result['error'] = ("Wrong model.")
            return

        form = forms.Form(self.request.POST)

        form.fields['action_name'] = forms.CharField(required=True)
        form.fields['object_list'] = forms.CharField(required=True)

        for key, field in action['fields'].items():
            form.fields[key] = field

        if not form.is_valid():
            self.action_result['error'] = form.errors
            return

        if not hasattr(self, 'action_{}'.format(action_name)):
            self.action_result['error'] = "Wrong method."
            return

        method = getattr(self, 'action_{}'.format(action_name))

        try:
            success, result = method(form)
        except RuntimeError as error:
            self.action_result['error'] = error.args[0]
            return

        if success:
            self.action_result['success'] = True
            self.action_result['result'] = result
        else:
            self.action_result['error'] = result


    def _paginate_queryset(self, queryset):
        """A simplified paginator. It doesn't have to be as generic as Django's
        and DRF's are.

        Args:
            queryset (django.db.model.QuerySet): The queryset to paginate.

        Returns:
            django.core.paginator.Page: The current page object.

        Raises:
            ValueError: If you can't bother configure your URL pattern to only
                accept \\d+ in your "page" argument, you deserve an error.
        """
        paginator = Paginator(queryset, self.objects_per_page)
        page = int(self.kwargs.get(self.page_parameter, 1))

        return paginator.page(page)


    def list(self, request, *args, **kwargs):
        """Overrides DRF's implementation of listing. It's awful.

        DRF's implementation of listing is utterly inextensible. Both in 2.x
        and 3.x trunks (which we plan to support) it generates a serializer
        within the :method:`list` method and promptly throws it away, leaving
        us with only an useless :class:`Response` object, originated from the
        serializer's :attr:`data` attribute. We get no metadata from the
        serializer unless we do it ourselves, and that's what we're doing here.

        Args:
            request (django.http.request.HttpRequest): A request object, passed
                from Django.
            *args: Ordered arguments from the URL parsing algorithm.
            **kwargs: Named arguments from the URL parsing algorithm.

        Returns:
            rest_framework.response.Response: A JSON response including the
                whole of Anubis' state.
        """

        return Response(self.get_full_state())

    def get_full_state(self):
        self.object_list = self.get_queryset()
        state = self.get_state()

        return state

    def get_serialized_queryset(self, queryset):
        if self.group_by is None:
            return self.get_serializer(queryset, many=True).data

        groupers = [getattr(self, "group_by_{}".format(g), None)
                    for g in self.group_by]

        group_count = len(groupers)

        if None in groupers:
            return self.get_serializer(queryset, many=True).data

        data = OrderedDict()

        for obj in queryset:
            groups = [grouper(obj) for grouper in groupers]

            branch = data

            for i, group in enumerate(groups):
                if i == group_count - 1:
                    leaf = branch.setdefault(group, [])
                else:
                    branch = branch.setdefault(group, OrderedDict())

            leaf.append(obj)

        data, _ = self._tree_serialize(data, 0)

        return data

    def _tree_serialize(self, node, depth):
        if isinstance(node, OrderedDict):
            serialized_node = []

            for group, subgroup in node.items():
                subgroup, leaf = self._tree_serialize(subgroup, depth + 1)

                serialized_node.append({
                    "__groupName": group,
                    "__leaf": leaf,
                    "__depth": depth,
                    "__items": subgroup
                })

            return serialized_node, False
        else:
            return self.get_serializer(node, many=True).data, True

    def get_queryset(self):
        try:
            original = super().get_queryset()
        except AssertionError:
            original = self.model.objects.all()

        if self.boolean_expression is not None:
            queryset = self.get_queryset_filter(original)
        else:
            queryset = original.none()

        queryset = self.sort_queryset(queryset)
        queryset = self.paginate_queryset(queryset)

        return queryset

    def sort_queryset(self, queryset):
        if not self.is_sortable or self.boolean_expression is None:
            return queryset

        sort_key = self.kwargs[self.sorting_parameter]
        ascending = not sort_key[0] == "-"
        sort_key = sort_key[1:]

        options = self.sorting_options if not self.is_multi_modeled \
            else self.sorting_options[self._model_key]

        assert sort_key in [i[0] for i in options], \
            "Sorting by {} is not allowed.".format(sort_key)

        self._sorting['by'] = sort_key
        self._sorting['ascending'] = ascending

        sort_method = "sort_by_{}".format(sort_key) \
            if not self.is_multi_modeled \
            else "sort_{}_by_{}".format(self._model_key, sort_key)

        return getattr(self, sort_method)(queryset, ascending)

    def paginate_queryset(self, queryset):
        if not self.is_paginated or self.boolean_expression is None:
            return queryset

        page = self._paginate_queryset(queryset)
        current_page = self.kwargs[self.page_parameter]

        def get_from_and_to(page_number):
            from_ = (page_number - 1) * self.objects_per_page + 1
            to_ = min(page_number * self.objects_per_page,
                      page.paginator.count)

            if page.paginator.count == 0:
                from_ = 0

            return (page_number, from_, to_)

        all_pages = [get_from_and_to(num) for num in page.paginator.page_range]

        self.pagination_data = {
            "currentPage": current_page,
            "allPages": all_pages,
            "recordCount": page.paginator.count,
            "nextPageNumber": page.next_page_number() \
                if page.has_next() else None,
            "previousPageNumber": page.previous_page_number() \
                if page.has_previous() else None,
        }

        return page.object_list



    def get_serializer_class(self):
        search_serializer, _ = self.serializers

        return search_serializer

    def get_details_serializer_class(self):
        _, details_serializer = self.serializers

        return details_serializer

    def _prepare_attributes(self):
        self.model = self.get_model()
        self.serializers = self.get_serializers()
        self.boolean_expression = self.get_boolean_expression()

    def get_model(self):
        if not self.is_multi_modeled:
            return self.model

        self._model_key = self.kwargs.get(self.model_parameter,
                                          self.default_model)

        return self._model_lookup[self._model_key]

    def get_serializers(self):
        if not self.is_multi_modeled:
            self._serializer_lookup = {"_default": self.serializers}

            return self.serializers

        return self._serializer_lookup[self._model_key]

    def get_boolean_expression(self):
        expression = self.kwargs.get(self.expression_parameter, None)

        if expression is None or expression == "":
            return None

        expression = expression.strip().rstrip("/")

        try:
            boolean = BooleanBuilder(expression).build()
        except ValueError:
            error = ValueError(_(("Check your expression for a missing "
                                  "connector, for instance.")))
            error.name = lambda: _("Syntax Error")
            raise error

        return boolean

    def get_filters(self):
        if not self.is_multi_modeled:
            return self.filters

        def check_conversion(filter_name, filter_):
            if not isinstance(filter_, type) or \
                    not issubclass(filter_, ConversionFilter):
                return filter_

            base_filter = None
            other_models = [key for key in self._model_lookup.keys() \
                          if key != self._model_key]

            for model_name in other_models:
                candidate = self.filters[model_name][filter_name]

                if not isinstance(candidate, type) or \
                        not issubclass(candidate, ConversionFilter):
                    base_filter = candidate
                    break

            if base_filter is None:
                raise ImproperlyConfigured(('No base filter for filter "{}'
                                            '" applying to model "{}".').
                                           format(filter_name,
                                                  self._model_key))

            return filter_(base_filter)

        filters = self.filters[self._model_key]

        return {filter_name: check_conversion(filter_name, filter_) \
                for filter_name, filter_ in filters.items()}

    def get_queryset_filter(self, queryset):
        """Gets a queryset and use the current :attr:`boolean_expression` to
        filter it.

        Args:
            queryset (django.db.models.QuerySet): A queryset to be filtered
            by the current :attr:`boolean_expression`.

        Returns:
            django.db.models.QuerySet: The filtered queryset.
        """
        aggregator = QuerySetAggregator(queryset, self.get_filters())

        return self.boolean_expression.traverse(aggregator)

    def get_state(self):
        anubis_state = {
            "searchResults": self.get_search_results(),
            "details": self.get_details(),
        }

        return anubis_state

    def get_details(self):
        details_id = self.kwargs.get(self.details_parameter, None)

        if details_id is not None:
            try:
                details_obj = self.model.objects.get(pk=details_id)
            except self.model.DoesNotExist:
                details_obj = None
            else:
                context = {"request": self.request}

                serializer = self \
                    .get_details_serializer_class()(details_obj,
                                                    context=context)

                details_obj = serializer.data

            return {"object": details_obj, "model": self._model_key}
        else:
            return None

    def get_search_results(self):
        # TODO: textExpression should be computed from the parsed
        # boolean_expression.

        aggregator = ListAggregator(self.get_filters())
        visible = self.boolean_expression is not None

        expression = self.boolean_expression.traverse(aggregator) \
            if visible else []

        for i, unit in enumerate(expression):
            unit.update({"index": i})


        results = {
            "position": len(expression),
            "expression": expression,
            "textExpression": self.kwargs.get(self.expression_parameter, ""),
            "pagination": self.get_pagination(),
            "actions": self.get_actions() if visible else {},
            "visible": visible,
            "model": self._model_key,
            "results": self.get_serialized_queryset(self.object_list),
            "sorting": self.get_sorting(),
            "selection": []
        }

        if self.action_result is not None:
            results["actionResult"] = self.action_result

        return results

    def get_pagination(self):
        return self.pagination_data

    def get_actions(self):
        if self.actions is None:
            return {}

        if self.user_serializer is None:
            return {}

        actions = {key: dict(a) for key, a in self.actions.items()
                   if (not self.is_multi_modeled or
                       self._model_key in a['models']) and (
                           a.get('permissions', None) is None or
                           self.request.user.is_authenticated() and all([
                               self.request.user.has_perm(p)
                               for p in a['permissions']])
                       )
                  }

        for key in list(actions.keys()):
            action = actions[key]
            action['fields'] = {k: self.render_field(f)
                                for k, f in action['fields'].items()}

        return actions

    def get_sorting(self):
        if self.is_sortable:
            options = self.sorting_options if self.is_multi_modeled else {
                "_default": self.sorting_options
            }
            default = self.sorting_default if self.is_multi_modeled else {
                "_default": self.sorting_default
            }
        else:
            options = None
            default = None

        return {
            "available": options,
            "current": self._sorting,
            "default": default
        }

    def get_final_response(self, original):
        return self.get_context_data()

    def render_field(self, field):
        return FieldSerializer(field).data

