/* mini plugin to allow reversing an array see http://stackoverflow.com/questions/1394020/jquery-each-backwards */
jQuery.fn.reverse = [].reverse;

var breakpoints = {
    mobile: "screen and (max-width:767px)", /* NB: max-width must be 1px less than the min-width use for desktopSmall, below, otherwise both fire */
    mobileAndDesktopSmall: "screen and (max-width: 1023px)",
    desktopSmall: "screen and (min-width:768px)",
    desktopRegular: "screen and (min-width:1024px)",
    desktopLarge: "screen and (min-width:1280px)"
};

var expansionAnimationSpeed = 300;

// this value is used in pushstate.js as well
window.affixOffsetTop = 151;

// window.Affix is the internal class used by each bootsrap-affix instance
// it needs to made public in bootstrap-affix.js
window.Affix.prototype.disable = function(){
    if(this.$element.length){
        this._$element = this.$element;
        this.$element = $([]);
    }
};

window.Affix.prototype.enable = function(){
    if(this._$element){
        this.$element = this._$element;
    }
};

function onDocumentReady(jQuery, inLightBox){
    // By default we get an unmodified version of jQuery as the first argument
    // but in pushstate.js we pass a modified version of jQuery
    // that restricts it to work with elemnts in the lightbox only.
    // This way we can avoid initialising things behind the lightbox twice,
    // and we don't have to duplicate any code to run in the lightbox only.

    var $ = jQuery;

    /* Fluid video enhancement */
    fluidvids.init({
      selector: ['iframe'], // runs querySelectorAll()
      players: ['www.youtube.com', 'player.vimeo.com', 'cdn.embedly.com'] // players to support
    });

    /* generic function to show / hide elements
     * the argument element will be assigned or unassigned an 'expanded' class.
     * The rest should be handled by the css, including display:none or display:block No sliding. */
    function showHide(clickElement, classElement){
        $(clickElement).click(function(eventObject){
            $(classElement).toggleClass('expanded');
        });
    }

    /* show hide the footer - needs its own function because of being idiosyncratic */
    function showHideFooter() {
        $('footer .menu .main').click(function(eventObject){
            $(this).toggleClass('expanded');
            $('.submenu-block', this).slideToggle(expansionAnimationSpeed);
        });
        $('.submenu-block').click(function(e){
            e.stopPropagation();
        });
    }

    /* show hide dialogue - has its own funciton because of hide behaviour */
    function showHideDialogue() {
        $('.share').click(function() {
            if($('.dialogue').hasClass('expanded')) {
                $('.dialogue').removeClass('expanded');
                $('.dialogue').slideUp();
            } else {
                $('.dialogue').addClass('expanded');
                $('.dialogue').slideDown();
            }
        });
        $(document).click(function() {
            $('.dialogue').removeClass('expanded');
            $('.dialogue').slideUp();
        });
        $('.dialogue').click(function(e){
            e.stopPropagation();
        });
        $('.share').click(function(e){
            e.preventDefault();
            e.stopPropagation();
        });
    }

    /* generic function to show hide an element with slidey fun
    The classElement gets an expanded class, and the showElement gets hidden/shown
    with a slide */
    function showHideSlide(clickElement, classElement, showElement, openByDefault) {
        if(typeof openByDefault == "undefined"){
            openByDefault = true
        }

        if (!openByDefault){
            $(showElement).hide();
        }

        $(clickElement).click(function(eventObject){
            $(classElement).toggleClass('expanded');
            $(showElement).slideToggle(expansionAnimationSpeed);
            return false;
        });
    }

    /* hide the search submit button then show
    on typing text */
    function showSearchSubmit() {
        $('js-search-button').hide();
        $('js-search-input').focus(function() {
           $('js-search-button').show();
        });
        $(document).click(function() {
            $('js-search-button').hide();
        });
        $('js-search-input').click(function(e){
            e.stopPropagation();
        });
    }

    /* search autocomplete */
    function showSearchAutocomplete() {
        if(inLightBox){
            return;
        }
        $("input#search_box").autocomplete({
            source: function(request, response) {
                $.getJSON("/search/suggest/?q=" + request.term, function(data) {
                    response(data);
                });
            },
            select: function( event, ui ) {
                window.location.href = ui.item.search_url || ui.item.url;
            }
        }).data("ui-autocomplete")._renderItem = function( ul, item ) {
            return $( "<li></li>" ).data( "item.autocomplete", item ).append( "<a>" + item.title + "<span>" + (item.search_name || "") + "</span></a>" ).appendTo( ul );
        };
    }

    /*google maps for contact page
    Currently not being used but leaving commented out for reference - contains the correct lat and longs for Kensington and Battersea campuses */
    // function initializeMaps() {
    //     var mapCanvas = document.getElementById('map_canvas_kensington');
    //     var mapOptions = {
    //         center: new google.maps.LatLng(51.501144, -0.179285),
    //         zoom: 16,
    //         mapTypeId: google.maps.MapTypeId.ROADMAP
    //     };
    //     var map = new google.maps.Map(mapCanvas, mapOptions);

    //     var mapCanvas2 = document.getElementById('map_canvas_battersea');
    //     var mapOptions2 = {
    //         center: new google.maps.LatLng(51.479167, -0.170076),
    //         zoom: 16,
    //         mapTypeId: google.maps.MapTypeId.ROADMAP
    //     };
    //     var map2 = new google.maps.Map(mapCanvas2, mapOptions2);
    // }


    function applyCarousel(carouselSelector){
        var $this = $(carouselSelector);

        function calcHeight(){
            return $this.parent().width();
        }

        // on mobile the overlay text (or the caption if there is no overlay text) display below the image.
        // have to calculate the height and add it on to the max-height of the li and bx-viewpoort in the calculations to make sure it shows
        // correctly for portrait images
        function calcCaptionHeight(){
            var captionTextHeight = 0;
            $('.mobilecaption').each(function(){
                if ($(this).height() > captionTextHeight) {
                    captionTextHeight = $(this).height();
                }
            });
            return captionTextHeight;
        }

        $(window).resize(function(){
            $this.parent().css('max-height', calcHeight() + calcCaptionHeight());
            $('li', $this).css('max-height', calcHeight() + calcCaptionHeight());
            $('.portrait img', $this).css('max-height', calcHeight());
        });

        var carousel = $this.bxSlider({
            adaptiveHeight: true,
            pager: function(){ return $(this).hasClass('paginated'); },
            touchEnabled: ($('li', $this).length > 1) ? true: false,
            onSliderLoad: function(){
                $this.parent().css('max-height', calcHeight() + calcCaptionHeight());
                $('li', $this).css('max-height', calcHeight() + calcCaptionHeight());
                $('.portrait img', $this).css('max-height', calcHeight());
            },
            onSlideBefore: function($slideElement, oldIndex, newIndex){
                // find vimeos in old slide and stop them if playing
                $('.videoembed.vimeo iframe').each(function(idx, iframe) {
                    $f(iframe).api('pause');
                });
            }
        });

        return carousel;
    }

    showSearchSubmit();
    showSearchAutocomplete();
    showHideFooter();
    showHideSlide('.today h2', '.today', '.today ul', $('.today').hasClass('expanded'));
    showHideSlide('.related h2', '.related', '.related .wrapper');
    showHide('.js-showsearch', '.js-search');
    showHideDialogue();
    showHideSlide('.profile .showBiography', '.profile .biography', '.profile .biography');
    showHideSlide('.profile .showPractice', '.profile .practice', '.profile .practice');
    showHideSlide('.profile .showExternalCollaborations', '.profile .external-collaborations', '.profile .external-collaborations');
    showHideSlide('.profile .showPublications', '.profile .publications', '.profile .publications');
    showHideSlide('.showbody', '.hide-body', '.hide-body');
    showHideSlide('.contact-dropdown .contact-dropdown-header', '.contact-dropdown .contact-dropdown-header', '.contact-dropdown .dropdown', false);
    showHideSlide('.research-show-more', '.school-research-list', '.research-more', false);
    
    /* change text on show more button to 'hide' once it has been clicked */
    $('.profile .showmore').click(function(eventObject){
        if($(this).html() == 'hide'){
            $(this).html('show more');
        } else {
            $(this).html('hide');
        }
    });
    $('.type-standard-index .showmore').click(function(eventObject){
        if($(this).html() == 'hide'){
            $(this).html('read more');
        } else {
            $(this).html('hide');
        }
    });

    /* add focus to the search input when the mobile search button is clicked */
    $('.showsearch').click(function() {
        $('#search_box').focus();
    });


    /* tabs */
    //apply active class in correct place and add tab links
    $('.tab-nav li:first-child').addClass('active');
    $('.tab-pane').first().addClass('active');
    $('.tab-content .header a').first().addClass('active');
    $('.tab-nav li a').each(function(index){
        $(this).attr('href', "#tab" + (index+1));
    });
    $('.tab-pane').each(function(index){
        $(this).attr('id', "tab" + (index+1));
    });
    $('.tab-content .header a').each(function(index){
        $(this).attr('href', "#tab" + (index+1));
    });

    /* start any bxslider carousels not found within a tab  */
    $('.carousel:not(.tab-pane .carousel)').each(function(){
        applyCarousel($(this));
    });

    /* check if there's a carousel in the first tab and start it if so */
    /* also find the associated nav element and set carousel=true so it only executes once */
    $('.tab-content #tab1 .carousel').each(function(){
        applyCarousel($(this));
        $(this).closest('.tab-content').siblings('.tab-nav').find('a[href="#tab1"]').each(function(){
            $(this).data('carousel', true);
        });
    });

    $('.tab-nav a, .tab-content .header a').click(function (e) {
        e.preventDefault();

        /* This hides the tab on mobile phones if clicked a second time */
        if ($(this).hasClass('active')) {
            $('.tab-pane.active').toggleClass('hide_if_mobile');
        } else {
            // Save old tab position
            var oldY = $(this).offset().top;

            // Switch tabs
            $(this).tab('show');

            // Work out change in position and scroll by it
            var changeY = $(this).offset().top - oldY;
            window.scrollBy(0, changeY);

            // Remove hide_if_mobile class from all tab-panes that have it
            $('.tab-pane.hide_if_mobile').removeClass('hide_if_mobile');
        }

        /* ensure carousels within tabs only execute once, on first viewing */
        if(!$(this).data('carousel')){
            applyCarousel($('.carousel', $($(this).attr('href'))));
            $(this).data('carousel', true);
        }
    });

    /* Vimeo player API */
    $('.videoembed.vimeo').each(function() {
        var $this = $(this);
        var iframe = $('iframe', $this)[0];
        var player = $f(iframe);

        // Call the API when a button is pressed
        $('.playpause', $(this)).on('click', function() {
            player.api('play');
            $this.toggleClass('playing');
         });

        // Also start playback if poster image is clicked anywhere
        $('.poster', $(this)).click(function() {
            player.api('play');
            $this.toggleClass('playing');
        });
    });

    /* Tweet blocks */
    $('.twitter-feed-items').each(function(){
        var username = $.trim($(this).data('twitter-feed')).replace(/^@/,'');
        var link = '<a href="http://twitter.com/' + username + '">@' + username +'</a>';
        $(this).tweet({
            join_text: 'auto',
            username: username,
            avatar_size: 32,
            auto_join_text_default: 'from ' + link,
            loading_text: 'Checking for new tweets...',
            count: 3,
            template: '<div class="tweet-wrapper"><span class="twitter-icon"></span>{text} <span class="tweet-meta">{time} {join}</span></div>',
        });
    });

    /* Packery tweet blocks (behaves as several individual blocks) */
    $('.packery .tweet').each(function(){
        if(!window.packerytweets){
            var username = $.trim($(this).data('twitter-feed')).replace(/^@/,'');
            var count = $(this).data('twitter-count');

            var tmp = $('<div></div>');
            tmp.tweet({
                join_text: 'auto',
                username: username,
                avatar_size: 32,
                auto_join_text_default: 'from @' + username,
                loading_text: 'Checking for new tweets...',
                count: count
            });

            window.packerytweets = tmp;
        }
    });
    $(window.packerytweets).on('loaded', function(){
        var arr = $.makeArray($('li', window.packerytweets));
        $('.packery .tweet .inner .content').each(function(){
            $(this).html($(arr.shift()).html());
        });
    });

    /* mobile rejigging */
    Harvey.attach(breakpoints.mobile, {
        setup: function(){
            window.disablePushState = true;
            $('footer .social-wrapper').insertBefore('footer li.main:first'); //move social icons for mobile
            $('footer .smallprint ul').insertBefore('span.address'); //move smallprint for mobile
            $('aside .events-ads-wrapper').insertAfter('aside .related'); //events and ads move to bottom of sidebar in mobile
        },
        on: function(){
            $('footer .social-wrapper').insertBefore('footer li.main:first'); //move social icons for mobile
            $('footer .smallprint ul').insertBefore('span.address'); //move smallprint for mobile
            $('aside .events-ads-wrapper').insertAfter('aside .related'); //events and ads move to bottom of sidebar in mobile
        },
        off: function(){
            $('footer .social-wrapper').insertBefore('footer .smallprint'); //move social icons for mobile
            $('footer .smallprint ul').insertAfter('span.address'); //move smallprint for mobile
            $('aside .events-ads-wrapper').insertBefore('aside .related'); //events and ads moving to top of sidebar for desktop
        }
    });

    // Things definitely only for desktop
    Harvey.attach(breakpoints.desktopSmall, {
        setup: function(){},
        on: function(){
            /* Duplicate anything added to this function, into the ".lt-ie9" section below */

            /* Packery */
            $('.packery').imagesLoaded( function() {
                window.packery = $('.packery').packery({
                    itemSelector: '.item'
                });
            });
        },
        off: function(){
            $('.packery').packery('destroy');
        }
    });

    /* IE<9 targetted execution of above desktopSmall Harvey stuff, since media queries aren't understood */
    $('.lt-ie9').each(function(){
        /* Packery */
        $('.packery').imagesLoaded( function() {
            window.packery = $('.packery').packery({
                itemSelector: '.item'
            });
        });
    });

    /* x-plus functionality */

    $('.x-plus').each(function(){
        var $this = $(this);
        var paginationContainer = $this.data('pagination');
        var loadmore = $('.load-more', $this);
        var loadmoreTarget = $('.load-more-target', $this);
        var itemContainer = $('.item-container', $this);
        var ul = $('> ul', itemContainer);
        var items = $('> li', ul);
        var step = 100;
        var hiddenClasses = 'hidden fade-in-before';
        var contractedHeight = items.first().height();

        // split list at the 'load-more-target' item.
        var loadmoreTargetIndex = items.index(loadmoreTarget);
        var loadmoreIndex = items.index(loadmore);
        var newItems = items.slice(loadmoreTargetIndex, loadmoreIndex);

        var prepareNewItems = function(items){
            items.addClass(hiddenClasses);
        };

        var showNewItems = function(){
            itemContainer.css('height', itemContainer.height());
            newItems.removeClass('hidden');
            itemContainer.animate({height:ul.height()}, expansionAnimationSpeed, function(){
                itemContainer.removeAttr('style');
            });

            // Fade in each item one by one
            var time = 0;
            newItems.each(function(index){
                var $item = $(this);
                setTimeout( function(){
                    $item.addClass('fade-in-after');
                }, time);
                time += step;
            });
        };

        var hideNewItems = function(){
            $this.removeClass('expanded');
            itemContainer.animate({height:contractedHeight}, expansionAnimationSpeed, function(){
                itemContainer.removeAttr('style');
                newItems.addClass('hidden');
            });

            // Fade out each item one by one
            var time = 0;
            newItems.reverse().each(function(index){
                var $item = $(this);
                setTimeout( function(){
                    $item.removeClass('fade-in-after').addClass('fade-in-before');
                }, time);
                time += step;
            });
        };

        // prepare the items already in the page (if non-inifinite-scroll)
        prepareNewItems(items.slice(loadmoreTargetIndex, loadmoreIndex));

        // This click event can originate from the filtered results on an index page or any other paginated content.
        // If it is from a filter then we need to use event delegation but on other pages with multiple paginated
        // items this would result in a single event handler bound multiple times to the same container element.
        // So we have to use different containers to bind the event to: #listing for filters, and $this for everything else.
        var $bindTo = $this.closest("#listing").length ? $this.closest("#listing") : $this;

        $($bindTo).on("click", ".load-more", function(e){
            e.preventDefault();
            var loadmore = $(this);

            if(paginationContainer && $(paginationContainer).length){
                var nextLink = $('.next a', $(paginationContainer));
                var nextLinkUrl = nextLink.attr('href');

                // get next set of results
                var nextPage = $('<html></html>').load(nextLinkUrl, function(){
                    newItems = $('.x-plus .item-container > ul > li:not(.load-more)', nextPage);
                    prepareNewItems(newItems);
                    loadmore.before(newItems);
                    if(loadmore.hasClass('gallery-load-more')){
                        alignGallery();
                    }

                    // get next pagination link
                    if($(paginationContainer + ' .next a', nextPage).length){
                        nextLink.attr('href', $(paginationContainer + ' .next a', nextPage).attr('href'));
                    }else{
                        loadmore.remove();
                    }
                    showNewItems();

                });
            }else if(!$this.hasClass('expanded')){
                showNewItems();
                $this.addClass('expanded');
            }else{
                hideNewItems();
            }

            return false;
        });
    });

    $('.packery .load-more').each(function(){
        $this = $(this);
        $this.click(function(e){
            e.preventDefault();
            var tmp = $('<div></div>').load(current_page + " .item", "exclude=" + excludeIds, function(data){
                var items = $('.item', tmp);

                if (items.length){
                    $('.packery ul').append(items);
                    $('.packery').imagesLoaded( function() {
                        $('.packery').packery('appended', items);
                    });

                    //append ids returned to those already excluded
                    items.each(function(){
                        excludeIds.push($(this).data('id'))
                    })
                } else {
                    $this.fadeOut();
                }
            });
        });
    });

    /* Alters a UL of gallery items, so that each row's worth of iems are within their own UL, to avoid alignment issues */

    var alignGallery = function(){
        $('.gallery').each(function(){
            var maxWidth = $(this).width();
            var totalWidth = 0;
            var rowCounter = 0;
            var rowArray = [];
            var items = $('.item', $(this));

            function addToArray(elem){
                totalWidth += elem.width();
                if(typeof rowArray[rowCounter] == "undefined"){
                    rowArray[rowCounter] = [];
                }
                rowArray[rowCounter].push(elem.toArray()[0]); /* unclear why this bizarre toArray()[0] method is necessary. Can't find better alternative */
            }

            items.each(function(){
                if(totalWidth + $(this).width() >= maxWidth){
                    rowCounter ++;
                    totalWidth = 0;

                    addToArray($(this));
                }else{
                    addToArray($(this));
                }
            });


            // Remove any existing ul.newrow elements before rewrapping
            // Means we don't get lots of nested uls when clicking the load more button
            items.parent().each(function(){
                if($(this).prop('tagName') == 'UL' && $(this).hasClass('newrow')){
                    $(this).replaceWith(function(){
                        return $(this).contents();
                    });
                }
            });

            for(i = 0; i < rowArray.length; i++){
                $(rowArray[i]).wrapAll('<ul class="newrow"></ul>');
            }
        });
    };
    alignGallery();
    window.alignGallery = alignGallery; // this is used in filters.js too

	// Copied from @Yarin's answer in http://stackoverflow.com/questions/4197591/parsing-url-hash-fragment-identifier-with-javascript
	function getHashParams() {
		var hashParams = {};
		var e,
			a = /\+/g,  // Regex for replacing addition symbol with a space
			r = /([^&;=]+)=?([^&;]*)/g,
			d = function (s) { return decodeURIComponent(s.replace(a, " ")); },
			q = window.location.hash.substring('#/?'.length);

		while (e = r.exec(q))
		   hashParams[d(e[1])] = d(e[2]);

		return hashParams;
	}

    /* Search filters */
    $('.filters').each(function(){
        $self = $(this);

		function setLabel(option){
            $('label[for=' + $(option).parent().data('id') + ']', $self).html($(option).html()).addClass('active');
        }

        $('label', $self).click(function(){
            $(this).parent().toggleClass('expanded');
            $(this).parent().siblings().removeClass('expanded');
        });

        /* save original label val to data */
        $('label', $self).each(function(){
            $(this).data('original-label', $(this).html());
        });

        /* create popouts from existing select options */
        $('select', $self).each(function(){
            var options = $('option', $(this));
            var newOptions = '';
            var filterAttrs = 'data-id="' + $(this).attr('id') + '"';

			hashValue=getHashParams()[$(this).attr('name')];

            options.each(function(){
				var isSelected = "";
				if(hashValue == $(this).val() ) {
					isSelected ="selected";
					$(this).prop('selected', true);
				} else if (!hashValue) {
                    // TODO: Test this a  bit
                    isSelected=$(this).prop('selected')==true?"selected":"";
                }
                newOptions = newOptions + '<li data-val="' + ($(this).attr('value') ? $(this).val() : "") + '" class="'+ isSelected +'">' + $(this).html() + '</li>';
            });
            newOptions = newOptions + '</ul>';
            var thisOption = $('<div class="options" ' + filterAttrs + '><ul ' + filterAttrs + '>' + newOptions + '</div>');
            $(this).addClass('enhanced').after(thisOption);
        });

        /* if form already has items selected, replicate this */
        $('.options li', $self).each(function(){
            if($(this).hasClass('selected') && $(this).data('val')){
                setLabel($(this));
            }
        });

        /* Change label values when options are chosen */
        $('.options li', $self).on('click keydown', function(){
            $(this).siblings().removeClass('selected');
            $(this).addClass('selected');
            if($(this).data('val')){
                setLabel($(this));
            }else{
                $('label[for=' + $(this).parent().data('id') + ']', $self).each(function(){
                    $(this).html($(this).data('original-label')).removeClass('active');
                });
            }
            $('#' + $(this).parent().data('id')).val($(this).data('val'));
        });

        $(document).on('click', function(e){
            if(!$(e.target).parent().hasClass('filter')){
                $('label', $self).parent().removeClass('expanded');
            }
        });
    });

    /* Apply custom styles to selects */
    $('select:not(.filters select)').customSelect({
        customClass: "select"
    });

    /* Cookie notice */

    var displayCookieNotice = function(context, settings) {
      // Notice and message
      $('body').prepend('<div class="cookie-notice" style="display: block;"><div class="cookie-notice-content"><a id="cookie-notice-close" class="button" href="#">Dismiss</a><p class="cookie-notice-text bc4 body-text-style">We use cookies to help give you the best experience on our website. By continuing without changing your cookie settings, we assume you agree to this. Please read our <a href="/more/contact-us/about-this-website/privacy-cookies/">privacy policy</a> to find out more.</p></div></div>');

      // Close button
      $(document).delegate('#cookie-notice-close', 'click', function() {
        $(".cookie-notice").slideUp("slow");
        return false;
      });

      $(".cookie-notice").slideDown("slow");

      //set notice to never show again by default. Unnecessary to show every page load, particularly if we're suggesting showing it once is considered as acceptance.
      dontShowCookieNoticeAgain();
    };

    var dontShowCookieNoticeAgain = function() {
      // domainroot root variable is set in base.html - needed so the same cookie works across all subdomains

      // set or extend the cookie life for a year
      var exdate = new Date();
      exdate.setDate(exdate.getDate() + 365);
      document.cookie = "dontShowCookieNotice=" + "TRUE; expires=" + exdate.toUTCString() + ";domain=" + domainroot + ";path=/";
    };

    var pleaseShowCookieNotice = function() {
      // Don't show the notice if we have previously set a cookie to hide it
      var dontShowCookieNotice = (document.cookie.indexOf("dontShowCookieNotice") != -1) ? false : true;
      return dontShowCookieNotice;
    };

    $('body').once(function(){
      if (pleaseShowCookieNotice() == true) {
        displayCookieNotice();
      }
    });

    var enquiryForm = function() {

        var $trigger            = $( '.js-enquiry-form-trigger' ),
            $triggerButton      = $( '.enquiry-form-trigger' ),
            $triggerSidebar     = $( '.enquiry-form-trigger--sidebar' ),
            $triggerBody        = $( '.enquiry-form-trigger--body' ),
            $sidebar            = $( '.enquiry-form' ),
            $sidebarInner       = $( '.enquiry-form__inner' ),
            $bodyContent        = $( '.mobile-content-wrapper' ),
            $wrapper            = $( '.enquiry-trigger-wrapper' ),
            $background         = $('html');
            wrapperFixed        = 'enquiry-trigger-wrapper--fixed',
            showSidebar         = 'enquiry-form--show',
            shiftContent        = 'mobile-content-wrapper--shift-left',
            toggled             = 'enquiry-form-trigger--toggled',
            contentShifted      = 'mobile-content-wrapper--open',
            displayBuffer       = 10,
            state               = {
                open    : false,
                busy    : false,
                hasData : false
            },
            breakpoint          = {
                mobile  : 768
            };

        function selectPlaceholders() {

            $sidebar.find( 'select' ).each(function(){

                var $select          = $(this),
                    placeholderText  = $select.attr( 'placeholder' );

                // Add blank <option> as placeholder
                $select.prepend(
                    $( '<option>' , {
                        value    : '', 
                        text     : placeholderText, 
                        selected : true 
                    }
                ));

                // Add icon
                $select.parent().addClass( 'select-icon' );
            });

        }

        function open(){
            if( !state.busy ){
                state.busy = true;

                setTimeout(function(){
                    $sidebar.addClass( showSidebar );
                    $bodyContent.addClass( shiftContent );
                    $background.addClass(contentShifted);
                    $wrapper.addClass( wrapperFixed );
                    $triggerButton.addClass( toggled );
                    $('.enquiry-form-trigger').addClass('enquiry-form-trigger--fixed');
                    
                    // Show/hide triggers
                    if ( $(window).width() > breakpoint.mobile ) {
                        $triggerBody.hide();

                        setTimeout(function() {
                            $triggerSidebar.fadeIn();
                        }, 100);
                    }

                    state.open = true;
                    
                    if ( state.hasData ) {
                        state.busy = false;
                    }

                }, displayBuffer );

                if ( !state.hasData ) {
                    jQuery.ajax({
                        url: $sidebar.data('from-url'),
                        cache: false,
                        data: {
                            format: 'enquiry_form'
                        },
                        success: function(data) {
                            if (data.length) {
                                $sidebarInner.html(data);

                                // Modify placeholders
                                selectPlaceholders();

                                state.hasData = true;
                            }
                        },
                        complete: function() {
                            state.busy = false;
                        }
                    });
                }
            }
        }

        function close() {
            if( !state.busy ){
                state.busy = true;

                setTimeout(function(){
                    $sidebar.removeClass( showSidebar );
                    $bodyContent.removeClass( shiftContent );
                    $wrapper.removeClass( wrapperFixed );
                    $triggerButton.removeClass( toggled );
                    $('.enquiry-form-trigger').removeClass('enquiry-form-trigger--fixed');
                    //$background.removeClass( contentShifted);


                    // Show/hide triggers
                    if ( $(window).width() > breakpoint.mobile ) {
                        $triggerSidebar.hide();

                        setTimeout(function() {
                            $triggerBody.fadeIn();
                        }, 300);
                    }

                    state.open = false;
                    state.busy = false;
                }, displayBuffer );
            }
        }

        function toggle(){
            if( state.open ) {
                close();
            } else {
                open();
            }
        }

        function bindEvents(){
            $trigger.on( 'click', function(){
                toggle();
            });

            $bodyContent.on( 'click', function(){
                close();
            });
        }

        bindEvents();
    };

    enquiryForm();

    var contactUsForm = function() {

        var $trigger             = $( '.js-contact-us-form-trigger' ),
            $headerWrapper       = $( '.header-wrapper' ),
            $mobileContent       = $( '.body-text__mobile-contacts' ),
            $modalContent        = $( '.pjax-content' ),
            $modalWrapper        = $( '.page-wrapper' ),
            modalClose           = '.contact-us-form-modal #pjax-close',
            modalOverlay         = '.contact-us-form-modal .page-overlay',
            /*
            We need to add the no-pushstate class
            to temporary disable pushstate while our modal is opened.

            See event selectors for event handlers in pushstate.js
             */
            mobileContentClasses = 'body-text__mobile-contacts__dynamic-content',
            modalClasses         = 'lightbox-view lightbox-visible contact-us-form-modal no-pushstate',
            modalBodyKeydown     = 'body.contact-us-form-modal.lightbox-view',
            prevScrollY          = null,
            state                = {
                open     : false,
                busy     : false,
                useModal : true
            };

        function scrollPostition() {
            return +(window.scrollY || window.pageYOffset);
        }

        // We will use this function to display content on large screens
        function showModal(data) {
            $modalContent.html(data);
            $( 'body' ).addClass( modalClasses );

            prevScrollY = scrollPostition();

            // needed so that the browser can scroll back when closing the lightbox
            $( 'body, html' ).css('min-height', $(document).height());

            // disable bs-affix because it would interfer with positioning
            $modalWrapper.data('bs.affix').disable();
            $modalWrapper.removeClass('affix affix-top');

            var affixed = $headerWrapper.hasClass('affix');
            $modalWrapper.css({
                top: -scrollPostition() + (affixed ? 186 : 200)
            });

            // scroll to top, but leave the menu collapsed
            $(window).scrollTop(affixOffsetTop);
        }

        // We will use this function to display content on mobile devices
        function showOnPage(data) {
            var $innerElement = $('<div></div>');

            $innerElement.addClass(mobileContentClasses);
            $innerElement.html(data);

            $mobileContent.html($innerElement);

            $("html, body").animate({
                scrollTop: $mobileContent.show().offset().top
            }, 500);
        }

        function closeModal() {
            $( 'body' ).removeClass( modalClasses );
            $modalContent.html('');
        }

        function open(programme_contact) {
            if ( !state.busy ) {
                state.busy = true;

                // Requests current page
                jQuery.ajax({
                    cache: false,
                    data: {
                        programme_contact: programme_contact,
                        format: 'programme_contact_form'
                    },
                    success: function(data) {
                        if (data.length) {
                            if (state.useModal) {
                                showModal(data);
                            } else {
                                showOnPage(data);
                            }
                        }
                    },
                    complete: function() {
                        state.busy = false;
                    }
                });
            }
        }

        function bindEvents() {
            prevScrollY = scrollPostition();

            $trigger.on( 'change', function() {
                open(this.value);
            });

            $(document).on('click', modalClose, function(e) {
                closeModal();
            });

            $(document).on('keydown', modalBodyKeydown, function(e) {
                if (e.keyCode == 27) {

                    closeModal();
                }
            });

            $(document).on('click', modalOverlay, function(e) {
                closeModal();
            });

            Harvey.attach(breakpoints.mobile, {
                on: function() {
                    state.useModal = false;
                    closeModal();
                },
                off: function() {
                    state.useModal = true;
                    $mobileContent.html('');
                }
            });
        }

        bindEvents();
    };

    contactUsForm();

    // apply bold text (assumes just one set of asterisks to delimit bold text)
    $('.js-bold').each(function() {
        var text = $(this).text();
        var splitText = text.split(/[**]/);
        var boldedText = splitText[0] + '<b>' + splitText[1] + '</b>' + splitText[2];
        $(this).html(boldedText);
    });

    // Sticky header
    $(window).scroll(function(){
        var sticky = $('.js-sticky-header'),
            scroll = $(window).scrollTop();

        if (scroll > 0) sticky.addClass('fixed');
        else sticky.removeClass('fixed');
    });
}
