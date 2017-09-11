from django.conf.urls import url

from anubis.thesaurus import views

urlpatterns = [
    url(
        r'^thesaurus-node-ac/$',
        views.NodeAutocomplete.as_view(),
        name='thesaurus-node-ac'
    ),
]
