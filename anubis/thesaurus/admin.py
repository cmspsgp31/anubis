""" Admin definitions for thesaurus app.
"""

from django.utils.translation import ugettext as _
from django import forms
from django.contrib import admin
from anubis.thesaurus import models

class EdgeAdmin(admin.TabularInline):
    model = models.Edge
    fk_name = "start_node"
    extra = 1

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
    extra = 1

class FacetAdmin(admin.TabularInline):
    model = models.FacetIndicator
    classes = ['collapse']
    extra = 1

class NodeForm(forms.ModelForm):
    class Meta:
        model = models.Node
        fields = "__all__"
        widgets = {
            'label': forms.TextInput(attrs={"size": "100"}),
            'apps': forms.TextInput(attrs={"size": "100"}),
        }

class NodeAdmin(admin.ModelAdmin):
    form = NodeForm
    inlines = (NoteAdmin, EdgeAdmin, FacetAdmin)
    list_display = ("label",)


admin.site.register(models.Node, NodeAdmin)
