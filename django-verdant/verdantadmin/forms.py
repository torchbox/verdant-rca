from django.forms import ModelForm

ADMIN_HANDLERS = {}


def build_model_form_class(model_class):
    class MyModelForm(ModelForm):
        class Meta:
            model = model_class
            # TODO: un-hard-code these somehow - we want model forms for things that aren't pages
            exclude = ['content_type', 'path', 'depth', 'numchild']

    return MyModelForm


class AdminHandler(object):
    inlines = []

    def __init__(self, *args, **kwargs):
        instance = kwargs.get('instance', None)

        if not hasattr(self.__class__, 'form'):
            self.__class__.form = build_model_form_class(self.__class__.model)

        self.form_instance = self.form(*args, instance=instance)

        self.inline_instances = [
            inline(*args, instance=instance)
            for inline in self.inlines
        ]

    def is_valid(self):
        result = self.form_instance.is_valid()
        for inline in self.inline_instances:
            result &= inline.is_valid()
        return result

    def save(self, commit=True):
        result = self.form_instance.save(commit=commit)
        if commit:
            self.save_inlines()
        return result

    def save_inlines(self, commit=True):
        for inline in self.inline_instances:
            inline.save(commit=commit)


def build_admin_handler_class(model_class):
    class MyAdminHandler(AdminHandler):
        model = model_class

    return MyAdminHandler


def get_admin_handler_for_model(model_class):
    if model_class not in ADMIN_HANDLERS:
        ADMIN_HANDLERS[model_class] = build_admin_handler_class(model_class)

    return ADMIN_HANDLERS[model_class]


def register(model_class, admin_handler):
    ADMIN_HANDLERS[model_class] = admin_handler
