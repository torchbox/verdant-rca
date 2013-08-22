$(function(){
    $('#nav-toggle').click(function(){ 
        $('body').toggleClass('nav-open');
    });

    $('textarea').autosize();

    $('.explorer').addClass('dl-menuwrapper').dlmenu({animationClasses : { classin : 'dl-animate-in-2', classout : 'dl-animate-out-2' }});
})
