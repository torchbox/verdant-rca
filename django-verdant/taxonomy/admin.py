from django.conf.urls import url
from django.contrib.admin.utils import quote
from django.utils.functional import cached_property
from django.utils.translation import ugettext as _

from wagtail.contrib.modeladmin.helpers import ButtonHelper
from wagtail.contrib.modeladmin.options import ModelAdmin, ModelAdminGroup
from wagtail.contrib.modeladmin.views import InstanceSpecificView
from wagtail.wagtailadmin.utils import get_object_usage

from . import models


class UsageView(InstanceSpecificView):
    page_title = _('Usage of')

    def get_usage(self):
        return get_object_usage(self.instance)

    def check_action_permitted(self, user):
        return self.permission_helper.user_can_edit_obj(user, self.instance)

    def get_meta_title(self):
        return _('Usage of %s') % self.verbose_name

    def get_context_data(self, **kwargs):
        context = super(UsageView, self).get_context_data(**kwargs)
        buttons = self.button_helper.get_buttons_for_obj(
            self.instance, exclude=['usage'])
        context.update({
            'view': self,
            'instance': self.instance,
            'usage': self.get_usage(),
        })
        return context

    def get_template_names(self):
        return ['taxonomy/admin/usage.html']


class TaxonomyButtonHelper(ButtonHelper):
    """
    A subclass of ButoonHelper which includes a 'Usage' button
    """
    usage_button_classnames = []

    def usage_button(self, pk, classnames_add=[], classnames_exclude=[]):
        classnames = self.usage_button_classnames + classnames_add
        cn = self.finalise_classname(classnames, classnames_exclude)
        return {
            'url': self.url_helper.get_action_url('usage', quote(pk)),
            'label': _('Usage'),
            'classname': cn,
            'title': _('Usage of %s') % self.verbose_name,
        }

    def get_buttons_for_obj(self, obj, exclude=None, classnames_add=None,
                            classnames_exclude=None):
        exclude = exclude or []
        classnames_add = classnames_add or []
        classnames_exclude = classnames_exclude or []

        btns = super(TaxonomyButtonHelper, self).get_buttons_for_obj(
            obj,
            exclude=exclude,
            classnames_add=classnames_add,
            classnames_exclude=classnames_exclude
        )

        ph = self.permission_helper
        usr = self.request.user
        pk = quote(getattr(obj, self.opts.pk.attname))

        if('usage' not in exclude and ph.user_can_edit_obj(usr, obj)):
            btns.append(
                self.usage_button(pk, classnames_add, classnames_exclude)
            )

        return btns


class TaxonomyModelAdmin(ModelAdmin):
    button_helper_class = TaxonomyButtonHelper
    usage_view_class = UsageView

    def usage_view(self, request, instance_pk):
        kwargs = {'model_admin': self, 'instance_pk': instance_pk}
        view_class = self.usage_view_class
        return view_class.as_view(**kwargs)(request)

    def get_admin_urls_for_registration(self):
        urls = super(TaxonomyModelAdmin, self).get_admin_urls_for_registration()

        urls += (
            url(self.url_helper.get_action_url_pattern('usage'),
                self.usage_view,
                name=self.url_helper.get_action_url_name('usage')),
        )

        return urls


class AreaModelAdmin(TaxonomyModelAdmin):
    model = models.Area


class SchoolModelAdmin(TaxonomyModelAdmin):
    model = models.School


class ProgrammeModelAdmin(TaxonomyModelAdmin):
    model = models.Programme


class TaxonomyModelAdminGroup(ModelAdminGroup):
    menu_label = 'Taxonomy'
    menu_icon = 'folder-open-inverse'
    menu_order = 750
    items = (AreaModelAdmin, SchoolModelAdmin, ProgrammeModelAdmin)