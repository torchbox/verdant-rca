from wagtail.contrib.modeladmin.options import ModelAdmin, ModelAdminGroup

from . import models


class AreaModelAdmin(ModelAdmin):
    model = models.Area


class SchoolModelAdmin(ModelAdmin):
    model = models.School


class ProgrammeModelAdmin(ModelAdmin):
    model = models.Programme


class TaxonomyModelAdminGroup(ModelAdminGroup):
    menu_label = 'Taxonomy'
    menu_icon = 'folder-open-inverse'
    menu_order = 750
    items = (AreaModelAdmin, SchoolModelAdmin, ProgrammeModelAdmin)