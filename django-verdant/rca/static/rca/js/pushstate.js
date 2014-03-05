(function(){
    // TODO:
    // * bind click handlers to selected elements only

    var initialUrl = window.location.href;

    var affixOffsetTop = window.affixOffsetTop; // defined in site.js

    var prevScrollY = window.scrollY;

    var cache = {};

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

    function showLightbox(contents){
        
        $(".pjax-content").html(contents);

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

        // resize lightbox to fit contents:
        fixLightboxHeight();
        setTimeout(fixLightboxHeight, 1000);
    }

    History.Adapter.bind(window, 'statechange', function(){ // Note: We are using statechange instead of popstate

        var state = History.getState(); // Note: We are using History.getState() instead of event.state

        // We should use if(state.data.showLightbox) but the initial data can get mixed up
        // with the following ones after full page reloads, so we're not relying on that
        if(state.url != initialUrl){
            var contents = cache[state.url];
            if(contents){
                showLightbox(contents);
            }else{
                $.ajax({
                    // use different url for ajax in order to avoid the browser caching the ajax response,
                    // and displaying it instead of the real page
                    url: state.url + "?_ajax=1",
                    success: function(data, status, xhr){
                        var url = this.url.replace("?_ajax=1", "");
                        var obj = extractContainer(data, xhr, {
                            requestUrl: url,
                            fragment: ".page-content > .inner"
                        });
                        var contents = obj.contents;
                        cache[url] = contents;
                        showLightbox(contents);
                    }
                });
            }
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
            $(window).scrollTop(prevScrollY);

            if(window.scrollY <= affixOffsetTop){
                $(".page-wrapper").removeClass("affix").addClass("affix-top");
            }
        }
    });

    $(document).on('click', 'aside a', function(event) {
        History.pushState({showLightbox: true}, $(this).text(), $(this).attr("href"));
        return false;
    });


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
