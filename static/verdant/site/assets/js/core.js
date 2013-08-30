$(function(){
    $('#nav-toggle').click(function(){ 
        $('body').toggleClass('nav-open');
    });

    $('textarea').autosize();

    $('.explorer').addClass('dl-menuwrapper').dlmenu({animationClasses : { classin : 'dl-animate-in-2', classout : 'dl-animate-out-2' }});

    $('input,textarea,select').focus(function(){
    	$(this).closest('.field').addClass('focused')
    	$(this).closest('fieldset').addClass('focused')
    }).blur(function(){
    	$(this).closest('.field').removeClass('focused')
    	$(this).closest('fieldset').removeClass('focused')
    });
})
