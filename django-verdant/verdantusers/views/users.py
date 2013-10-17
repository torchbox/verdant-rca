from django.http import Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.contenttypes.models import ContentType

from treebeard.exceptions import InvalidMoveToDescendant

from verdantadmin.edit_handlers import TabbedInterface, ObjectList

def logintest(request):   
    return render(request, 'verdantusers/users/login.html', {})