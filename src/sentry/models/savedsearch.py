from django.db import models
from django.db.models import Q, UniqueConstraint
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from sentry.db.models import FlexibleForeignKey, Model, region_silo_model, sane_repr
from sentry.db.models.fields.text import CharField
from sentry.models.search_common import SearchType


class SortOptions:
    DATE = "date"
    NEW = "new"
    PRIORITY = "priority"
    FREQ = "freq"
    USER = "user"
    TREND = "trend"
    INBOX = "inbox"

    @classmethod
    def as_choices(cls):
        return (
            (cls.DATE, _("Last Seen")),
            (cls.NEW, _("First Seen")),
            (cls.PRIORITY, _("Priority")),
            (cls.FREQ, _("Events")),
            (cls.USER, _("Users")),
            (cls.TREND, _("Relative Change")),
            (cls.INBOX, _("Date Added")),
        )


@region_silo_model
class SavedSearch(Model):
    """
    A saved search query.
    """

    __include_in_export__ = True
    # TODO: Remove this column and rows where it's not null once we've
    # completely removed Sentry 9
    project = FlexibleForeignKey("sentry.Project", null=True)
    organization = FlexibleForeignKey("sentry.Organization", null=True)
    type = models.PositiveSmallIntegerField(default=SearchType.ISSUE.value, null=True)
    name = models.CharField(max_length=128)
    query = models.TextField()
    sort = CharField(
        max_length=16, default=SortOptions.DATE, choices=SortOptions.as_choices(), null=True
    )
    date_added = models.DateTimeField(default=timezone.now)
    # TODO: Remove this column once we've completely removed Sentry 9
    is_default = models.BooleanField(default=False)
    is_global = models.NullBooleanField(null=True, default=False, db_index=True)
    owner = FlexibleForeignKey("sentry.User", null=True)

    class Meta:
        app_label = "sentry"
        db_table = "sentry_savedsearch"
        unique_together = (
            ("project", "name"),
            # Each user can have one default search per org
            ("organization", "owner", "type"),
        )
        constraints = [
            UniqueConstraint(
                fields=["organization", "name", "type"],
                condition=Q(owner__isnull=True),
                name="sentry_savedsearch_is_global_6793a2f9e1b59b95",
            ),
            UniqueConstraint(
                fields=["is_global", "name"],
                condition=Q(is_global=True),
                name="sentry_savedsearch_organization_id_313a24e907cdef99",
            ),
        ]

    @property
    def is_pinned(self):
        if hasattr(self, "_is_pinned"):
            return self._is_pinned
        return self.owner is not None and self.organization is not None

    @is_pinned.setter
    def is_pinned(self, value):
        self._is_pinned = value

    @property
    def is_org_custom_search(self):
        return self.owner is None and self.organization is not None

    __repr__ = sane_repr("project_id", "name")


# TODO: Remove once we've completely removed sentry 9
@region_silo_model
class SavedSearchUserDefault(Model):
    """
    Indicates the default saved search for a given user
    """

    __include_in_export__ = True

    savedsearch = FlexibleForeignKey("sentry.SavedSearch")
    project = FlexibleForeignKey("sentry.Project")
    user = FlexibleForeignKey("sentry.User")

    class Meta:
        unique_together = (("project", "user"),)
        app_label = "sentry"
        db_table = "sentry_savedsearch_userdefault"
