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
import json

from functools import reduce

from rest_framework.views import APIView
from django.core.paginator import Paginator
from django.http.response import HttpResponseForbidden
from rest_framework.exceptions import NotAcceptable
from rest_framework.response import Response

from anubis.url import BooleanBuilder
from anubis.aggregators import QuerySetAggregator, TokenAggregator
from anubis.filters import Filter, ConversionFilter



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

                from django.template.loaders.app_directories import Loader

                loader = Loader()
                name = "{}.html".format(template)
                template_body = loader.load_template_source(name)[0]

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


class AppViewMixin:
    """A mixin for creating views containing the Anubis search interface.

    This is the mixin you should inherit from when you want to create a view
    that displays the Anubis search interface. It does not create any views
    regarding the JSON API needed to make the interface actually work and
    perform searches.

    Attributes:
        anubis_state: A structure of nested `dict`s, `list`s, `str`s and
            `int`s that can be converted to JSON. This will be passed to the
            JavaScript interface as the global variable __AnubisState.

    """

    base_url = ""
    """Base URL for the application displaying the search interface.
    """

    def __init__(self):
        super().__init__()

        self.anubis_state = \
            {"tokenEditor": {
                "editorText": "",
                "editorPosition": -1,
                "tokenList": [],
                "expression": "",
                "parseTree": None,
                "model": None
            },
             "searchResults": {
                 "expression": "",
                 "visible": False,
                 "actions": {
                     "action_01": {
                         "allowed": False,
                         "url": ""
                     }
                 },
                 "model": None,
                 "sort": {
                     "by": None,
                     "ascending": True
                 },
                 "results": [],
                 "page": 0,
                 "selection": []
             },
             "models": {
                 "model_01": {}
             },
             "counter": 0,
             "baseURL": self.base_url
            }

    def get_context_data(self, **kwargs):
        """Provides the necessary context for the search interface to run.
        """

        context = super().get_context_data(**kwargs)
        context["anubis_state"] = json.dumps(self.anubis_state)

        return context
