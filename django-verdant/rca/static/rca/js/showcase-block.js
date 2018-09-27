$(function(){
    // Showcase carousel
    var $showcaseSlider = $('.js-showcase');
    var prevButton = '<button aria-label="Previous" class="slider__button slider__button--prev" type="button"><svg class="slider__arrow slider__arrow--prev"><title>Previous</title><use xlink:href="#chevron"></use></svg></button>';
    var nextButton = '<button aria-label="Next" class="slider__button slider__button--next" type="button"><svg class="slider__arrow slider__arrow--next"><title>Previous</title><use xlink:href="#chevron"></use></svg></button>';

    $showcaseSlider.slick({
        // medium and large desktop
        prevArrow: prevButton,
        nextArrow: nextButton,
        centerMode: true,
        infinte: true,
        slidesToShow: 3,
        centerPadding: 'calc(5vw - 8px)', // offset minus padding between items
        responsive: [
            {
                // small desktop
                breakpoint: 1024,
                settings: {
                    centerPadding: '5vw', // offset
                    slidesToShow: 1
                }
            },
            {
                breakpoint: 768,
                settings: {
                    centerPadding: '13px', // just works
                    slidesToShow: 1
                }
            }
        ]
    });
});
