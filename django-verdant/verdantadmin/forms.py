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
    def __init__(self, model_class, **kwargs):
        if 'form' in kwargs:
            self.form_class = kwargs['form']
        else:
            self.form_class = build_model_form_class(model_class)


def get_admin_handler_for_model(model_class):
    if model_class not in ADMIN_HANDLERS:
        ADMIN_HANDLERS[model_class] = AdminHandler(model_class)

    return ADMIN_HANDLERS[model_class]


def register(model_class, admin_handler):
    ADMIN_HANDLERS[model_class] = admin_handler
