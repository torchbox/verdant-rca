from django.db import models
from wagtail.contrib.settings.models import BaseSetting, register_setting
from wagtail.wagtailadmin.edit_handlers import PageChooserPanel


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
        verbose_name="Index for new student pages",
        default=6201
    )
    rca_now_index = models.ForeignKey(
        'wagtailcore.Page', null=False, blank=False, on_delete=models.PROTECT,
        related_name='+',
        help_text="New RCA Now pages will be added as children of this page.",
        verbose_name="Index for new RCA Now pages",
        default=36
    )

    panels = [
        PageChooserPanel('new_student_page_index', 'rca.StandardIndex'),
        PageChooserPanel('rca_now_index', 'rca.RCANowIndex')
    ]
