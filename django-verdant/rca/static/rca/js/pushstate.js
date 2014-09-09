(function(){
    // TODO:
    // Add different base template for ajax requests:
    // {% extends request.is_ajax|yesno:"rca/base_ajax.html,rca/base.html" %}

    var initialUrl = window.location.href;

    var affixOffsetTop = window.affixOffsetTop; // defined in site.js

    var prevScrollY = window.scrollY;

    var cache = {};

    function initLightbox(){


        prevScrollY = window.scrollY;

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

        if(window.scrollY > affixOffsetTop){
            // scroll to top, but leave the menu collapsed
            $(window).scrollTop(affixOffsetTop);
        }
    }

    function showLightbox(contents){
        $(".pjax-content").html(contents);
        $("body").addClass('lightbox-visible');
    }

    History.Adapter.bind(window, 'statechange', function(){ // Note: We are using statechange instead of popstate

        var state = History.getState(); // Note: We are using History.getState() instead of event.state

        if(!$('body.lightbox-view').length && !state.data.showLightbox){
            location.href = state.url;
            return;
        }

        if(state.data.showLightbox){
            var contents = cache[state.url];
            if(contents){
                initLightbox();
                showLightbox(contents);
            }else{
                initLightbox();
                $.ajax({
                    // use different url for ajax in order to avoid the browser caching the ajax response,
                    // and displaying it instead of the real page
                    url: state.url + "?pjax=1",
                    success: function(data, status, xhr){
                        var url = this.url.replace("?pjax=1", "");
                        // extractContainer is a local function exported from jquery.pjax.js
                        var obj = extractContainer(data, xhr, {
                            requestUrl: url,
                            fragment: ".page-content > .inner"
                        });
                        var contents = obj.contents;
                        cache[url] = contents;
                        showLightbox(contents);

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
                        });
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

            if(window.scrollY <= affixOffsetTop){
                $(".page-wrapper").removeClass("affix").addClass("affix-top");
            }
        }
    });

    function shouldOpenInLightbox(){
        var $this = $(this);
        var href = $this.attr('href');

        var returnFalseIfAnyIsTrue = [
            !href,
            href == '/',
            href && href.indexOf('http') === 0,
            href && href.indexOf('#') != -1,
            href && href.indexOf('javascript:') != -1,
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

        var openInLightbox = !(new RegExp(window.neverOpenInLightbox[0]).test(href));
        if(openInLightbox)
            openInLightbox = !(new RegExp(window.neverOpenInLightbox[1]).test(href));


        return openInLightbox;
    }

    $('a').each(function(){
        if(shouldOpenInLightbox.call(this)){
            $(this).addClass('lightbox-link');
            // TODO: this is for debugging only
            // $(this).css('text-decoration', 'line-through');
        }
    });

    $(document).on('click', 'a', function(event) {
        var href = $(this).attr('href');
        var openInLightbox = shouldOpenInLightbox.call(this);

        if(openInLightbox){
            History.pushState({showLightbox: true}, $(this).text(), href);
            return false;
        }
    });

    $('.page-overlay').on('click', function(){
        History.back();
    });

    // TODO: the extra methods should be added on document ready, otherwise they throw exceptions in the pushstate code
    $(window).on("load", function(){
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

})();
