function createSearchTermsChooser(id) {
    var chooserElement = $('#' + id + '-chooser');
    var input = $('#' + id);

    chooserElement.click(function() {
        var initialUrl = '{% url "verdantsearch_searchterms_chooser" %}';

        ModalWorkflow({
            'url': initialUrl,
            'responses': {
                'searchtermsChosen': function(searchTermsData) {
                    input.val(searchTermsData.terms);
                }
            }
        });
    });
}