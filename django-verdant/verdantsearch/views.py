from verdantsearch import Search


def search(request):
    q = request.GET.get("q", "")

    if q != "":
        do_search = True
        search_results = Search().search(q)
    else:
        do_search = False
        search_results = None


def suggest(request):
    q = request.GET.get("q", "")

    if q != "":
        search_results = Search().search(q)
    else:
        search_results = None