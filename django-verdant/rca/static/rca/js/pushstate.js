$(function(){
    // TODO:
    // Add different base template for ajax requests:
    // {% extends request.is_ajax|yesno:"rca/base_ajax.html,rca/base.html" %}

    // window.disablePushState is set in site.js for small screens
    if(!Modernizr.history || window.disablePushState){
        return;
    }

    function scrollPostition(){
        return +(window.scrollY || window.pageYOffset);
    }

    var initialUrl = window.location.href;

    var affixOffsetTop = window.affixOffsetTop; // defined in site.js

    var prevScrollY = scrollPostition();

    var cache = {};

    function initLightbox(){

        prevScrollY = scrollPostition();

        // needed so that the browser can scroll back when closing the lightbox
        $("body, html").css("min-height", $(document).height());

        // display lightbox
        $("body").addClass("lightbox-view");

        // disable bs-affix because it would interfer with positioning
        $(".page-wrapper").data('bs.affix').disable();
        $(".page-wrapper").removeClass('affix affix-top');

        var affixed = $(".header-wrapper").hasClass("affix");
        $(".page-wrapper").css({
            top: -scrollPostition() + (affixed ? 186 : 200)
        });

        // scroll to top, but leave the menu collapsed
        $(window).scrollTop(affixOffsetTop);
    }

    function showLightbox(contentsObj){
        // Always take a clone of the content so js enhancement is done on a fresh DOM each time
        $(".pjax-content").html(contentsObj.contents.clone(false)).addClass(contentsObj.bodyClasses);
        $(".pjax-wrapper").attr('tabindex', '0');
        $("body").addClass('lightbox-visible');

        // we don't need to have min-height any more, it's set before opening the lightbox to help keep the scroll position
        $("body, html").css("min-height", 0);
        // For some reason the above line causes Chrome to jump back to the top of the page
        // if the user has not scrolled the page since it was last done. Work around this by
        // scrolling it back to the lightbox's 'home' position now
        $(window).scrollTop(affixOffsetTop);

        var jQueryInLightbox = function( selector, context ) {
            if(context){
                context = jQuery(context, '.pjax-wrapper');
                return new jQuery.fn.init(selector, context);
            }else{
                return new jQuery.fn.init(selector, '.pjax-wrapper');
            }
        };
        jQueryInLightbox.prototype = jQuery.prototype;
        jQuery.extend(jQueryInLightbox, jQuery);
        jQuery(function(){
            onDocumentReady(jQueryInLightbox, true);
            $(".page-wrapper").data('bs.affix').disable();
        });
    }

    History.Adapter.bind(window, 'statechange', function(){ // Note: We are using statechange instead of popstate

        var state = History.getState(); // Note: We are using History.getState() instead of event.state

        // do a normal page load if the browser has been resized to mobile layout
        if(window.disablePushState){
            location.reload();
            return;
        }

        // if a page with a lightbox was reloaded then we get a normal page,
        // so when the user hits the back button we can't just hide the lightbox (now there isn't any after the page reload)
        // but we need to go back to the previous page instead, i.e. reload the page with the now modified url
        if(!$('body.lightbox-view').length && !state.data.showLightbox){
            location.reload();
            return;
        }

        if(state.data.showLightbox){
            if(cache[state.url]){
                initLightbox();
                showLightbox(cache[state.url]);
            }else{
                initLightbox();
                $.ajax({
                    // use different url for ajax in order to avoid the browser caching the ajax response,
                    // and displaying it instead of the real page
                    url: state.url + "?pjax=1",
                    timeout: 5 * 1000,  // milliseconds
                    success: function(data, status, xhr){
                        var url = this.url.replace("?pjax=1", "");

                        // extractContainer is a local function exported from jquery.pjax.js
                        var obj = extractContainer(data, xhr, {
                            requestUrl: url,
                            fragment: ".page-content > .inner"
                        });

                        // if page called is unexpectedly invalid e.g the fragment selector above doesn't exist
                        // load the page normally
                        if(!obj.contents){
                            location.href = state.url;
                        }

                        // Cache for reuse later
                        cache[url] = obj;

                        // if the user concelled the request then don't show the lightbox now
                        if(!$('body.lightbox-view').length){
                            return;
                        }

                        showLightbox(obj);
                    },
                    error: function(){
                        // at this point the current url already points to the destination page
                        if(window.debug && window.console){
                            console.warn('RCA: There was an error loading the lightbox.');
                            console.warn('RCA: Reloading page...');
                        }
                        location.reload();
                    }
                });
            }
        }else{
            var affixed = $(".header-wrapper").hasClass("affix");

            // hide overlay
            $("body").removeClass("lightbox-view lightbox-visible");

            // re-enable bs-affix on .page-wrapper
            $(".page-wrapper").css({
                top: ""
            });
            $(".page-wrapper").data('bs.affix').enable();
            $(".page-wrapper").addClass("affix");

            // scroll back to the original position
            $(window).scrollTop(prevScrollY);

            if(scrollPostition() <= affixOffsetTop){
                $(".page-wrapper").removeClass("affix").addClass("affix-top");
            }
            $('.pjax-content').empty();
        }
    });

    function shouldOpenInLightbox(){
        var $this = $(this);
        var href = $this.attr('href');

        var returnFalseIfAnyIsTrue = [
            !href,
            href == '/',
            href && href.indexOf('#') != -1,
            href && href.indexOf('.') != -1,
            $this.closest('aside').length,
            $this.closest('.pjax-content').length,
            $this.closest('aside').length,
            !$this.closest('.page-wrapper').length
        ];

        for (var i = returnFalseIfAnyIsTrue.length - 1; i >= 0; i--) {
            if(returnFalseIfAnyIsTrue[i]){
                return false;
            }
        }

        // If we have an url with an expicitly defined protocol
        if(href.indexOf(':') != -1)
        // and if that's not on the current domain, or has a different protocol
        if(href.indexOf(location.protocol + '//' + location.hostname) == -1){
            // then don't open it in the lightbox.
            return false;
        }
        // Otherwise it might be opened in lightbox.

        var openInLightbox = !(new RegExp(window.neverOpenInLightbox[0]).test(href));
        if(openInLightbox)
            openInLightbox = !(new RegExp(window.neverOpenInLightbox[1]).test(href));


        return openInLightbox;
    }

    // $('a').each(function(){
    //     if(shouldOpenInLightbox.call(this)){
    //         $(this).addClass('lightbox-link');
    //         // TODO: this is for debugging only
    //         // $(this).css('text-decoration', 'line-through');
    //     }
    // });

    $(document).on('click', 'a', function(event) {
        var href = $(this).attr('href');
        var openInLightbox = shouldOpenInLightbox.call(this);

        if(openInLightbox){
            History.pushState({showLightbox: true}, $(this).text(), href);
            return false;
        }
    });

    $(document).on('click', '#pjax-close', function(event) {
        History.back();
    });

    $(document).on('keydown', 'body.lightbox-view', function(e){
        if(e.keyCode == 27){
            History.back();
        }
    });

    $('.page-overlay').on('click', function(){
        History.back();
    });
});
