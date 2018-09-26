$(function(){
    var $testimonialSlider = $('.js-testimonial');
    var prevButton = '<button aria-label="Previous" class="slider__button slider__button--prev" type="button"><svg class="slider__arrow slider__arrow--prev"><title>Previous</title><use xlink:href="#chevron"></use></svg></button>';
    var nextButton = '<button aria-label="Next" class="slider__button slider__button--next" type="button"><svg class="slider__arrow slider__arrow--next"><title>Previous</title><use xlink:href="#chevron"></use></svg></button>';

    $testimonialSlider.slick({
        prevArrow: prevButton,
        nextArrow: nextButton,
        infinte:true,
        dots: true,
        slidesToShow: 1
    });
});
