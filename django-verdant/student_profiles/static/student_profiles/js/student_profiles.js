/**
* Load the given file to check whether this is a readable image.
*/
function checkImageFile(file, dfd, data) {

    var reader = new FileReader();
    var image  = new Image();
    
    reader.readAsDataURL(file);  
    reader.onload = function(_file) {
        image.src    = _file.target.result;
        image.onload = function() {
            dfd.resolveWith(this, [data]);
        };
        image.onerror= function() {
            file.error = 'Invalid file type.';
            dfd.rejectWith(this, [data]);
        };
    };
  
}

/**
* Put our image validation in the jquery-fileupload processing queue
*/
$.blueimp.fileupload.prototype.processActions.validate = function (data, options) {
    if (options.disabled) {
        return data;
    }
    var dfd = $.Deferred(),
    file = data.files[data.index];

    if (!options.acceptFileTypes.test(file.type)) {
        file.error = 'Invalid file type.';
        dfd.rejectWith(this, [data]);
    } else {
        checkImageFile(file, dfd, data);
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
        imageMaxWidth: 800,
        imageMaxHeight: 800,
        imageMinWidth: 10,
        imageMinHeight: 10,
        sequentialUploads: true,
        dropZone: dropElement,
        paramName: 'image',

        acceptFileTypes: /(\.|\/)(gif|jpe?g|png)$/i,

        processfail: function (e, data) {
            alert('Could not upload ' + data.files[data.index].name + ': this file is not a valid image.');
        },
        add: function(e, data) {
            containerElement.find('.progress .bar').show();
            window.onbeforeunload = confirmOnPageExit;
            originalAdd.call(this, e, data);
        },
        done: function (e, data) {
    
            containerElement.find('.progress .bar').hide();
            if (!data.result.ok)
            {
                alert("Could not upload the file. Please try again with a different file.");
            }
            else
            {
                containerElement.find('.preview').html(data.files[0].preview);
                containerElement.find('.preview').show();
                containerElement.find('.clearbutton').show();
          
                idElement.val(data.result.id);
                idElement.change();
            }
        },
        fail: function (e, data) {
            containerElement.find('.progress .bar').hide();
            alert("Could not upload the file: the server responded with an error.");
        },
        progress: function (e, data) {
            var progress = parseInt(data.loaded / data.total * 100, 10);
            containerElement.find('.progress .bar').css('width', progress + '%');
        },
    };
    options = options || {};
    upload_options = $.extend(upload_options, options);

    $(containerElement).fileupload(upload_options);
    
    // set the "clear field" button action
    containerElement.find('.clearbutton').click(function(e) {
        $(this).hide();
        containerElement.find('.preview').html('');
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
        console.log("Unstick");
    } else {
        $('.notes').sticky({
            topSpacing: 200,
            bottomSpacing: 680
        });
        console.log("Stick");
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
    e.preventDefault();
    if (window.confirm("Sending this form for moderation means you can no longer make changes, would you like to go ahead and send it for moderation?")) {
        $(this).submit();
    }
})


