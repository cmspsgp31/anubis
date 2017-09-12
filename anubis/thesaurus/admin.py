""" Admin definitions for thesaurus app.
"""

from django import forms
from django.conf import settings
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from dal import autocomplete, forward

from anubis.thesaurus import models

def collapse_if(key):
    return ['collapse'] if key in settings.THESAURUS_COLLAPSE else []

class NoteForm(forms.ModelForm):
    class Meta:
        model = models.Note
        fields = "__all__"
        widgets = {
            'title': forms.TextInput(attrs={"size": "100"}),
            'contents': forms.Textarea(attrs={"rows": "5", "cols": "100"})
        }


class NoteAdmin(admin.StackedInline):
    form = NoteForm
    model = models.Note
    classes = collapse_if('notes')
    extra = 1

class FacetForm(forms.ModelForm):
    class Meta:
        model = models.FacetIndicator
        fields = "__all__"
        widgets = {
            'label': forms.TextInput(attrs={"size": "100"}),
        }

class FacetAdmin(admin.TabularInline):
    form = FacetForm
    model = models.FacetIndicator
    classes = collapse_if('facets')
    extra = 1


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

class ParentAwareInlineFormSet(forms.BaseInlineFormSet):
    def get_form_kwargs(self, index):
        kwargs = super().get_form_kwargs(index)
        kwargs['parent_object'] = self.instance
        return kwargs


class EdgeForm(forms.ModelForm):
    dimension = forms.ModelChoiceField(
        queryset=models.Dimension.objects.all(),
        label=_("Dimension"),
        required=False
    )

    class Meta:
        model = models.Edge
        fields = "__all__"
        widgets = {
            'end_node': autocomplete.ModelSelect2(
                url='thesaurus-node-ac',
                forward=[forward.Field('start_node', 'thesaurus_node')]
            )
        }

    def __init__(self, *args, **kwargs):
        parent_object = kwargs.pop("parent_object", None)

        if parent_object is not None and parent_object.pk is not None:
            if hasattr(parent_object, "thesaurus"):
                thesaurus = parent_object.thesaurus

                self.declared_fields['dimension'].queryset = models.Dimension. \
                    objects.filter(thesaurus=thesaurus)

                self.base_fields["end_node"].queryset = models.Node.objects. \
                    filter(thesaurus=thesaurus)

            self.base_fields["facet"].queryset = models.FacetIndicator. \
                objects.filter(for_node=parent_object)

        super().__init__(*args, **kwargs)


class EdgeAdmin(admin.StackedInline):
    formset = ParentAwareInlineFormSet
    form = EdgeForm
    model = models.Edge
    readonly_fields = ['created_by', 'created_at', 'last_modified_by',
                       'last_modified_at']
    fk_name = "start_node"
    extra = 1
    classes = collapse_if('edges')
    fieldsets = (
        (None, {
            'fields': ['end_node']
        }),
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
    extra = 1
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
            'label': forms.TextInput(attrs={"size": "100"}),
            'apps': forms.TextInput(attrs={"size": "100"}),
        }

@admin.register(models.Node)
class NodeAdmin(BlameAdminMixin, admin.ModelAdmin):
    form = NodeForm
    readonly_fields = ['created_by', 'created_at', 'last_modified_by',
                       'last_modified_at']
    inlines = (CorrelationAdmin, EdgeAdmin, NoteAdmin, FacetAdmin)
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

class DimensionForm(forms.ModelForm):
    class Meta:
        model = models.Dimension
        fields = "__all__"
        widgets = {
            'name': forms.TextInput(attrs={"size": "100"}),
        }

class DimensionAdmin(admin.TabularInline):
    model = models.Dimension
    form = DimensionForm
    extra = 1

class ThesaurusForm(forms.ModelForm):
    class Meta:
        model = models.Thesaurus
        fields = "__all__"
        widgets = {
            'name': forms.TextInput(attrs={"size": "100"}),
        }


@admin.register(models.Thesaurus)
class ThesaurusAdmin(admin.ModelAdmin):
    inlines = (DimensionAdmin,)
    form = ThesaurusForm
    model = models.Thesaurus
