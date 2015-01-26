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
* Catch Save dialog
*/

$('.submit-page').click(function(e) {
    // e.preventDefault();
    if (window.confirm("Sending this post for moderation means you can no longer make changes, would you like to go ahead and send it for moderation?")) {
        $(this).parent().submit();
        return true;
    } else {
        return false;
    }
});

/*
* Catch delete dialog
*/

$('.delete-post').click(function(e) {
    e.preventDefault();
    if (window.confirm("Would you like to go ahead with deleting this post?")) {
        $(this).parent().submit();
        return true;
    } else {
        return false;
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

