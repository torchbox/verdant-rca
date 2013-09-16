function makeRichTextEditable(id) {
    var input = $('#' + id);
    var richText = $('<div class="richtext"></div>').html(input.val());
    richText.insertBefore(input);
    input.hide();
    richText.hallo({
        toolbar: 'halloToolbarFixed',
        plugins: {
            'halloformat': {},
            'halloheadings': {},
            'hallolists': {},
            'halloreundo': {},
            'halloverdantimage': {},
            'halloverdantlink': {}
        }
    }).bind('hallomodified', function(event, data) {
        input.val(data.content);
    });
}


function createPageChooser(id, pageType, openAtParentId) {
    var chooserElement = $('#' + id + '-chooser');
    var pageTitle = chooserElement.find('.page-title');
    var input = $('#' + id);

    $('.action-choose-page', chooserElement).click(function() {
        var initialUrl = '/admin/choose-page/' + pageType + '/';
        /* TODO: don't hard-code this URL, as it may be changed in urls.py */
        if (openAtParentId) {
            initialUrl += openAtParentId + '/';
        }
        ModalWorkflow({
            'url': initialUrl,
            'responses': {
                'pageChosen': function(pageData) {
                    input.val(pageData.id);
                    openAtParentId = pageData.parentId;
                    pageTitle.text(pageData.title);
                    chooserElement.removeClass('blank');
                }
            }
        });
    });

    $('.action-clear', chooserElement).click(function() {
        input.val('');
        openAtParentId = null;
        chooserElement.addClass('blank');
    });
}
