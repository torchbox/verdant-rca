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
            containerElement.find('#progress .bar').show();
            originalAdd.call(this, e, data);
        },
        done: function (e, data) {
    
            containerElement.find('#progress .bar').hide();
            if (!data.result.ok)
            {
                alert("Could not upload the file. Please try again with a different file.");
            }
            else
            {
                containerElement.find('#preview').html(data.files[0].preview);
                containerElement.find('#preview').append('<span>' + data.files[0].name + '</span>');
                containerElement.find('#preview').append('<div id="info-flash" style="z-index: 100; background-color: #FF7B0A; position: absolute; top: 0; left: 0; width: 100%; height: 100%; text-align: center; font-size: 250%;">Saved</div>');
                containerElement.find('#preview #info-flash').fadeOut(2000);
          
                idElement.val(data.result.id);
            }
        },
        fail: function (e, data) {
            alert("Could not upload the file: the server responded with an error.");
            containerElement.find('#progress .bar').hide();
        },
        progressall: function (e, data) {
            var progress = parseInt(data.loaded / data.total * 100, 10);
            containerElement.find('#progress .bar').css('width', progress + '%');
        }
    };
    options = options || {};
    upload_options = $.extend(upload_options, options);

    // activate the file upload field
    $(containerElement).fileupload(upload_options);
}

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


