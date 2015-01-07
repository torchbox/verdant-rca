import re

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
            
            # parse out the introduction here
            r = re.compile('^(<h1>(.+?)</h1>)')
            if r.search(instance.body):
                match_groups = r.search(instance.body).groups()
                intro_all = match_groups[0]
                intro = match_groups[1]
                initial['intro_text'] = intro
                initial['body'] = instance.body[len(intro_all):]
            
            kwargs['initial'] = initial
        
        super(PageForm, self).__init__(*args, **kwargs)
    
    intro_text = forms.CharField(
        label="Introduction",
        required=False,
        widget=forms.Textarea,
    )
    
    def clean(self):
        intro_text = self.cleaned_data['intro_text']
        body = self.cleaned_data['body']
        
        self.cleaned_data['body'] = '<h1>{intro}</h1>{body}'.format(
            intro=intro_text,
            body=body
        )
        
        return self.cleaned_data
    
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

u'<h1>This is the introduction!</h1>\n<h1></h1><h2><b>Can we not do an h1 here?!</b></h2>This is an introduction!\nAnd some more writing here! wow, save was called in the beginning?'

# Author selection logic:
# Credit ('by'):
#    Choose type (select, values = Single student or Group of students)
#      Conditional field if Single student selected:
#        Name of Student (Wagtail page picker)
#      Conditional field if Group of students selected:
#        Name of Students (basic text)
