function makeRichTextEditable(id) {
    var input = $('#' + id);
    var richText = $('<div class="richtext"></div>').html(input.val());
    richText.insertBefore(input);
    input.hide();

    function removeStylingSpans(context) {
        /* Strip the 'style' attribute from spans that have no other attributes.
        (we don't remove the span entirely as that messes with the cursor position,
        and spans will be removed anyway by our whitelisting)
        */
        $('span[style]', context).filter(function() {
            return this.attributes.length === 1;
        }).removeAttr('style');
    }

    richText.hallo({
        toolbar: 'halloToolbarFixed',
        plugins: {
            'halloformat': {},
            'halloheadings': {},
            'hallolists': {},
            'halloreundo': {},
            'halloverdantimage': {},
            'halloverdantlink': {},
            'halloverdantdoclink': {}
        }
    }).bind('hallomodified', function(event, data) {
        input.val(data.content);
    }).bind('paste', function(event, data) {
        setTimeout(function() {
            removeStylingSpans(richText);
        }, 1);
    });
}


function createPageChooser(id, pageType, openAtParentId) {
    var chooserElement = $('#' + id + '-chooser');
    var pageTitle = chooserElement.find('.page-title');
    var input = $('#' + id);

    $('.action-choose', chooserElement).click(function() {
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

function initDateChoosers(context) {
    $('input.friendly_date', context).datepicker({
        dateFormat: 'd M yy', constrainInput: false, /* showOn: 'button', */ firstDay: 1
    });
}
function initDateChooser(id) {
    $('#' + id).datepicker({
        dateFormat: 'd M yy', constrainInput: false, /* showOn: 'button', */ firstDay: 1
    });
}

$(function() {
    initDateChoosers();
});

function InlinePanel(opts) {
    var self = {};

    self.initInlineChildDeleteButton = function (prefix) {
        var childId = 'inline_child_' + prefix;
        var deleteInputId = 'id_' + prefix + '-DELETE';
        $('#' + deleteInputId + '-button').click(function() {
            /* set 'deleted' form field to true */
            $('#' + deleteInputId).val('1');
            $('#' + childId).fadeOut();
        });
    };

    buildExpandingFormset(opts.formsetPrefix, {
        onAdd: function(formCount) {
            function fixPrefix(str) {
                return str.replace(/__prefix__/g, formCount);
            }
            self.initInlineChildDeleteButton(fixPrefix(opts.emptyChildFormPrefix));
            if (opts.canOrder) {
                $(fixPrefix('#id_' + opts.emptyChildFormPrefix + '-ORDER')).val(formCount);
            }
            opts.onAdd(fixPrefix);
        }
    });

    return self;
}
