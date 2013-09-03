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
    def __init__(self, *args, **kwargs):
        instance = kwargs.get('instance', None)
        self.form_instance = self.form(*args, instance=instance)

    def is_valid(self):
        return self.form_instance.is_valid()

    def save(self, commit=True):
        return self.form_instance.save(commit=commit)


def build_admin_handler_class(model_class):
    class MyAdminHandler(AdminHandler):
        form = build_model_form_class(model_class)

    return MyAdminHandler


def get_admin_handler_for_model(model_class):
    if model_class not in ADMIN_HANDLERS:
        ADMIN_HANDLERS[model_class] = build_admin_handler_class(model_class)

    return ADMIN_HANDLERS[model_class]


def register(model_class, admin_handler):
    ADMIN_HANDLERS[model_class] = admin_handler
