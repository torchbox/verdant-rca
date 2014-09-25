/* Procedural enhancement of galleries that use colorbox as a lightbox modal popup */
$(function(){
	"use strict";

	// gallery lightboxes
    $('a.lightbox').one('click', function(){
        // lazy init on click
        $('a.lightbox').colorbox({
            rel: '.lightbox',
            overlayClose: true,
            opacity: 0.7,
        	inline: function(){ return $(this).hasClass('inline')},
        	width: function(){ return ($(this).hasClass('inline')) ? "50%" : null },
            height: function(){ return ($(this).hasClass('inline')) ? null : ($(window).height() * (0.9)) },
            maxWidth: function(){ return $(window).width() * 0.9},
            onOpen: function(){
                $('body').addClass('gallery-lightbox-open');
            },
            onClosed: function(){
                $('body').removeClass('gallery-lightbox-open');
            }
        });

        // then run the item clicked
        $(this).trigger('click');
        return false
    });
})