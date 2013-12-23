from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from verdantsearch import models, forms


@login_required
def index(request):
    # Select only search terms with editors picks
    searchterms_list = models.SearchTerms.objects.filter(editors_picks__isnull=False).distinct()
    return render(request, 'verdantsearch/editorspicks/index.html', {
        'searchterms_list': searchterms_list,
    })


@login_required
def add(request):
    searchterms_form = forms.SearchTermsForm()
    editors_pick_formset = forms.EditorsPickFormSet()

    return render(request, 'verdantsearch/editorspicks/add.html', {
        'searchterms_form': searchterms_form,
        'editors_pick_formset': editors_pick_formset,
    })


@login_required
def edit(request, searchterms_urlified):
    searchterms_terms = models.SearchTerms._deurlify_terms(searchterms_urlified)
    searchterms = get_object_or_404(models.SearchTerms, terms=searchterms_terms)

    if request.POST:
        editors_pick_formset = forms.EditorsPickFormSet(request.POST, instance=searchterms)

        if editors_pick_formset.is_valid():
            editors_pick_formset.save()

            return redirect('verdantsearch_editorspicks_index')
        else:
            print editors_pick_formset.errors
    else:
        editors_pick_formset = forms.EditorsPickFormSet(instance=searchterms)

    return render(request, 'verdantsearch/editorspicks/edit.html', {
        'editors_pick_formset': editors_pick_formset,
        'searchterms': searchterms,
    })