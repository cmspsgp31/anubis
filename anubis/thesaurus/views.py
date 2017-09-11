from django.shortcuts import render

from dal import autocomplete

class NodeAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        from anubis.thesaurus import models

        if not self.request.user.is_authenticated():
            return models.Node.objects.none()

        qs = models.Node.objects.all()

        if self.q:
            qs = qs.filter(label__icontains=self.q)

        return qs


