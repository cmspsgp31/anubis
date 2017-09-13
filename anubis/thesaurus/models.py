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
        verbose_name=_("created by")
    )

    created_at = models.DateTimeField(
        null=False,
        auto_now_add=True,
        verbose_name=_("created at"),
    )

    last_modified_by = models.ForeignKey(
        to=settings.AUTH_USER_MODEL,
        editable=False,
        blank=True,
        null=True,
        related_name="modified_%(class)s_objects",
        on_delete=models.SET_NULL,
        verbose_name=_("last modified by")
    )

    last_modified_at = models.DateTimeField(
        null=False,
        auto_now=True,
        verbose_name=_("last modified at"),
    )

    class Meta:
        abstract = True

class Thesaurus(models.Model):
    class Meta:
        verbose_name = _("thesaurus")
        verbose_name_plural = _("thesauri")

    name = models.TextField(
        verbose_name=_("name"),
        null=False,
        blank=False
    )

    def __str__(self):
        return ugettext("Thesaurus") + ": {}".format(self.name)

class Dimension(models.Model):
    class Meta:
        verbose_name = _("dimension")
        verbose_name_plural = _("dimensions")

    name = models.TextField(
        verbose_name=_("name"),
        null=False,
        blank=False
    )

    correlation_init = models.CharField(
        max_length=20,
        null=False,
        blank=False,
        verbose_name=_("initials for correlated terms"),
        default=_("RT")
    )

    edge_start_init = models.CharField(
        max_length=20,
        null=False,
        blank=False,
        verbose_name=_("initials for generic terms"),
        default=_("GT")
    )

    edge_end_init = models.CharField(
        max_length=20,
        null=False,
        blank=False,
        verbose_name=_("initials for specific terms"),
        default=_("ST")
    )

    thesaurus = models.ForeignKey(
        to="Thesaurus",
        related_name="dimensions",
        verbose_name=_("thesaurus"),
        on_delete=models.CASCADE,
        blank=False,
        null=False
    )

    def __str__(self):
        return ugettext("Dimension") + ": {}".format(self.name)

class Node(BlamableModel):
    class Meta:
        verbose_name = _("term")
        verbose_name_plural = _("terms")

    class QuerySet(ProcedureQuerySet):
        pass

    objects = QuerySet.as_manager()

    label = models.TextField(
        verbose_name=_("term"),
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
        verbose_name=_("child terms"),
    )

    correlated = models.ManyToManyField(
        to="self",
        symmetrical=False, # but it's actually True, and due to Django's
                           # restrictions we have to implement the symmetry
                           # manually.
        through="Correlation",
        through_fields=("from_node", "to_node"),
        related_name="reverse_correlated+",
        verbose_name=_("correlated terms")
    )

    used_for = models.ManyToManyField(
        to="self",
        symmetrical=False,
        through="UsedFor",
        through_fields=("allowed_node", "verbotten_node"),
        related_name="should_use",
        verbose_name=_("used for")
    )

    thesaurus = models.ForeignKey(
        to="Thesaurus",
        related_name="nodes",
        verbose_name=_("thesaurus"),
        on_delete=models.CASCADE,
        blank=False,
        null=False
    )

    apps = postgres.ArrayField(
        models.TextField(
            blank=False,
            null=False
        ),
        verbose_name=_("app availability"),
        blank=True,
        null=False,
        help_text=_("Comma-separated list of apps "
                    "that can use this term."),
    )

    def __str__(self):
        return self.label

class UsedFor(BlamableModel):
    class Meta:
        verbose_name = _("equivalence")
        verbose_name_plural = _("equivalences")

    verbotten_node = models.ForeignKey(
        to="Node",
        related_name="prohibition",
        blank=False,
        null=False,
        verbose_name=_("used for"),
        on_delete=models.CASCADE,
        unique=True # Emulates a One to Many relationship with an
                    # intermediary table
    )

    allowed_node = models.ForeignKey(
        to="Node",
        related_name="allowances",
        on_delete=models.CASCADE,
        blank=False,
        null=False
    )

    def __str__(self):
        # return self.verbotten_node.label
        return ugettext("\"{verbotten}\": use \"{allowed}\""). \
            format(verbotten=self.verbotten_node.label,
                   allowed=self.allowed_node.label)


class Correlation(BlamableModel):
    class Meta:
        verbose_name = _("correlation")
        verbose_name_plural = _("correlations")

    from_node = models.ForeignKey(
        to="Node",
        related_name="correlations",
        blank=False,
        null=False,
        on_delete=models.CASCADE,
        verbose_name=_("correlated term")
    )

    to_node = models.ForeignKey(
        to="Node",
        related_name="correlations_to+",
        blank=False,
        null=False,
        on_delete=models.CASCADE,
        verbose_name=_("correlated term")
    )

    dimension = models.ForeignKey(
        to="Dimension",
        related_name="correlations",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        verbose_name=_("dimension")
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

    def __str__(self):
        return "{from_node} <-> {to_node}".format(
            from_node=self.from_node.label,
            to_node=self.to_node.label
        )


class Edge(BlamableModel):
    class Meta:
        verbose_name = _("edge")
        verbose_name_plural = _("edges")
        unique_together = [['start_node', 'end_node', 'dimension']]
        ordering = ('start_node', 'dimension', 'ordering',)

    start_node = models.ForeignKey(
        to="Node",
        related_name="child_edges",
        blank=False,
        null=False,
        on_delete=models.CASCADE,
        verbose_name=_("parent term")
    )

    end_node = models.ForeignKey(
        to="Node",
        related_name="parent_edges",
        blank=False,
        null=False,
        on_delete=models.CASCADE,
        verbose_name=_("child term")
    )

    dimension = models.ForeignKey(
        to="Dimension",
        related_name="edges",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        verbose_name=_("dimension")
    )

    ordering = models.PositiveIntegerField(
        blank=True,
        null=False,
        default=0
    )

    facet = models.ForeignKey(
        to="FacetIndicator",
        related_name="on_edges",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        verbose_name=_("facet indicator"),
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
        verbose_name = _("facet indicator") # rótulo nodal
        verbose_name_plural = _("facet indicators")
        unique_together = [['label', 'for_node']]
        ordering = ('for_node', 'ordering')

    label = models.TextField(
        verbose_name=_("name"),
        blank=False,
        null=False
    )

    for_node = models.ForeignKey(
        to="Node",
        related_name="facet_indicators",
        blank=False,
        null=False,
        on_delete=models.CASCADE,
        verbose_name=_("term")
    )

    ordering = models.PositiveIntegerField(
        blank=True,
        null=False,
        default=0
    )

    def __str__(self):
        return ugettext("Facet indicator") \
            + ": {}".format(self.label)


class Note(models.Model):
    class Meta:
        verbose_name = _("note")
        verbose_name_plural = _("notes")
        ordering = ['node', 'ordering']

    title = models.TextField(
        verbose_name=_("note title"),
        blank=True,
        null=False
    )

    contents = models.TextField(
        verbose_name=_("note contents"),
        blank=False,
        null=False
    )

    node = models.ForeignKey(
        to="Node",
        related_name="notes",
        verbose_name=_("term"),
        on_delete=models.CASCADE,
        blank=False,
        null=False
    )

    ordering = models.PositiveIntegerField(
        blank=True,
        null=False,
        default=0
    )

