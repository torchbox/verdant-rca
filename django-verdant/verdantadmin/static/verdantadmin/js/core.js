$(function(){
    $('#nav-toggle').click(function(){ 
        $('body').toggleClass('nav-open');
    });

    fitNav();
    $(window).resize(function(){
        fitNav();
    })

    $('textarea').autosize();

    $('.explorer').addClass('dl-menuwrapper').dlmenu({
        animationClasses : {
            classin : 'dl-animate-in-2', 
            classout : 'dl-animate-out-2'
        }
    });

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
})

function fitNav(){
    $('.nav-wrapper').css('min-height',$(window).height());
}
