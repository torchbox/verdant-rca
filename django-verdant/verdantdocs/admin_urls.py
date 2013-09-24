from django.conf.urls import patterns, url


urlpatterns = patterns('verdantdocs.views',
    url(r'^$', 'documents.index', name='verdantdocs_index'),
    url(r'^add/$', 'documents.add', name='verdantdocs_add_document'),
    url(r'^edit/(\d+)/$', 'documents.edit', name='verdantdocs_edit_document'),
    url(r'^search/$', 'documents.search', name='verdantdocs_search'),

    url(r'^chooser/$', 'chooser.chooser', name='verdantdocs_chooser'),
    url(r'^chooser/(\d+)/$', 'chooser.document_chosen', name='verdantdocs_document_chosen'),
)
