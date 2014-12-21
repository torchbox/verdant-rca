from django.shortcuts import render
from django import forms



class ExampleForm(forms.Form):
    
    t1 = forms.CharField(
        help_text='Everything is awesome!',
    )
    t2 = forms.CharField()
    t3 = forms.CharField()
    t4 = forms.CharField()
    t5 = forms.CharField()
    t6 = forms.CharField()

    def __init__(self, *args, **kwargs):
        super(ExampleForm, self).__init__(*args, **kwargs)

        print self.fields

        self.fields['t2'].is_read_only = True
        print self.fields['t2'].is_read_only


    t2.is_read_only = True


def example(request):
    data = {}
    
    data['form'] = ExampleForm(
        initial={
            't1': 't1 dorem ipsum',
            't2': 't1 dorem ipsum',
            't3': 't1 dorem ipsum',
            't4': 't1 dorem ipsum',
            't5': 't1 dorem ipsum',
            't6': 't1 dorem ipsum',
        }
    )
    
    return render(request, 'student_profiles/example.html', data)
