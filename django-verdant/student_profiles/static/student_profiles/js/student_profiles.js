/**
 * Make a given 'id' into a hallo.js rich text editor with our plugins and stylings.
 */
function makeRichTextEditable(id) {

    var halloPlugins = {
        'halloformat': {},
        'halloheadings': {formatBlocks: ["p", "h4", ]},
        'hallohr': {},
        'halloreundo': {},
    };

    var input = $('#' + id);
    var richText = $('<div class="richtext"></div>').html(input.val());
    richText.insertBefore(input);
    $('<p class="help-text">If you paste formatted text into this field (for example from a Word document) and it doesn’t look right, please use the ‘Save as Draft’ button at the bottom of the screen, which should clean up any problems.</p>').insertAfter(input);
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
        toolbarCssClass: (input.closest('.object').hasClass('full')) ? 'full' : '',
        plugins: halloPlugins
    }).bind('hallomodified', function(event, data) {
        input.val(data.content);
        if (!removeStylingPending) {
            setTimeout(removeStyling, 100);
            removeStylingPending = true;
        }
    }).bind('paste', function(event, data) {
        setTimeout(removeStyling, 1);
    }).bind('halloactivated', function(event, data) {
        $('span.ui-button-text').each(function(i, el) {
            var jel = $(el);
            if (jel.text() == 'P'){
                jel.html('TEXT <i></i>');  // this one is a hack to add the <i> element: it changes the way the button is laid out and moves it into alignment with the other buttons
                jel.parent().css('width', '8em');
            } else if (jel.text() == 'H4'){
                jel.html('HEADING<i></i>');
                jel.parent().css('width', '8em');
            }
        });
    });
}


/**
* Load the given file to check whether this is a readable image.
*/
function checkImageFile(file, dfd, data, options) {

    var reader = new FileReader();
    var image  = new Image();
    var minWidth = options.imageMinWidth;
    var minHeight = options.imageMinHeight;
    
    reader.readAsDataURL(file);  
    reader.onload = function(_file) {
        image.src    = _file.target.result;
        image.onload = function() {

            if (
                (image.width < minWidth || image.height < minHeight)
                && (image.height < minWidth || image.width < minHeight))
            {
                data.error = 'Minimum image size is: ' + minWidth + 'x' + minHeight + '.';
                dfd.rejectWith(this, [data]);
            } else {
            dfd.resolveWith(this, [data]);
                $(".preview").addClass("has-image");
            }
        };
        image.onerror= function() {
            data.error = 'Invalid file type: only gif, jpg and png are allowed. Changing file extension does not change the file type.';
            dfd.rejectWith(this, [data]);
        };
    };
  
}

/**
* Put our image validation in the jquery-fileupload processing queue
*/
$.blueimp.fileupload.prototype.processActions.validate_img = function (data, options) {
    if (options.disabled) {
        return data;
    }
    var dfd = $.Deferred(),
    file = data.files[data.index];

    if (options.maxFileSize < file.size)
    {
        data.error = 'File is too large. Please make sure your file is smaller than ' + Math.floor(options.maxFileSize / 1024 / 1024) + ' MB.';
        dfd.rejectWith(this, [data]);
    } else if (!options.acceptFileTypes.test(file.type)) {
        data.error = 'Invalid file type: only gif, jpg and png are allowed.';
        dfd.rejectWith(this, [data]);
    } else {
        checkImageFile(file, dfd, data, options);
    }
    return dfd.promise();
};

/**
* Nice little hover-effect for file dropping.
*/ 
$(document).bind('dragover', function (e)
{
    var dropZone = $('.dropzone'),
    foundDropzone,
    timeout = window.dropZoneTimeout;
    if (!timeout)
    {
        dropZone.addClass('in');
    }
    else
    {
        clearTimeout(timeout);
    }
    var found = false,
    node = e.target;

    do{

        if ($(node).hasClass('dropzone'))
        {
            found = true;
            foundDropzone = $(node);
            break;
        }

        node = node.parentNode;

    }while (node != null);

    dropZone.removeClass('in hover');

    if (found)
    {
        foundDropzone.addClass('hover');
    }

    window.dropZoneTimeout = setTimeout(function ()
    {
        window.dropZoneTimeout = null;
        dropZone.removeClass('in hover');
    }, 100);
});

/**
* The actual data-binding function that enables file uploads
*/ 
function activateImageUpload(for_id, options) {

    // prevent the automatic drop handler because we want specific drop zones
    $(document).bind('drop dragover', function (e) {
        e.preventDefault();
    });

    // remember the original add function for later because we're going to overwrite it
    var originalAdd = $.blueimp.fileupload.prototype.options.add;
    var containerElement = $($('#' + for_id));
    var dropElement = containerElement.find('.dropzone');
    var idElement = containerElement.find('#id_' + for_id + '_val');
    
    var upload_options = {
        dataType: 'json',
        imageMinWidth: 0,
        imageMinHeight: 0,
        maxFileSize: 99999999999999999999,  // TO INFINITY AND BEYOND!!
        sequentialUploads: true,
        dropZone: dropElement,
        paramName: 'image',

        processQueue: [
            {
                action: 'validate_img',
                acceptFileTypes: '@',
                maxFileSize: '@',
                imageMinWidth: '@',
                imageMinHeight: '@',
                disabled: '@disableValidation'
            },
            {
                action: 'loadImageMetaData',
                disableImageHead: '@',
                disableExif: '@',
                disableExifThumbnail: '@',
                disableExifSub: '@',
                disableExifGps: '@',
                disabled: '@disableImageMetaDataLoad'
            },
            {
                action: 'loadImage',
                // Use the action as prefix for the "@" options:
                prefix: true,
                fileTypes: '@',
                maxFileSize: '@',
                noRevoke: '@',
                disabled: '@disableImageLoad'
            },
            {
                action: 'saveImage',
                quality: '@imageQuality',
                type: '@imageType',
                disabled: '@disableImageResize'
            },
            {
                action: 'resizeImage',
                // Use "preview" as prefix for the "@" options:
                prefix: 'preview',
                maxWidth: '@',
                maxHeight: '@',
                minWidth: '@',
                minHeight: '@',
                crop: '@',
                orientation: '@',
                thumbnail: '@',
                canvas: '@',
                disabled: '@disableImagePreview'
            },
            {
                action: 'setImage',
                name: '@imagePreviewName',
                disabled: '@disableImagePreview'
            },
        ],
        acceptFileTypes: /(\.|\/)(gif|jpe?g|png)$/i,

        processfail: function (e, data) {
            $('.uploadModal').hide();
            res = 'Could not upload ' + data.files[data.index].name + ': ';
            if (data.error)
                res += data.error;
            else
                res += 'This is not a valid file.';

            alert(res);
        },
        add: function(e, data) {
            $('div.uploadModal #content .progress .bar').css('width', '0%');
            containerElement.find('.progress .bar').css('width', '0%');
            $('.uploadModal').show();
            containerElement.find('.progress .bar').show();
            window.onbeforeunload = confirmOnPageExit;
            originalAdd.call(this, e, data);
        },
        done: function (e, data) {
            $('.uploadModal').fadeOut(animDuration);
            containerElement.find('.progress .bar').hide();
            if (!data.result.ok)
            {
                res = 'Could not upload the file. Please try again with a different file. ';
                if (data.result.errors)
                {
                    res += data.result.errors;
                }
                alert(res);

            }
            else
            {
                var new_canvas = $(data.files[0].preview);
                new_canvas.attr('class', 'preview_canvas');
                containerElement.find('.preview_canvas').replaceWith(new_canvas);
                containerElement.find('.preview_canvas').show();
                containerElement.find('.clearbutton').show();
          
                idElement.val(data.result.id);
                idElement.change();
            }
        },
        fail: function (e, data) {
            $('.uploadModal').hide();
            containerElement.find('.progress .bar').hide();
            alert("Could not upload the file: the server responded with an error.");
        },
        progress: function (e, data) {
            var progress = parseInt(data.loaded / data.total * 100, 10);
            $('div.uploadModal #content .progress .bar').css('width', progress + '%');
            containerElement.find('.progress .bar').css('width', progress + '%');
        },
    };
    options = options || {};
    upload_options = $.extend(upload_options, options);

    $(containerElement).fileupload(upload_options);
    
    // set the "clear field" button action
    containerElement.find('.clearbutton').click(function(e) {
        $(this).hide();
        containerElement.find('.preview_canvas').replaceWith("<div class='preview_canvas'></div>");
        idElement.val(''); idElement.change();
        e.preventDefault();
    });
    
}

/**
* A simple animation for swapping two elements.
*/
var animDuration = 600;
function switchUp(elem) {
    var e1 = $(elem), e2 = e1.prev();
    var e1p = e1.position(), e2p = e2.position();

    var e1f = e1.find('.order-value'), e2f = e2.find('.order-value');
    var e1o = e1f.val(), e2o = e2f.val();
    e1f.val(e2o); e2f.val(e1o);
    e1f.change();

    e1.insertBefore(e2);
  
    e1.css('position', 'relative');
    e1.css('top', (e1p.top - e2p.top) + 'px');
    e1.animate({top: (e1p.top - e2p.top)/2 + 'px', left: '-30px'}, animDuration/2)
      .animate({top: '0px', left: '0px'}, animDuration/2);

    e2.css('position', 'relative');
    e2.css('top', (e2p.top - e1p.top) + 'px');
    e2.animate({top: (e2p.top - e1p.top)/2 + 'px', left: '30px'}, animDuration/2)
      .animate({top: '0px', left: '0px'}, animDuration/2);
};
function switchDown(elem) { switchUp($(elem).next()); };

/**
*  Given a list of jQuery element search terms, for each of the terms it will find all fitting elements and update
*  their move-up/move-down buttons with click and update handlers.
*  Example updateFormButtons('#myform .form-row');
*/
function updateFormButtons(search_term) {
  
    function updateIndividualButtonInForm(searchTerm, lastIndex) {
        return function(index, row) {
            if (index == 0) { $(row).find('.move-up').fadeOut(animDuration); }        // if we knew the width of the element, it would be nicer to have a width-animation
            else {  // not the first element, activate the move-up button
                $(row).find('.move-up').unbind('click').click(function() {
                    switchUp(row);
                    updateFormButtons(searchTerm);
                }).fadeIn(animDuration);
            }
            if (index == lastIndex) { $(row).find('.move-down').fadeOut(animDuration); }
            else {  // not the last element, activate the move-down button
                $(row).find('.move-down').unbind('click').click(function() {
                    switchDown(row);
                    updateFormButtons(searchTerm);
                }).fadeIn(animDuration);
            }
        }
    }
  
    var elems = $(search_term);
    elems.each(updateIndividualButtonInForm(search_term, elems.length-1));
};


/**
*  Enabling a formset with all necessary options
*/
function makeFormset(prefix, addedFunc) {
    var search_term = '#' + prefix + ' .inline-form';
    $(search_term).formset({
        minNumberOfForms: 1,
        prefix: prefix,
        formCssClass: 'dynamic-formset-' + prefix,
        added: function(row) {
            row.find('input.order-value').val($('#id_' + prefix + '-TOTAL_FORMS').val());
            updateFormButtons(search_term);
            if (addedFunc) addedFunc(row);
        },
        removed: function(row) {
            updateFormButtons(search_term);
        },
    });
  
    updateFormButtons(search_term);
};

/**
 * Update the carousel select items so that only the fields for the selection
 * that is active are shown.
 */
function updateCarouselSelects(prefix) {
  $('#' + prefix + ' select').change(function() {
    var value = $(this).val();
    var _match = this.id.match(/id_carousel-(\d+)-item_type/);
    var id_number = _match ? _match[1] : '';

    if (value == 'image')
    {
      $('#carousel-' + id_number + '-image_id').parent().show();
      $('#id_carousel-' + id_number + '-overlay_text').parent().show();
      $('#id_carousel-' + id_number + '-title').parent().show();
      $('#id_carousel-' + id_number + '-creator').parent().show();
      $('#id_carousel-' + id_number + '-year').parent().show();
      $('#id_carousel-' + id_number + '-medium').parent().show();
      $('#id_carousel-' + id_number + '-dimensions').parent().show();
      $('#id_carousel-' + id_number + '-photographer').parent().show();

      $('#id_carousel-' + id_number + '-embedly_url').parent().hide();
      $('#carousel-' + id_number + '-poster_image_id').parent().hide();

      $('#id_carousel-' + id_number + '-embedly_url').val('');
      $('#carousel-' + id_number + '-poster_image_id input').val('');
    } else if (value == 'video')
    {
      $('#carousel-' + id_number + '-image_id').parent().hide();
      $('#id_carousel-' + id_number + '-overlay_text').parent().hide();
      $('#id_carousel-' + id_number + '-title').parent().hide();
      $('#id_carousel-' + id_number + '-creator').parent().hide();
      $('#id_carousel-' + id_number + '-year').parent().hide();
      $('#id_carousel-' + id_number + '-medium').parent().hide();
      $('#id_carousel-' + id_number + '-dimensions').parent().hide();
      $('#id_carousel-' + id_number + '-photographer').parent().hide();

      $('#id_carousel-' + id_number + '-embedly_url').parent().show();
      $('#carousel-' + id_number + '-poster_image_id').parent().show();

      $('#carousel-' + id_number + '-image_id').val('');
      $('#id_carousel-' + id_number + '-overlay_text').val('');
      $('#id_carousel-' + id_number + '-title').val('');
      $('#id_carousel-' + id_number + '-creator').val('');
      $('#id_carousel-' + id_number + '-year').val('');
      $('#id_carousel-' + id_number + '-medium').val('');
      $('#id_carousel-' + id_number + '-dimensions').val('');
      $('#id_carousel-' + id_number + '-photographer').val('');
    }
  });
};

/**
 * Update the supervisor fields to only show those that are necessary for the selected type.
 */
function updateSupervisorSelects(prefix) {
  $('#' + prefix + ' select').change(function() {
    var value = $(this).val();
    var _match = this.id.match(/id_supervisor-(\d+)-supervisor_type/);
    var id_number = _match ? _match[1] : '';

    if (value == 'internal') {
      $('#id_supervisor-' + id_number + '-supervisor').parent().show();

      $('#id_supervisor-' + id_number + '-supervisor_other').parent().hide();
      $('#id_supervisor-' + id_number + '-supervisor_other').val('');

    }
    else if (value == 'other')
    {

      $('#id_supervisor-' + id_number + '-supervisor').parent().hide();
      $('#id_supervisor-' + id_number + '-supervisor').val('');

      $('#id_supervisor-' + id_number + '-supervisor_other').parent().show();
    }
  });
}


/*
* Stop user from leaving the page without confirmation.
*/
var confirmOnPageExit = function (e) 
{
    // If we haven't been passed the event get the window.event
    e = e || window.event;

    var message = 'You have unsaved changes. Are you sure you want to leave this page?';

    // For IE6-8 and Firefox prior to version 4
    if (e) 
    {
        e.returnValue = message;
    }

    // For Chrome, Safari, IE8+ and Opera 12+
    return message;
};
// but allow leaving via the submit button
$('form.student-profile input[type="submit"]').click(function() {
    window.onbeforeunload = null;
    stopAutosave();
});
$('form.now-page input[type="submit"]').click(function() {
    window.onbeforeunload = null;
    stopAutosave();
});

/*
* Prepare for AJAX calls with a CSRF token cookie.
*/
function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie != '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) == (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
var csrftoken = getCookie('csrftoken');
function csrfSafeMethod(method) {
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}
function sameOrigin(url) {
    // test that a given url is a same-origin URL
    // url could be relative or scheme relative or absolute
    var host = document.location.host; // host + port
    var protocol = document.location.protocol;
    var sr_origin = '//' + host;
    var origin = protocol + sr_origin;
    // Allow absolute or scheme relative URLs to same origin
    return (url == origin || url.slice(0, origin.length + 1) == origin + '/') ||
    (url == sr_origin || url.slice(0, sr_origin.length + 1) == sr_origin + '/') ||
    // or any other URL that isn't scheme relative or absolute i.e relative.
    !(/^(\/\/|http:|https:).*/.test(url));
}
$.ajaxSetup({
    beforeSend: function(xhr, settings) {
        if (!csrfSafeMethod(settings.type) && sameOrigin(settings.url)) {
            // Send the token to same-origin, relative URLs only.
            // Send the token only if the method warrants CSRF protection
            // Using the CSRFToken value acquired earlier
            xhr.setRequestHeader("X-CSRFToken", csrftoken);
        }
    }
});

/*
* Sticky notes
*/

function stickyNote() {
    if ($(window).width() < 1100) {
        $('.note').unstick();
    } else {
        $('.notes').sticky({
            topSpacing: 200,
            bottomSpacing: 680
        });
    }
}

$(window).resize(function() {
    stickyNote();
});

stickyNote();

/*
* Catch Save and Submit
*/
$('.submit-page').click(function(e) {
    if (window.confirm("DO NOT CLICK YES UNLESS YOUR PROFILE IS COMPLETE!\n\nYOU WILL NOT BE ABLE TO EDIT ANYTHING AFTER CLICKING OK, INCLUDING POSTCARD IMAGES!\n\nSending this form for moderation means you can no longer make changes or add content to your profile. Please check you have completed all sections before clicking OK.")) {
        $('#js_submit_for_moderation').val('submit_for_moderation');
        $(this).parents('form').submit();
        return true;
    } else {
        return false;
    }
});

$('.preview-post').click(function(e) {
    $(this).parents('form').attr('target', '_blank');
});


/*
* Catch delete dialog
*/
$('.delete-post').click(function(e) {
    if (window.confirm("Would you like to go ahead with deleting this post?")) {
        $(this).parent().submit();
        return true;
    } else {
        return false;
    }
});

/*
* Check for preview image
*/

if ($('.image-uploader-block .preview').children('img').length > 0 || $('.image-uploader-block .preview').children('canvas').length > 0) {
    $('.image-uploader-block .preview').addClass('has-image');
}

/*
* Remove image uploaded
*/
$('.preview.has-image').on('click',function() {
    $(this).removeClass('has-image');
});

/*
* Label is for checkbox
*/

$('input[type=checkbox]').closest('label').addClass('checkbox-label').children().first().before('<i class="icon ion-android-checkbox-blank"></i>');
$('input[type=checkbox]:checked').closest('label').children('.icon').removeClass('ion-android-checkbox-blank').addClass('ion-android-checkbox');

/*
* Handle checkedbox label status on change
*/

$('input[type=checkbox]').on('change',function() {
    if ($(this).is(':checked')) {
        $(this).parent().children('.icon').removeClass('ion-android-checkbox-blank').addClass('ion-android-checkbox');
    } else {
        $(this).parent().children('.icon').removeClass('ion-android-checkbox').addClass('ion-android-checkbox-blank');
    }
});

