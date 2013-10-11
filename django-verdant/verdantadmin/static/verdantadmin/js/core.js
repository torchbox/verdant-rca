$(function(){
    // Enable toggle to open/close nav
    $('#nav-toggle').click(function(){ 
        $('body').toggleClass('nav-open');
    });

    // Enable swishy section navigation menu
    $('.explorer').addClass('dl-menuwrapper').dlmenu({
        animationClasses : {
            classin : 'dl-animate-in-2', 
            classout : 'dl-animate-out-2'
        } 
    });

    // Resize nav to fit height of window. This is an unimportant bell/whistle to make it look nice
    var fitNav = function(){
        $('.nav-wrapper').css('min-height',$(window).height());
    }
    fitNav();
    $(window).resize(function(){
        fitNav();
    })

    // Apply auto-height sizing to text areas
    // NB .richtext (hallo.js-enabled) divs do not need this as they expand to fit their content by default
    $('textarea').autosize();

    // Enable nice focus effects on all fields. This enables help text on hover.
    $(document).on('focus mouseover', 'input,textarea,select', function(){
    	$(this).closest('.field').addClass('focused')
    	$(this).closest('fieldset').addClass('focused')
        $(this).closest('li').addClass('focused')
    })
    $(document).on('blur mouseout', 'input,textarea,select', function(){
    	$(this).closest('.field').removeClass('focused')
    	$(this).closest('fieldset').removeClass('focused')
        $(this).closest('li').removeClass('focused')
    });

    /* tabs */
    $('.tab-nav a').click(function (e) {
        e.preventDefault()
        $(this).tab('show');
    });   

    // Add class to the body from which transitions may be hung so they don't appear to transition as the page loads
    $('body').addClass('ready'); 

    $('.dropdown-toggle').bind('click', function(){
        $(this).closest('.dropdown').toggleClass('open');
    });

    /* Bulk-selection */
    $(document).on('click', 'thead .bulk', function(){
        $(this).closest('table').find('tbody .bulk input').each(function(){
            $(this).prop('checked', !$(this).prop('checked'));            
        })
    });
})