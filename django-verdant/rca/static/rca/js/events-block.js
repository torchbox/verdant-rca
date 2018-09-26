$(function(){
    // Events carousel
    var $eventsSlider = $('.js-events');
    var prevButton = '<button aria-label="Previous" class="events-block__prev events-block__button" type="button"><svg class="events-block__arrow"><title>Previous</title><use xlink:href="#chevron"></use></svg></button>';
    var nextButton = '<button aria-label="Next" class="events-block__next events-block__button" type="button"><svg class="events-block__arrow"><title>Previous</title><use xlink:href="#chevron"></use></svg></button>';

    $eventsSlider.slick({
        // large desktop
        prevArrow: prevButton,
        nextArrow: nextButton,
        infinte: true,
        centerMode: true,
        centerPadding: '108px',
        slidesToShow: 3,
        responsive: [
            {
                // mobile
                breakpoint: 1024,
                settings: {
                    slidesToShow: 1,
                    centerPadding: '17px',
                }
            }
        ]
    });
});