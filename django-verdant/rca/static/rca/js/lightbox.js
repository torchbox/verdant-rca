/* Procedural enhancement of galleries that use colorbox as a lightbox modal popup */
$(function(){
	"use strict";

	// gallery lightboxes
    $('a.lightbox').one('click', function(){
        // lazy init on click
        $('a.lightbox').colorbox({
        	inline: function(){return $(this).hasClass('inline')},
        	width: function(){return ($(this).hasClass('inline')) ? "50%" : null },
            rel: '.lightbox',
            overlayClose: true,
            opacity: 0.7
        });

        // then run the item clicked
        $(this).trigger('click');
        return false
    });
})