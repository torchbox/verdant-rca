from django.forms import ModelForm

MODEL_FORMS = {}

def get_form_for_model(model_class):

    if model_class not in MODEL_FORMS:
        class MyModelForm(ModelForm):
            class Meta:
                model = model_class
                # TODO: un-hard-code these somehow - we want model forms for things that aren't pages
                exclude = ['content_type', 'path', 'depth', 'numchild']
        MODEL_FORMS[model_class] = MyModelForm

    return MODEL_FORMS[model_class]


def register(model_class, form_class):
    MODEL_FORMS[model_class] = form_class
