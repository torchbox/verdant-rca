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

function setItemWidth(carousel, width){
    $('.caption, .image', carousel).css({width:width});
}


$(function(){
    $('.carousel-news').each(function(){
        var $this = $(this);
        var $carousel = $('.carousel-content', $this);
        
        setItemWidth($carousel, $('.active', $carousel).width());
        $this.addClass('ready');
       
        $('> li', $carousel).bind('mouseover click', function(){
            $('> li', $carousel).removeClass('active');
            $(this).addClass('active');
        })

        $(window).resize(throttle(function(){
            setItemWidth($carousel, $('.active', $carousel).width());
        }));
    });
})