function throttle(fn, threshhold, scope) {
    threshhold || (threshhold = 250);
    var last, deferTimer;
    return function () {
        var context = scope || this;

        var now = +new Date, args = arguments;
        if (last && now < last + threshhold) {
            // hold on to it
            clearTimeout(deferTimer);
            deferTimer = setTimeout(function () {
                last = now;
                fn.apply(context, args);
            }, threshhold);
        } else {
            last = now;
            fn.apply(context, args);
        }
    };
}

function setWidth(carousel, width){
    $('.caption', carousel).css({maxWidth:'none', width:width});
}

$(function(){
    
    $('.carousel-news').each(function(){
        $this = $(this);
        $carousel = $('.carousel-content', $this);
        
        setWidth($carousel, $('.active', $carousel).width());

        $('> li', $carousel).bind('mouseover click', function(){
            $('> li', $carousel).removeClass('active');
            $(this).addClass('active');
        })

        $(window).resize(throttle(function(){
            setWidth($carousel, $('.active', $carousel).width());
        }));
    });    
})