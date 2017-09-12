from django.shortcuts import render

from dal import autocomplete

class NodeAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        from anubis.thesaurus import models

        if not self.request.user.is_authenticated():
            return models.Node.objects.none()

        qs = models.Node.objects.all()
        thesaurus_node_id = self.forwarded.get('thesaurus_node', None)

        if thesaurus_node_id is not None:
            try:
                thesaurus_node = models.Node.objects \
                    .get(pk=thesaurus_node_id)
            except models.Node.DoesNotExist:
                thesaurus_node = None
        else:
            thesaurus_node = None

        if self.q:
            qs = qs.filter(label__icontains=self.q)

        if thesaurus_node is not None and thesaurus_node.thesaurus is not None:
            qs = qs.filter(thesaurus=thesaurus_node.thesaurus)


        return qs


