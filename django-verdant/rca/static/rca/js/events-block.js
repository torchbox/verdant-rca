$(function(){
    // Events carousel
    var $eventsSlider = $('.js-events');
    var prevButton = '<button aria-label="Previous" class="slider__button slider__button--prev" type="button"><svg class="slider__arrow slider__arrow--prev"><title>Previous</title><use xlink:href="#chevron"></use></svg></button>';
    var nextButton = '<button aria-label="Next" class="slider__button slider__button--next" type="button"><svg class="slider__arrow slider__arrow--next"><title>Previous</title><use xlink:href="#chevron"></use></svg></button>';

    $eventsSlider.slick({
        // large desktop
        prevArrow: prevButton,
        nextArrow: nextButton,
        infinte: true,
        centerMode: true,
        centerPadding: 'calc(5vw - 8px)',
        slidesToShow: 3,
        responsive: [
            {
                // mobile
                breakpoint: 1024,
                settings: {
                    slidesToShow: 1,
                    centerPadding: '13px',
                }
            }
        ]
    });
});
