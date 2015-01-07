from django import forms

from wagtail.wagtailcore.fields import RichTextArea

from rca.help_text import help_text
from rca.models import RcaNowPage


class PageForm(forms.ModelForm):
    
    def __init__(self, *args, **kwargs):
        
        instance = kwargs.get('instance')
        if instance:
            initial = kwargs.get('initial', {})
            initial['tags'] = ','.join([t.name for t in instance.tags.all()])
            kwargs['initial'] = initial
        
        super(PageForm, self).__init__(*args, **kwargs)
    
    intro_text = forms.CharField(
        label="Introduction",
        required=False,
        widget=forms.Textarea,
    )
    
    class Meta:
        model = RcaNowPage
        fields = [
            'title',
            'intro_text',
            'body',
            # author selection logic here
            'author',
            'date',
            'programme',
            'tags',
        ]


# Author selection logic:
# Credit ('by'):
#    Choose type (select, values = Single student or Group of students)
#      Conditional field if Single student selected:
#        Name of Student (Wagtail page picker)
#      Conditional field if Group of students selected:
#        Name of Students (basic text)
