from django.db import models
from wagtail.contrib.settings.models import BaseSetting, register_setting
from wagtail.wagtailadmin.edit_handlers import FieldPanel, MultiFieldPanel, PageChooserPanel
from django.conf import settings


@register_setting
class StudentProfilesSettings(BaseSetting):
    """ ForeignKeys here are set with ``models.PROTECT``. This will still cause
    an unfriendly ProtectedError should anyone try to delete the target of this
    ForeignKey. However, that is preferable to allowing it to be deleted.
    """
    new_student_page_index = models.ForeignKey(
        'wagtailcore.Page', null=False, blank=False, on_delete=models.PROTECT,
        related_name='+',
        help_text="New student pages will be added as children of this page.",
        verbose_name="Student pages",
        default=settings.NEW_STUDENT_INDEX
    )
    rca_now_index = models.ForeignKey(
        'wagtailcore.Page', null=False, blank=False, on_delete=models.PROTECT,
        related_name='+',
        help_text="New RCA Now pages will be added as children of this page.",
        verbose_name="RCA Now pages",
        default=settings.RCA_NOW_INDEX
    )
    show_pages_enabled = models.BooleanField(
        default=True,
        help_text="Determine whether show pages and postcard upload are enabled.",
    )

    panels = [
        MultiFieldPanel([
            PageChooserPanel('new_student_page_index', 'rca.StandardIndex'),
            PageChooserPanel('rca_now_index', 'rca.RCANowIndex'),
        ], "Index page locations"),
        FieldPanel('show_pages_enabled')
    ]
