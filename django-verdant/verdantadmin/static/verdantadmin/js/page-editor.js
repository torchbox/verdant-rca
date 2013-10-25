function makeRichTextEditable(id) {
    var input = $('#' + id);
    var richText = $('<div class="richtext"></div>').html(input.val());
    richText.insertBefore(input);
    input.hide();

    var removeStylingPending = false;
    function removeStyling() {
        /* Strip the 'style' attribute from spans that have no other attributes.
        (we don't remove the span entirely as that messes with the cursor position,
        and spans will be removed anyway by our whitelisting)
        */
        $('span[style]', richText).filter(function() {
            return this.attributes.length === 1;
        }).removeAttr('style');
        removeStylingPending = false;
    }

    richText.hallo({
        toolbar: 'halloToolbarFixed',
        toolbarcssClass: 'testy',
        plugins: {
            'halloformat': {},
            'halloheadings': {formatBlocks: ["p", "h2", "h3", "h4", "h5"]},
            'hallolists': {},
            'hallohr': {},
            'halloreundo': {},
            'halloverdantimage': {},
            'halloverdantlink': {},
            'halloverdantdoclink': {},
        }
    }).bind('hallomodified', function(event, data) {
        input.val(data.content);
        if (!removeStylingPending) {
            setTimeout(removeStyling, 100);
            removeStylingPending = true;
        }
    }).bind('paste', function(event, data) {
        setTimeout(removeStyling, 1);
    });
}

function insertRichTextDeleteControl(elem) {
    var a = $('<a class="icon icon-cross text-replace delete-control">Delete</a>');
    $(elem).addClass('rich-text-deletable').prepend(a);
    a.click(function() {
        $(elem).fadeOut(function() {
            $(elem).remove();
        });
    })
}


function createPageChooser(id, pageType, openAtParentId) {
    var chooserElement = $('#' + id + '-chooser');
    var pageTitle = chooserElement.find('.title');
    var input = $('#' + id);

    $('.action-choose', chooserElement).click(function() {
        var initialUrl = '/admin/choose-page/';
        /* TODO: don't hard-code this URL, as it may be changed in urls.py */
        if (openAtParentId) {
            initialUrl += openAtParentId + '/';
        }
        ModalWorkflow({
            'url': initialUrl,
            'urlParams': {'page_type': pageType},
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
    $('.richtext [contenteditable="false"]').each(function() {
        insertRichTextDeleteControl(this);
    });

    /* Set up behaviour of preview button */
    $('#action-preview').click(function() {
        var previewWindow = window.open('', $(this).data('windowname'));
        $.post(
            $(this).data('action'),
            $('#page-edit-form').serialize(),
            function(data, textStatus, request) {
                if (request.getResponseHeader('X-Verdant-Preview') == 'ok') {
                    previewWindow.document.open();
                    previewWindow.document.write(data);
                    previewWindow.document.close();
                } else {
                    previewWindow.close();
                    document.open();
                    document.write(data);
                    document.close();
                }
            }
        );
    });
});

function InlinePanel(opts) {
    var self = {};

    self.initChildControls = function (prefix) {
        var childId = 'inline_child_' + prefix;
        var deleteInputId = 'id_' + prefix + '-DELETE';
        $('#' + deleteInputId + '-button').click(function() {
            /* set 'deleted' form field to true */
            $('#' + deleteInputId).val('1');
            $('#' + childId).fadeOut(function() {
                self.updateMoveButtonDisabledStates();
            });
        });
        if (opts.canOrder) {
            $('#' + prefix + '-move-up').click(function() {
                var currentChild = $('#' + childId);
                var currentChildOrderElem = currentChild.find('input[name$="-ORDER"]');
                var currentChildOrder = currentChildOrderElem.val();

                /* find the previous visible 'inline_child' li before this one */
                var prevChild = currentChild.prev(':visible');
                if (!prevChild.length) return;
                var prevChildOrderElem = prevChild.find('input[name$="-ORDER"]');
                var prevChildOrder = prevChildOrderElem.val();
                
                // async swap animation must run before the insertBefore line below, but doesn't need to finish first
                self.animateSwap(currentChild, prevChild);

                currentChild.insertBefore(prevChild);
                currentChildOrderElem.val(prevChildOrder);
                prevChildOrderElem.val(currentChildOrder);

                self.updateMoveButtonDisabledStates();
            });

            $('#' + prefix + '-move-down').click(function() {
                var currentChild = $('#' + childId);
                var currentChildOrderElem = currentChild.find('input[name$="-ORDER"]');
                var currentChildOrder = currentChildOrderElem.val();

                /* find the next visible 'inline_child' li after this one */
                var nextChild = currentChild.next(':visible');
                if (!nextChild.length) return;
                var nextChildOrderElem = nextChild.find('input[name$="-ORDER"]');
                var nextChildOrder = nextChildOrderElem.val();

                // async swap animation must run before the insertAfter line below, but doesn't need to finish first
                self.animateSwap(currentChild, nextChild);

                currentChild.insertAfter(nextChild);
                currentChildOrderElem.val(nextChildOrder);
                nextChildOrderElem.val(currentChildOrder);

                self.updateMoveButtonDisabledStates();
            });
        }
    };

    self.formsUl = $('#' + opts.formsetPrefix + '-FORMS');
    
    self.updateMoveButtonDisabledStates = function() {
        if (opts.canOrder) {
            forms = self.formsUl.children('li:visible');
            forms.each(function(i) {
                $('ul.controls .inline-child-move-up', this).toggleClass('disabled', i == 0);
                $('ul.controls .inline-child-move-down', this).toggleClass('disabled', i == forms.length - 1);
            });
        }
    }

    self.animateSwap = function(item1, item2){
        var parent = self.formsUl;
        var children = parent.children('li:visible');

        // Apply moving class to container (ul.multiple) so it can assist absolute positioning of it's children
        // Also set it's relatively calculated height to be an absolute one, to prevent the container collapsing while its children go absolute 
        parent.addClass('moving').css('height', parent.height());
        
        children.each(function(){
            console.log($(this));
            $(this).css('top', $(this).position().top);
        }).addClass('moving');

        // animate swapping around
        item1.animate({
            top:item2.position().top
        }, 200, function(){
            parent.removeClass('moving').removeAttr('style');
            children.removeClass('moving').removeAttr('style');
        });
        item2.animate({
            top:item1.position().top
        }, 200, function(){
            parent.removeClass('moving').removeAttr('style');
            children.removeClass('moving').removeAttr('style');
        })
    }

    buildExpandingFormset(opts.formsetPrefix, {
        onAdd: function(formCount) {
            function fixPrefix(str) {
                return str.replace(/__prefix__/g, formCount);
            }
            self.initChildControls(fixPrefix(opts.emptyChildFormPrefix));
            if (opts.canOrder) {
                $(fixPrefix('#id_' + opts.emptyChildFormPrefix + '-ORDER')).val(formCount);
            }
            self.updateMoveButtonDisabledStates();
            opts.onAdd(fixPrefix);
        }
    });

    return self;
}
