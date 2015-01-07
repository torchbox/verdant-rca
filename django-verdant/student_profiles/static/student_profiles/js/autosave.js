/**
 *  Enable auto-saving for the given form.
 */
var autosaveTimers = {}
function enableAutosave(formsel) {
    autosaveTimers[formsel] = 0;
    var form = $(formsel);
    var delay = 4000;
    var delayShowSaved = 2000;
    var saveString = '';
    var overlay = $('<div id="overlay">Saving...</div>').appendTo(document.body).css('top', '-3em');
    
    function save(element) {
        clearTimeout(autosaveTimers[formsel]);   // we clear the timeout because we only want to save n seconds after the last edit
        window.onbeforeunload = confirmOnPageExit;

        autosaveTimers[formsel] = setTimeout(function() {
            window.onbeforeunload = null;
            var dataString = form.serialize();
            if (saveString == dataString)
            {
                // no need to save because nothing changed
                return;
            }
            saveString = dataString;
            
            overlay.html('Saving...').animate({'top': 0}, 400);
            
            $.ajax({
                type: "POST",
                data: dataString,
                success: function(msg) {
                    if (msg.ok)
                    {
                        overlay.html('Saved!');
                        setTimeout(function() {
                            overlay.animate({'top': '-3em'}, 400);
                        }, 2000);
                    }
                    else {
                        overlay.css('background-color', '#f00').html('Could not save. Please save manually!');
                    }
                },
                error: function(msg) {
                    overlay.css('background-color', '#f00').html('Could not save. Please save manually!');
                }
            });
        }, delay);
    }
    
    $(form).find('input').each(function(i, val) {
        $(val).change(save);
        $(val).keyup(save);
    });
    $(form).find('select').each(function(i, val) {
        $(val).change(save);
    });
    $(form).find('textarea').each(function(i, val) {
        $(val).change(save);
        $(val).keyup(save);
    });
}
// stop any autosave timers that might be running at the moment
function stopAutosave() {
    for (i in autosaveTimers)
    {
        clearTimeout(autosaveTimers[i]);
    }
}
// and then immediately enable it for the profile-form in the view
enableAutosave('form.student-profile');
