from django.http import HttpResponse

from verdantimages.models import Image

def chooser(request):
    images = Image.objects.order_by('title')
    return HttpResponse("""
        {
            'html': '<h1>Some HTML</h1>',
            'onload': function(modal) {console.log('hello from onload');}
        }
    """, mimetype="text/javascript")
