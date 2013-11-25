$(function(){
    function pixelToNumber(val){
        return parseInt(("" + val).replace(/[\-px]+/g, ""), 10);
    }
    var $slider = $(".slider");
    var $left = $(".wrapper-left");
    var $right = $(".wrapper-right");
    var scrollY;

    $(".search input").toggleClick(function(){
        var leftOffset = $left.offset();
        var leftMarginTop = pixelToNumber($left.css("margin-top"));
        var leftWidht = $left.width();
        scrollY = window.scrollY;

        $right.addClass("wrapper-right-before-slide-right");
        $slider.addClass("slider-animate-slide-right", 1000, function(){
            $left.addClass("wrapper-left-after-slide-right");
            $left.css({
                top: - scrollY + leftOffset.top - leftMarginTop,
                left: -leftWidht,
                width: leftWidht
            });
        });

    }, function(){
        $left.removeClass("wrapper-left-after-slide-right");
        $left.attr("style", "");
        $slider.removeClass("slider-animate-slide-right", 1000, function(){
            $right.removeClass("wrapper-right-before-slide-right");
            $(window).scrollTop(scrollY);
        });

    });
});
