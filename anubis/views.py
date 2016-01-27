# Copyright (C) 2014, Ugo Pozo
#               2014, Câmara Municipal de São Paulo

# views.py - views do Anubis

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
This module contains views, mixins and helpers to define views that use
Anubis's facilities to perform searches.
"""

import re

from functools import reduce

from rest_framework.exceptions import NotAcceptable
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.serializers import ModelSerializer, Serializer
from rest_framework.views import APIView

from django.conf.urls import url
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.core.exceptions import ImproperlyConfigured
from django.http.response import HttpResponseForbidden
from django.utils.translation import ugettext as _

from anubis.aggregators import QuerySetAggregator, TokenAggregator
from anubis.filters import Filter, ConversionFilter
from anubis.url import BooleanBuilder

def load_template(template, type_="html"):
    from django.template.utils import EngineHandler
    from django.template.base import TemplateDoesNotExist

    engines = EngineHandler()
    name = ".".join([template, type_])

    template_data = None

    for engine in engines.all():
        for loader in engine.engine.template_loaders:
            try:
                template_data = loader.load_template_source(name)
            except TemplateDoesNotExist:
                pass
            else:
                break

    if template_data is None:
        raise TemplateDoesNotExist(name)

    return template_data[0]



class TemplateRetrieverView(APIView):
    allowed_views = {}
    allowed_templates = []
    allowed_methods = {}

    @staticmethod
    def reformat_template(original):
        reformatted = original.replace("forloop", "loop") \
            .replace("elif", "elseif") \
            .replace("loop.counter", "loop.index") \
            .replace("loop.revcounter", "loop.revindex")

        reformatted = re.sub(r'\|([a-zA-Z]+)\:(\S+)', r'|\1(\2)', reformatted)

        return reformatted

    def get(self, _, templates):
        templates = templates.split(",")
        response = {}

        for template in templates:
            try:
                view_name, view_method = template.split(".")
            except ValueError:
                if template not in self.allowed_templates:
                    raise NotAcceptable("Template: {}".format(template))

                template_body = load_template(template)

                response[template] = self.reformat_template(template_body)
            else:
                if view_name not in self.allowed_views.keys():
                    raise NotAcceptable("View: {}".format(view_name))

                view = self.allowed_views[view_name]

                if view_name in self.allowed_methods.keys() and \
                        view_method not in self.allowed_methods[view_name]:
                    raise NotAcceptable("Method: {}.{}".format(view_name,
                                                               view_method))

                views = getattr(view, view_method)()

                response[view_name] = views
                # response.update({"{}.{}".format(view_name, name): \
                #                  template_body
                #                  for name, template_body in views.items()})

        return Response(response)


class ActionView(APIView):
    request_form = None
    answer_field = None
    additional_js = []
    additional_css = []
    title = ""
    description = None
    permissions_required = []

    def perform_action(self, bound_form, args, kwargs):
        raise NotImplementedError()

    def dispatch(self, request, *args, **kwargs):
        if self.permissions_required is not None:
            if not request.user.is_authenticated():
                response = HttpResponseForbidden()
            else:
                if all(map(request.user.has_perm, self.permissions_required)):
                    response = super().dispatch(request, *args, **kwargs)
                else:
                    response = HttpResponseForbidden()
        else:
            response = super().dispatch(request, *args, **kwargs)

        return response

    def post(self, request, *args, **kwargs):
        data = {}

        if not callable(self.request_form):
            success, reason = self.perform_action(None, args, kwargs)

            data = \
                {"result": "action", "success": success, "reason": reason
                }
        else:
            form = self.request_form(request.POST)

            if form.is_valid():
                success, reason = self.perform_action(form, args, kwargs)
                data = \
                    {"result": "action", "success": success, "reason": reason
                    }
            else:
                if self.answer_field is not None and \
                        self.answer_field in request.POST.keys() and \
                        request.POST[self.answer_field]:
                    result = "invalid_form"
                else:
                    result = "requires_data"
                    form = self.request_form(initial=request.POST)

                data = \
                    {"result": result, "form": form.as_p(), "title": self.title
                    }

                if self.description is not None:
                    data["description"] = self.description

        data.update(
            {"js": list(self.additional_js), "css": list(self.additional_css)
            })

        return Response(data)


class TranslationView(APIView):
    allowed_filters = {}

    def get(self, _, query):
        query = query.strip().rstrip("/")
        expression = BooleanBuilder(query).build()

        aggregator = TokenAggregator(self.allowed_filters)
        tokenized = expression.traverse(aggregator)

        return Response(dict(expression=tokenized))


class MultiModelMeta(type):

    @property
    def allowed_filters(cls):
        return cls._fieldset_filters

    def __new__(mcs, cls_name, bases, dct):
        model_filters = {}
        fieldset_filters = {}

        if "_allowed_filters" in dct.keys():
            filters_source = dct["_allowed_filters"]
            common_filters = {}

            for name, obj in filters_source.items():
                if isinstance(obj, Filter):
                    common_filters[name] = obj
                    base_filter = obj
                else:
                    base_filter = obj[0][1]
                    for model_name, filter_ in obj:
                        if isinstance(filter_, type) and \
                                issubclass(filter_, ConversionFilter):
                            filter_ = filter_(base_filter)

                        model_filters.setdefault(model_name, {})[
                            name] = filter_

                fieldset_filters[name] = base_filter

            for model_name in model_filters.keys():
                model_filters[model_name].update(common_filters)
        else:
            for base_cls in bases:
                if hasattr(base_cls, "_model_filters"):
                    model_filters = base_cls._model_filters

                if hasattr(base_cls, "_fieldset_filters"):
                    fieldset_filters = base_cls._fieldset_filters

        dct["_model_filters"] = model_filters
        dct["_fieldset_filters"] = fieldset_filters

        return super().__new__(mcs, cls_name, bases, dct)


class MultiModelMixin(metaclass=MultiModelMeta):
    model_parameter = None
    model_lookup = {}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._model = None

    @property
    def allowed_filters(self):
        try:
            return self._model_filters[self.kwargs[self.model_parameter]]
        except KeyError:
            return self.__class__.allowed_filters

    @property
    def model(self):
        if self._model is None:
            model_key = self.kwargs[self.model_parameter]
            self._model = self.model_lookup[model_key]

        return self._model

    @model.setter
    def model(self, value):
        self._model = value


class FilterViewMixin:
    expression_parameter = "search"
    allowed_filters = {}
    page_parameter = "page"
    objects_per_page = None
    pagination_cumulative = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.boolean_expression = None
        self.current_page = None
        self.current_page_object = None
        self.paginator = None

    def _get_queryset_filter(self, queryset):
        aggregator = QuerySetAggregator(queryset, self.allowed_filters)

        return self.boolean_expression.traverse(aggregator)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["filters"] = self.allowed_filters
        context["filter_keys"] = ",".join(self.allowed_filters.keys())
        context["search_text"] = self.kwarg_or_empty(self.expression_parameter)

        if self.boolean_expression is not None:
            aggregator = TokenAggregator(self.allowed_filters)
            context["search_expression"] = \
                self.boolean_expression.traverse(aggregator)

        context["search_performed"] = self.search_performed

        context["current_page"] = self.current_page
        context["current_page_object"] = self.current_page_object
        context["paginator"] = self.paginator

        return context

    @property
    def search_performed(self):
        return self.expression_parameter in self.kwargs \
            and self.kwargs[self.expression_parameter]

    def kwarg_or_none(self, key):
        if key in self.kwargs.keys() and self.kwargs[key]:
            return self.kwargs[key]
        else:
            return None

    def kwarg_or_empty(self, key):
        if key in self.kwargs.keys() and self.kwargs[key]:
            return self.kwargs[key]
        else:
            return ""

    @property
    def kwarg_val(self):
        return self.kwarg_or_none(self.expression_parameter)

    def get(self, *args, **kwargs):
        kwarg = self.kwarg_val

        if kwarg is not None:
            kwarg = kwarg.strip().rstrip("/")

            try:
                self.boolean_expression = BooleanBuilder(kwarg).build()
            except ValueError:
                error = ValueError(("Confira sua expressão e verifique se não"
                                    "esqueceu algum conector, por exemplo."))
                error.name = lambda: "Erro de Sintaxe"
                raise error

        return super().get(*args, **kwargs)

    def get_serializer_context(self):
        context = super().get_serializer_context()

        if self.objects_per_page is not None:
            context.setdefault("extra_data", {}) \
                .update({"current_page": self.current_page,
                         "total_pages": self.paginator.num_pages,
                         "last_page": self.paginator.num_pages == \
                            self.current_page,
                         "total_objects": self.paginator.count})

        actions = self.custom_actions()

        if len(actions) > 0:
            context.setdefault("extra_data", {}).update(
                {"actions": actions
                })

        return context

    def custom_actions(self):
        return []

    def get_queryset(self):
        # MRO do Python garante que haverá um get_queryset definido aqui se
        # FilterViewMixin for declarado como class pai antes da classe de View.
        original = super().get_queryset()

        if self.boolean_expression is not None:
            queryset = self._get_queryset_filter(original)
        else:
            queryset = original.none()

        return queryset

    def _paginate_queryset(self, queryset):
        self.current_page = self.kwarg_or_none(self.page_parameter)
        self.paginator = Paginator(queryset, self.objects_per_page)

        if self.current_page is None or self.current_page == 0:
            self.current_page = 1
        else:
            self.current_page = int(self.current_page)

        if self.current_page > self.paginator.num_pages:
            self.current_page = self.paginator.num_pages

        if self.pagination_cumulative:
            pages = range(1, self.current_page + 1)
        else:
            pages = [self.current_page]

        def fold(qset, page):
            self.current_page_object = self.paginator.page(page)
            qset += list(self.current_page_object.object_list)
            return qset

        return reduce(fold, pages, [])

    @classmethod
    def fieldsets(cls):
        return {filter_name: {"description": filter_.description,
                              "template": filter_.form.as_p(),
                              "arg_count": len(filter_.field_keys)}
                for filter_name, filter_ in cls.allowed_filters.items()}


class NoCacheMixin:

    def get(self, *args, **kwargs):
        response = super().get(*args, **kwargs)

        response['Cache-Control'] = "no-cache, no-store, must-revalidate"
        response['Pragma'] = "no-cache"
        response['Expires'] = "0"

        return response


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
    :class:`ListAPIView`. If you're build a HTML view, this class's child
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
    """

    base_url = ""
    api_prefix = "api"

    model = None
    default_model = None
    model_parameter = "model"

    serializers = None

    expression_parameter = "search"
    filters = {}

    objects_per_page = None
    page_parameter = "page"

    details_parameter = "details"
    details_slug = "details"

    search_slug = "search"

    sorting_options = None
    sorting_parameter = "sorted_by"
    sorting_default = None

    class _UserSerializer(ModelSerializer):
        class Meta:
            model = User
            fields = ('username', 'first_name', 'last_name', 'email')

    user_serializer = _UserSerializer

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
            models = "|".join(cls.model.keys())
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

        self._sorting = {
            "by": None,
            "ascending": True
        }

        if self.is_multi_modeled:
            self._model_lookup = self.model
            self.model = None

            self._serializer_lookup = self.serializers
            self.serializers = None
        else:
            self._model_lookup = {'_default': self.model}
            self._model_key = "_default"

    def get(self, *args, **kwargs):
        self._prepare_attributes()

        return super().get(*args, **kwargs)

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

        self.object_list = self.filter_queryset(self.get_queryset())

        context = self.get_context_data() # Changes self.object_list
        state = context["anubis_state"]

        serializer = self.get_serializer(self.object_list, many=True)

        state["searchResults"]["results"] = serializer.data

        return Response(context["anubis_state"])

    def get_queryset(self):
        original = super().get_queryset()

        if self.boolean_expression is not None:
            queryset = self.get_queryset_filter(original)
        else:
            queryset = original.none()

        queryset = self.sort_queryset(queryset)

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

    def get_context_data(self, **kwargs):
        anubis_state = self.get_full_state()

        try:
            context = super().get_context_data(**kwargs)
        except AttributeError:
            context = {}

        context["anubis_state"] = anubis_state

        return context

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
            self._model_key = "_default"
            self._model_lookup = {"_default": self.model}

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
            error = ValueError(_(("Check your expression for a missing"
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

    def get_full_state(self):
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
                context = { "request": self.request }

                serializer = self \
                    .get_details_serializer_class()(details_obj,
                                                    context=context)

                details_obj = serializer.data

            return { "object": details_obj, "model": self._model_key }
        else:
            return None

    def get_search_results(self):
        # TODO: textExpression should be computed from the parsed
        # boolean_expression.
        expression = self.boolean_expression
        visible = self.boolean_expression is not None

        return {
            "expression": expression,
            "textExpression": self.kwargs.get(self.expression_parameter, ""),
            "pagination": self.get_pagination(),
            "actions": self.get_actions(),
            "visible": visible,
            "model": self._model_key,
            "results": self.object_list,
            "sorting": self.get_sorting(),
            "selection": []
        }

    def get_pagination(self):
        if not self.is_paginated or self.boolean_expression is None:
            return None

        page = self._paginate_queryset(self.object_list)
        current_page = self.kwargs[self.page_parameter]

        self.object_list = page.object_list

        def get_from_and_to(page_number):
            from_ = (page_number - 1) * self.objects_per_page + 1
            to_ = min(page_number * self.objects_per_page,
                      page.paginator.count)

            return (page_number, from_, to_)

        all_pages = [get_from_and_to(num) for num in page.paginator.page_range]

        return {
            "currentPage": current_page,
            "allPages": all_pages,
            "recordCount": page.paginator.count,
            "nextPageNumber": page.next_page_number() \
                if page.has_next() else None,
            "previousPageNumber": page.previous_page_number() \
                if page.has_previous() else None,
        }

    def get_actions(self):
        return {}

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







class AppViewMixin(StateViewMixin):
    record_zoom = "record_zoom"
    record_list = "record_list"

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

    def get_full_state(self):
        base_state = dict(super().get_full_state())

        base_state.update({
            "tokenEditor": self.get_token_state(),
            "applicationData": self.get_application_data(),
            "models": self.get_models_meta(),
            "user": self.get_user_data(),
            "templates": self.get_templates(),
       })

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
        context = dict(super().get_context_data(**kwargs))
        state = context["anubis_state"]

        serializer = self.get_serializer(self.object_list, many=True)

        state["searchResults"]["results"] = serializer.data

        context["anubis_state"] = JSONRenderer().render(state)

        return context

    def get_models_meta(self):
        return {key: {"names": (model._meta.verbose_name.title(),
                                model._meta.verbose_name_plural.title()),
                      }
                for key, model in self._model_lookup.items()}

    def get_user_data(self):
        if self.user_serializer is None:
            return None

        return self.user_serializer(self.request.user).data \
            if self.request.user.is_authenticated() else None

    def get_templates(self):
        from django.template.loader import get_template

        def render(template):
            return get_template("{}.js".format(template)).render()

        if self.is_multi_modeled:
            if hasattr(self.record_zoom, "items"):
                record_zoom = {model: render(template) for model, template
                               in self.record_zoom.items()}
            else:
                record_zoom = {model: render(self.record_zoom)
                               for model in self._model_lookup.keys()}

            if hasattr(self.record_list, "items"):
                record_list = {model: render(template) for model, template
                               in self.record_list.items()}
            else:
                record_list = {model: render(self.record_list)
                               for model in self._model_lookup.keys()}

        else:
            record_zoom = {"_default": render(self.record_zoom)}
            record_list = {"_default": render(self.record_list)}

        return {
            "record": record_zoom,
            "search": record_list
        }

    def get_token_state(self):
        return {
            "editorText": "",
            "editorPosition": -1,
            "tokenList": [],
            "expression": "",
            "parseTree": None,
            "model": None
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
            self.base_url,
            self.search_slug,
            "${model}/" if self.is_multi_modeled else "",
            "${page}/" if self.is_paginated else "",
            "${sorting}/" if self.is_sortable else "",
            "${expr}"
        )

        react_search_api = "{}/{}/{}/{}{}{}{}".format(
            self.base_url,
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
            self.base_url,
            self.details_slug,
            "${model}/" if self.is_multi_modeled else "",
            "${id}"
        )

        react_details_api = "{}/{}/{}/{}{}".format(
            self.base_url,
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
            self.base_url,
            self.details_slug,
            "${model}/" if self.is_multi_modeled else "",
            "${id}",
            self.search_slug,
            "${page}/" if self.is_paginated else "",
            "${sorting}/" if self.is_sortable else "",
            "${expr}"
        )

        react_search_and_details_api = "{}/{}/{}/{}{}/{}/{}{}{}".format(
            self.base_url,
            self.api_prefix,
            self.details_slug,
            "${model}/" if self.is_multi_modeled else "",
            "${id}",
            self.search_slug,
            "${page}/" if self.is_paginated else "",
            "${sorting}/" if self.is_sortable else "",
            "${expr}"
        )

        return {
            "title": "Anubis Search Interface",
            "footer": ("© 2016, Câmara Municipal de São Paulo, "
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
        }
