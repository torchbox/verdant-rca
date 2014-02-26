
// TODO:
// * adjust top position of content when the header is not collapsed
// * bind click handlers to selected elements only
// * add chaching

window.initialUrl = window.location.href;

function fixLightboxHeight(){
    // .pjax-content is pos:abs and doesn't have a height,
    // so we need to calculate it based on the children
    // this might need to be run multiple times to account for image heights
    $('.pjax-content, .pjax-wrapper').css("height", "");
    $('.pjax-content').addClass("measure-height-helper");
    var newHeight = $('.pjax-content').height();
    $('.pjax-content').height(newHeight);
    $('.pjax-wrapper').height($('.pjax-content').outerHeight() + 186);
    $('.pjax-content').removeClass("measure-height-helper");
}

History.Adapter.bind(window, 'statechange', function(){ // Note: We are using statechange instead of popstate
    var state = History.getState(); // Note: We are using History.getState() instead of event.state
    // We should use if(state.data.showLightbox) but the initial data can get mixed up
    // with the following ones after full page reloads, so we're not relying on that
    if(state.url != window.initialUrl){
        $.ajax({
            url: state.url,
            success: function(data, status, xhr){
                var obj = extractContainer(data, xhr, {
                        requestUrl: state.url,
                        fragment: ".page-content > .inner"
                });
                $(".pjax-content").html(obj.contents);

                window.prevScrollY = window.scrollY;

                // needed so that the browser can scroll back when closing the lightbox
                $("body, html").css("min-height", $(document).height());

                // display lightbox
                $("body").addClass("lightbox-view");


                // disable bs-affix because it would interfer with positioning
                $(".page-wrapper").data('bs.affix').disable();
                $(".page-wrapper").removeClass('affix affix-top');

                var affixed = $(".header-wrapper").hasClass("affix");
                $(".page-wrapper").css({
                    top: -window.scrollY + (affixed ? 186 : 200)
                });

                if(window.scrollY > 151){
                    // scroll to top, but leave the menu collapsed
                    $(window).scrollTop(151);
                }

                // resize lightbox to fit contents:
                fixLightboxHeight();
                setTimeout(fixLightboxHeight, 1000);
            }
        });
    }else{
        var affixed = $(".header-wrapper").hasClass("affix");

        // hide overlay
        $("body").removeClass("lightbox-view");

        // re-enable bs-affix on .page-wrapper
        $(".page-wrapper").css({
            top: ""
        });
        $(".page-wrapper").data('bs.affix').enable();
        $(".page-wrapper").addClass("affix");

        // scroll back to the original position
        $(window).scrollTop(window.prevScrollY);
    }
});

$(document).on('click', 'aside a', function(event) {
    History.pushState({showLightbox: true}, $(this).text(), $(this).attr("href"));
    return false;
});


$(window).on("load", function(){
    // var Affix = $('[data-spy="affix"]').eq(0).data('bs.affix').constructor;
    var Affix = $('.page-wrapper').eq(0).data('bs.affix').constructor;
    Affix.prototype.disable = function(){
        if(this.$element.length){
            this._$element = this.$element;
            this.$element = $([]);
        }
    };
    Affix.prototype.enable = function(){
        if(this._$element){
            this.$element = this._$element;
        }
    };
});

