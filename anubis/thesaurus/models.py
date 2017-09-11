""" Thesaurus models.
"""

from django.conf import settings
from django.utils.translation import ugettext_lazy as _, ugettext
from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.postgres import fields as postgres
from django.core.exceptions import ValidationError

from anubis.query import ProcedureQuerySet

class BlamableModel(models.Model):
    """ This class is abstract model for adding the "blame" fields to a model:
        date of creation, latest modification, and the user who created and
        lastly modified the current record.
    """

    created_by = models.ForeignKey(
        to=settings.AUTH_USER_MODEL,
        editable=False,
        blank=True,
        null=True,
        related_name="created_%(class)s_objects",
        on_delete=models.SET_NULL,
        verbose_name=_("Created by")
    )

    created_at = models.DateTimeField(
        null=False,
        auto_now_add=True,
        verbose_name=_("Created at"),
    )

    last_modified_by = models.ForeignKey(
        to=settings.AUTH_USER_MODEL,
        editable=False,
        blank=True,
        null=True,
        related_name="modified_%(class)s_objects",
        on_delete=models.SET_NULL,
        verbose_name=_("Last modified by")
    )

    last_modified_at = models.DateTimeField(
        null=False,
        auto_now=True,
        verbose_name=_("Last modified at"),
    )

    class Meta:
        abstract = True

class Thesaurus(models.Model):
    class Meta:
        verbose_name = _("Thesaurus")
        verbose_name_plural = _("Thesauri")

    name = models.TextField(
        verbose_name=_("Name"),
        null=False,
        blank=False
    )

    def __str__(self):
        return ugettext("Thesaurus") + ": {}".format(self.name)

class Dimension(models.Model):
    class Meta:
        verbose_name = _("Dimension")
        verbose_name_plural = _("Dimensions")

    name = models.TextField(
        verbose_name=_("Name"),
        null=False,
        blank=False
    )

    thesaurus = models.ForeignKey(
        to="Thesaurus",
        related_name="dimensions",
        verbose_name=_("Thesaurus"),
        blank=False,
        null=False
    )

    def __str__(self):
        return ugettext("Dimension") + ": {}".format(self.name)

class Node(BlamableModel):
    class Meta:
        verbose_name = _("Term")
        verbose_name_plural = _("Terms")

    class QuerySet(ProcedureQuerySet):
        pass

    objects = QuerySet.as_manager()

    label = models.TextField(
        verbose_name=_("Term"),
        null=False,
        blank=False,
        unique=True
    )

    children = models.ManyToManyField(
        to="self",
        symmetrical=False,
        through="Edge",
        through_fields=("start_node", "end_node"),
        related_name="parents",
        verbose_name=_("Child terms"),
    )

    correlations = models.ManyToManyField(
        to="self",
        symmetrical=False, # but it's actually True, and due to Django's
                           # restrictions we have to implement the symmetry
                           # manually.
        through="Correlation",
        through_fields=("from_node", "to_node"),
        related_name="correlated+",
        verbose_name=_("Correlated terms")
    )

    thesaurus = models.ForeignKey(
        to="Thesaurus",
        related_name="nodes",
        verbose_name=_("Thesaurus"),
        blank=False,
        null=False
    )

    apps = postgres.ArrayField(
        models.TextField(
            blank=False,
            null=False
        ),
        verbose_name=_("App availability"),
        blank=True,
        null=False,
        help_text=_("Comma-separated list of apps "
                    "that can use this term."),
    )

    def __str__(self):
        return self.label

class Correlation(BlamableModel):
    class Meta:
        verbose_name = _("Correlation")
        verbose_name_plural = _("Correlations")

    from_node = models.ForeignKey(
        to="Node",
        related_name="correlations_from+",
        blank=False,
        null=False,
        verbose_name=_("Correlated term")
    )

    to_node = models.ForeignKey(
        to="Node",
        related_name="correlations_to+",
        blank=False,
        null=False,
        verbose_name=_("Correlated term")
    )

    dimension = models.ForeignKey(
        to="Dimension",
        related_name="correlations",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        verbose_name=_("Dimension")
    )

    def clean(self):
        """ Validate that both the start and end nodes belong to the same
            thesaurus.
        """

        if not self.from_node.thesaurus == self.to_node.thesaurus:
            raise ValidationError(_("Correlated terms \"{from_}\" and \"{to}\" "
                                    "should belong to the same thesaurus."
                                   ).format(from_=self.from_node.label,
                                            to=self.to_node.label)
                                 )

        if self.dimension is not None and \
                not self.dimension.thesaurus == self.from_node.thesaurus:
            raise ValidationError(_("The dimension thesaurus \"{dim_thes}\" "
                                    "should be the same thesaurus (\"{node_"
                                    "thes}\") of both the terms in the "
                                    " relationship."
                                   ).format(
                                       dim_thes=self.dimension.thesaurus.name,
                                       node_thes=self.from_node.thesaurus.name
                                   )
                                 )


class Edge(BlamableModel):
    class Meta:
        verbose_name = _("Edge")
        verbose_name_plural = _("Edges")

    start_node = models.ForeignKey(
        to="Node",
        related_name="child_edges",
        blank=False,
        null=False,
        verbose_name=_("Parent term")
    )

    end_node = models.ForeignKey(
        to="Node",
        related_name="parent_edges",
        blank=False,
        null=False,
        verbose_name=_("Child term")
    )

    dimension = models.ForeignKey(
        to="Dimension",
        related_name="edges",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        verbose_name=_("Dimension")
    )

    facet = models.ForeignKey(
        to="FacetIndicator",
        related_name="on_edges",
        blank=True,
        null=True,
        verbose_name=_("Facet indicator"),
        default=None
    )

    def clean_facets(self):
        """ Validate facets to assure the user has only used facets owned
            by the start node in the edge.
        """

        if self.facet is not None and \
                not self.facet.for_node == self.start_node:
            raise ValidationError(_(("You cannot use a facet indicator from "
                                     "the term \"{owner}\" in an edge whose "
                                     "parent is a different term "
                                     "(\"{parent}\")."
                                    ).format(owner=self.facet.for_node.label,
                                             parent=self.start_node.label)
                                   ))

    def clean_thesaurus(self):
        """ Validate that both the start and end nodes belong to the same
            thesaurus.
        """

        if not self.start_node.thesaurus == self.end_node.thesaurus:
            raise ValidationError(_(("Parent term \"{parent}\" and child term "
                                     "\"{child}\" don't belong to the same "
                                     "thesaurus."
                                    ).format(parent=self.start_node.label,
                                             child=self.end_node.label)
                                   ))

        if self.dimension is not None and \
                not self.dimension.thesaurus == self.start_node.thesaurus:
            raise ValidationError(_("The dimension thesaurus \"{dim_thes}\" "
                                    "should be the same thesaurus (\"{node_"
                                    "thes}\") of both the terms in the "
                                    " relationship."
                                   ).format(
                                       dim_thes=self.dimension.thesaurus.name,
                                       node_thes=self.start_node.thesaurus.name
                                   )
                                 )

    def clean(self):
        """ Performs all validations.
        """
        self.clean_facets()
        self.clean_thesaurus()

        return super().clean()


    def __str__(self):
        return "{start_node} -> {end_node}".format(
            start_node=self.start_node.label,
            end_node=self.end_node.label
        )

class FacetIndicator(models.Model):
    class Meta:
        verbose_name = _("Facet Indicator") # rótulo nodal
        verbose_name_plural = _("Facet Indicators")

    label = models.TextField(
        verbose_name=_("Name"),
        blank=False,
        null=False
    )

    for_node = models.ForeignKey(
        to="Node",
        related_name="facet_indicators",
        blank=False,
        null=False,
        verbose_name=_("Term")
    )

    def __str__(self):
        return ugettext("Facet indicator") + ": {}".format(self.label)


class Note(models.Model):
    class Meta:
        verbose_name = _("Note")
        verbose_name_plural = _("Notes")

    title = models.TextField(
        verbose_name=_("Note title"),
        blank=True,
        null=False
    )

    contents = models.TextField(
        verbose_name=_("Note contents"),
        blank=False,
        null=False
    )

    node = models.ForeignKey(
        to="Node",
        related_name="notes",
        verbose_name=_("Term"),
        blank=False,
        null=False
    )
