""" Admin definitions for thesaurus app.
"""

import copy

from django import forms
from django.db.models import ManyToOneRel, OneToOneRel
from django.conf import settings
from django.contrib import admin, messages
from django.urls import reverse
from django.utils.html import mark_safe
from django.utils.translation import ugettext_lazy as _

from dal import autocomplete, forward

from adminsortable2 import admin as sortable

from anubis.thesaurus import models

def collapse_if(key):
    return ['collapse'] if key in settings.THESAURUS_COLLAPSE else []

def get_text_input(full_width=False):
    size = 'calc(100% - 184px)' if not full_width else '100%'

    return forms.TextInput(attrs={
        'style': 'width: {};'.format(size),
        'size': '',
    })

class SortableInlineFormSet(sortable.CustomInlineFormSet):
    ordering = ('ordering',)

class ParentAwareSortableInlineFormSet(SortableInlineFormSet):
    def get_form_kwargs(self, index):
        kwargs = super().get_form_kwargs(index)
        kwargs['parent_object'] = self.instance
        return kwargs

class ParentAwareInlineFormSet(forms.BaseInlineFormSet):
    def get_form_kwargs(self, index):
        kwargs = super().get_form_kwargs(index)
        kwargs['parent_object'] = self.instance
        return kwargs

class NoteForm(forms.ModelForm):
    ordering = forms.HiddenInput()

    class Meta:
        model = models.Note
        fields = "__all__"
        widgets = {
            'title': get_text_input(),
            'contents': forms.Textarea(attrs={"rows": "5", "cols": "100"})
        }


class NoteAdmin(sortable.SortableInlineAdminMixin, admin.StackedInline):
    formset = SortableInlineFormSet
    form = NoteForm
    model = models.Note
    classes = collapse_if('notes')
    extra = 0

class FacetForm(forms.ModelForm):
    ordering = forms.HiddenInput()

    class Meta:
        model = models.FacetIndicator
        fields = "__all__"
        widgets = {
            'label': get_text_input(full_width=True),
        }

class FacetAdmin(sortable.SortableInlineAdminMixin, admin.TabularInline):
    formset = SortableInlineFormSet
    form = FacetForm
    model = models.FacetIndicator
    classes = collapse_if('facets')
    extra = 0

class BlameAdminMixin:
    def _modify_blameable(self, user, obj):
        if obj.pk is None and hasattr(obj, "created_by"):
            obj.created_by = user

        if hasattr(obj, "last_modified_by"):
            obj.last_modified_by = user

    def save_model(self, request, obj, form, change):
        self._modify_blameable(request.user, obj)

        return super().save_model(request, obj, form, change)

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)

        for obj in formset.deleted_objects:
            obj.delete()

        for instance in instances:
            self._modify_blameable(request.user, instance)
            instance.save()

        formset.save_m2m()

class BaseEdgeForm(forms.ModelForm):
    dimension = forms.ModelChoiceField(
        queryset=models.Dimension.objects.all(),
        label=_("Dimension"),
        required=False
    )

    class Meta:
        model = models.Edge
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        parent_object = kwargs.pop("parent_object", None)

        if parent_object is not None and parent_object.pk is not None:
            if hasattr(parent_object, "thesaurus"):
                thesaurus = parent_object.thesaurus

                self.declared_fields['dimension'].queryset = models \
                    .Dimension \
                    .objects \
                    .filter(thesaurus=thesaurus)

                self.base_fields[self._editable_node].queryset = models.Node \
                    .objects \
                    .filter(thesaurus=thesaurus)

            self.base_fields["facet"].queryset = models.FacetIndicator. \
                objects.filter(for_node=parent_object)

        super().__init__(*args, **kwargs)

class DownwardEdgeForm(BaseEdgeForm):
    _editable_node = "end_node"

    class Meta(BaseEdgeForm.Meta):
        fields = "__all__"
        widgets = {
            # 'ordering': forms.HiddenInput(),
            'end_node': autocomplete.ModelSelect2(
                url='thesaurus-node-ac',
                forward=[forward.Field('start_node', 'thesaurus_node')]
            )
        }

class UpwardEdgeForm(BaseEdgeForm):
    _editable_node = "start_node"

    class Meta(BaseEdgeForm.Meta):
        exclude = ["ordering"]
        widgets = {
            'start_node': autocomplete.ModelSelect2(
                url='thesaurus-node-ac',
                forward=[forward.Field('end_node', 'thesaurus_node')]
            )
        }

class BaseEdgeAdmin(admin.StackedInline):
    model = models.Edge
    readonly_fields = ['created_by', 'created_at', 'last_modified_by',
                    'last_modified_at']
    extra = 0
    classes = collapse_if('edges')
    fieldsets = (
        (_("Advanced fields"), {
            'classes': collapse_if('advanced_fields'),
            'fields': ['dimension', 'facet']
        }),
        (_("Metadata"), {
            'classes': collapse_if('metadata'),
            'fields': ['created_by', 'created_at', 'last_modified_by',
                    'last_modified_at'],
        }),
    )

class DownwardEdgeAdmin(sortable.SortableInlineAdminMixin, BaseEdgeAdmin):
    formset = ParentAwareSortableInlineFormSet
    form = DownwardEdgeForm
    fieldsets = [[None, {
        'fields': ['end_node', 'ordering']
    }]] + list(BaseEdgeAdmin.fieldsets)
    fk_name = "start_node"
    verbose_name = _("downward edge")
    verbose_name_plural = _("downward edges")
    ordering = ('ordering',)

class UpwardEdgeAdmin(BaseEdgeAdmin):
    formset = ParentAwareInlineFormSet
    form = UpwardEdgeForm
    fieldsets = [[None, {
        'fields': ['start_node']
    }]] + list(BaseEdgeAdmin.fieldsets)
    fk_name = "end_node"
    verbose_name = _("upward edge")
    verbose_name_plural = _("upward edges")
    ordering = ('start_node__label',)


class CorrelationForm(forms.ModelForm):
    dimension = forms.ModelChoiceField(
        queryset=models.Dimension.objects.all(),
        label=_("Dimension"),
        required=False
    )

    class Meta:
        model = models.Correlation
        fields = "__all__"
        widgets = {
            'to_node': autocomplete.ModelSelect2(
                url='thesaurus-node-ac',
                forward=[forward.Field('from_node', 'thesaurus_node')]
            )
        }

    def __init__(self, *args, **kwargs):
        parent_object = kwargs.pop("parent_object", None)

        if parent_object is not None and parent_object.pk is not None:
            thesaurus = parent_object.thesaurus

            self.declared_fields["dimension"].queryset = models.Dimension. \
                objects.filter(
                    thesaurus=thesaurus
                )

            self.base_fields["to_node"].queryset = models.Node.objects.filter(
                thesaurus=thesaurus
            )

        super().__init__(*args, **kwargs)


class CorrelationAdmin(admin.StackedInline):
    formset = ParentAwareInlineFormSet
    form = CorrelationForm
    model = models.Correlation
    readonly_fields = ['created_by', 'created_at', 'last_modified_by',
                       'last_modified_at']
    fk_name = "from_node"
    classes = collapse_if('correlations')
    extra = 0
    fieldsets = (
        (None, {
            'fields': ['to_node']
        }),
        (_("Advanced fields"), {
            'classes': collapse_if('advanced_fields'),
            'fields': ['dimension']
        }),
        (_("Metadata"), {
            'classes': collapse_if('metadata'),
            'fields': ['created_by', 'created_at', 'last_modified_by',
                       'last_modified_at'],
        }),
    )

class UsedForWrapper(admin.widgets.RelatedFieldWidgetWrapper):
    def get_context(self, name, value, attrs):
        context = copy.copy(super().get_context(name, value, attrs))

        context['url_params'] += "&used_for=1"

        return context

class UsedForForm(forms.ModelForm):
    verbotten_node = forms.ModelChoiceField(
        queryset=models.Node.objects.all(),
        widget=autocomplete.ModelSelect2(
            url='thesaurus-node-ac',
            forward=[forward.Field('allowed_node', 'thesaurus_node')]
        ),
        label=_("Used for")
    )

    class Meta:
        models = models.UsedFor
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        field = self.fields['verbotten_node']
        model = models.Node
        rel = OneToOneRel(field, model, 'id')

        self.fields['verbotten_node'].widget = UsedForWrapper(
            self.fields['verbotten_node'].widget,
            rel,
            admin.site,
            can_add_related=True,
            can_change_related=True
        )


class UsedForAdmin(admin.StackedInline):
    form = UsedForForm
    fk_name = "allowed_node"
    classes = collapse_if('used_for')
    readonly_fields = ['created_by', 'created_at', 'last_modified_by',
                       'last_modified_at']
    model = models.UsedFor
    extra = 0
    fieldsets = (
        (None, {
            'fields': ('verbotten_node',)
        }),
        (_("Metadata"), {
            'classes': collapse_if('metadata'),
            'fields': ['created_by', 'created_at', 'last_modified_by',
                       'last_modified_at'],
        }),
    )

class NodeForm(forms.ModelForm):
    thesaurus = forms.ModelChoiceField(
        queryset=models.Thesaurus.objects.all(),
        empty_label=None,
        label=_("Thesaurus")
    )

    class Meta:
        model = models.Node
        fields = "__all__"
        widgets = {
            'label': get_text_input(),
            'apps': get_text_input(),
        }

@admin.register(models.Node)
class NodeAdmin(BlameAdminMixin, admin.ModelAdmin):
    form = NodeForm
    readonly_fields = ['created_by', 'created_at', 'last_modified_by',
                       'last_modified_at']
    inlines_ = (UsedForAdmin, CorrelationAdmin, UpwardEdgeAdmin,
                DownwardEdgeAdmin, NoteAdmin, FacetAdmin)
    list_filter = ('thesaurus',)
    list_display = ("label",)
    fieldsets = (
        (None, {
            'fields': ('label',)
        }),
        (_("Advanced fields"), {
            'classes': collapse_if('advanced_fields'),
            'fields': ('thesaurus', 'apps')
        }),
        (_("Metadata"), {
            'classes': collapse_if('metadata'),
            'fields': ['created_by', 'created_at', 'last_modified_by',
                       'last_modified_at'],
        }),
    )

    def add_view(self, request, form_url='', extra_context=None):
        self.inlines = copy.copy(self.inlines_)

        if request.GET.get('used_for', None) == '1':
            self.inlines = []

        return super().add_view(request, form_url, extra_context)

    def change_view(self, request, object_id, form_url='', extra_context=None):
        self.inlines = copy.copy(self.inlines_)

        try:
            obj = models.Node.objects.get(pk=object_id)
        except models.Node.DoesNotExist:
            pass
        else:
            if obj.should_use.count() > 0:
                self.inlines = []
                node = obj.should_use.first()
                link = '<a href="{link}" target="_blank">{name}</a>' \
                    .format(link=reverse('admin:thesaurus_node_change',
                                         args=[node.id]),
                            name=node.label)
                message = _("This is not a preferred term. Use "
                            "{link}.").format(link=link)

                messages.add_message(request, messages.WARNING,
                                     mark_safe(message))

        return super().change_view(request, object_id, form_url, extra_context)


class DimensionForm(forms.ModelForm):
    class Meta:
        model = models.Dimension
        fields = "__all__"
        widgets = {
            'name': get_text_input(full_width=True),
            'correlation_init': get_text_input(full_width=True),
            'edge_start_init': get_text_input(full_width=True),
            'edge_end_init': get_text_input(full_width=True),
        }

class DimensionAdmin(admin.TabularInline):
    model = models.Dimension
    form = DimensionForm
    extra = 0

class ThesaurusForm(forms.ModelForm):
    class Meta:
        model = models.Thesaurus
        fields = "__all__"
        widgets = {
            'name': get_text_input(),
        }


@admin.register(models.Thesaurus)
class ThesaurusAdmin(admin.ModelAdmin):
    inlines = (DimensionAdmin,)
    form = ThesaurusForm
    model = models.Thesaurus
