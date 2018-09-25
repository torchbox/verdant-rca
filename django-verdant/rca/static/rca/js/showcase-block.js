$(function(){
    // Showcase carousel
    var $showcaseSlider = $('.js-showcase');
    var prevButton = '<button aria-label="Previous" class="showcase__prev showcase__button" type="button"><svg class="showcase__arrow"><title>Previous</title><use xlink:href="#chevron"></use></svg></button>';
    var nextButton = '<button aria-label="Next" class="showcase__next showcase__button" type="button"><svg class="showcase__arrow"><title>Previous</title><use xlink:href="#chevron"></use></svg></button>';

    $showcaseSlider.slick({
        // medium and large desktop
        prevArrow: prevButton,
        nextArrow: nextButton,
        centerMode: true,
        infinte:true,
        slidesToShow: 3,
        responsive: [
            {
                // small desktop / mobile
                breakpoint: 1024,
                settings: {
                    centerMode: true,
                    centerPadding: '40px',
                    slidesToShow: 1
                }
            }
        ]
    });
});