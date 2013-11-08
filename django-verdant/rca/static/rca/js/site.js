/* mini plugin to allow reversing an array see http://stackoverflow.com/questions/1394020/jquery-each-backwards */
jQuery.fn.reverse = [].reverse;

var breakpoints = {
    mobile: "screen and (max-width:768px)",
    desktopSmall: "screen and (min-width:768px)",
    desktopRegular: "screen and (min-width:1024px)",
    desktopLarge: "screen and (min-width:1280px)"
};

var expansionAnimationSpeed = 300;


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
    $('.footer-expand').click(function(eventObject){
        $(this).parent().toggleClass('expanded');
        $(this).prev().slideToggle(expansionAnimationSpeed);
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
function showHideSlide(clickElement, classElement, showElement) {
    $(clickElement).click(function(eventObject){
        $(classElement).toggleClass('expanded');
        $(showElement).slideToggle(expansionAnimationSpeed);
    });
}

/* hide the search submit button then show
on typing text */
function showSearchSubmit() {
    $('form.search input[type="submit"]').hide();
    $('form.search input[type="text"]').focus(function() {
       $('form.search input[type="submit"]').show();
    });
    $(document).click(function() {
        $('form.search input[type="submit"]').hide();
    });
    $('form.search input[type="text"]').click(function(e){
        e.stopPropagation();
    });
}

/* search autocomplete */
function showSearchAutocomplete() {
    $("input#search_box").autocomplete({
        source: function(request, response) {
            $.getJSON("/search/suggest/?q=" + request.term, function(data) {
                response(data);
            })
        },
        select: function( event, ui ) {
            window.location.href = ui.item.url;
        }
    });
}

/*google maps for contact page */
function initializeMaps() {
    var mapCanvas = document.getElementById('map_canvas_kensington');
    var mapOptions = {
        center: new google.maps.LatLng(51.501144, -0.179285),
        zoom: 16,
        mapTypeId: google.maps.MapTypeId.ROADMAP
    };
    var map = new google.maps.Map(mapCanvas, mapOptions);

    var mapCanvas2 = document.getElementById('map_canvas_battersea');
    var mapOptions2 = {
        center: new google.maps.LatLng(51.479167, -0.170076),
        zoom: 16,
        mapTypeId: google.maps.MapTypeId.ROADMAP
    };
    var map2 = new google.maps.Map(mapCanvas2, mapOptions2);
}


function applyCarousel(carouselSelector){
    var $this = $(carouselSelector);

    function calcHeight(){
        return $this.parent().width();
    }

    $(window).resize(function(){
        $this.parent().css('max-height', calcHeight());
        $('li', $this).css('max-height', calcHeight());
        $('.portrait img', $this).css('max-height', calcHeight());
    });

    var carousel = $this.bxSlider({
        adaptiveHeight: true,
        pager: function(){ return $(this).hasClass('paginated'); },
        onSliderLoad: function(){
            $this.parent().css('max-height', calcHeight());
            $('li', $this).css('max-height', calcHeight());
            $('.portrait img', $this).css('max-height', calcHeight());
        },
        onSlideBefore: function($slideElement, oldIndex, newIndex){
            // find vimeos in old slide and stop them if playing
            post($('.videoembed.vimeo iframe'), 'pause');
        }
    });

    return carousel;
}

// Helper function for sending a message to the player
function post(frame, action, value) {
    $(frame).each(function(){
        var url = $(this).attr('src').split('?')[0];
        var data = { method: action };

        if (value) {
            data.value = value;
        }

        $(this)[0].contentWindow.postMessage(JSON.stringify(data), url);
    });
}

$(function(){
    showSearchSubmit();
    showSearchAutocomplete();
    showHideFooter();
    showHideSlide('.today h2', '.today', '.today ul');
    showHideSlide('.related h2', '.related', '.related .wrapper');
    showHide('.showmenu', 'nav');
    showHide('.showsearch', 'form.search');
    showHideDialogue();
    showHideSlide('.profile .showBiography', '.profile .biography', '.profile .biography');
    showHideSlide('.profile .showPractice', '.profile .practice', '.profile .practice');
    /* change text on show more button to 'hide' once it has been clicked */
    $('.profile .showmore').click(function(eventObject){
        if($(this).html() == 'hide'){
            $(this).html('show more');
        } else {
            $(this).html('hide');
        }
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
        $(this).tab('show');

        /* ensure carousels within tabs only execute once, on first viewing */
        if(!$(this).data('carousel')){
            applyCarousel($('.carousel', $($(this).attr('href'))));
            $(this).data('carousel', true);
        }
    });

    /* Vimeo player API */
    $('.videoembed.vimeo').each(function(){
        var $this = $(this);
        var f = $('iframe', $(this));

        // Listen for messages from the player
        if (window.addEventListener){
            window.addEventListener('message', onMessageReceived, false);
        }
        else {
            window.attachEvent('onmessage', onMessageReceived, false);
        }

        // Handle messages received from the player
        function onMessageReceived(e) {
            var data = JSON.parse(e.data);

            switch (data.event) {
                case 'ready':
                    post(f, 'addEventListener', 'pause');
                    post(f, 'addEventListener', 'finish');
                    break;

                case 'pause':
                    //nothing
                    break;

                case 'finish':
                    //nothing
                    break;
            }
        }

        // Call the API when a button is pressed
        $('.playpause', $(this)).on('click', function() {
             post(f, 'play');
             $this.toggleClass('playing');
         });

        //also start playback if poster image is clicked anywhere
        $('.poster').click(function(){
            post(f, 'play');
            $this.toggleClass('playing');
        });
    });

    /* Tweet blocks */
    $('.twitter-feed-items').each(function(){
        var username = $(this).data('twitter-feed');
        $(this).tweet({
            join_text: 'auto',
            username: username,
            avatar_size: 32,
            auto_join_text_default: 'from @' + username,
            loading_text: 'Checking for new tweets...',
            count: 3
        });
    });

    /* Packery tweet blocks (behaves as several individual blocks) */
    $('.packery .tweet').each(function(){
        if(!window.packerytweets){
            var username = $(this).data('twitter-feed');
            var count = $(this).data('twitter-count');

            var tmp = $('<div></div>');
            tmp.tweet({
                join_text: 'auto',
                username: username,
                avatar_size: 32,
                auto_join_text_default: 'from @' + username,
                loading_text: 'Checking for new tweets...',
                count: count
            })

            window.packerytweets = tmp;
        }
    });
    $(window.packerytweets).on('loaded', function(){
        var arr = jQuery.makeArray($('li', window.packerytweets));
        $('.packery .tweet .inner').each(function(){
            $(this).html($(arr.pop()).html());
        });
    })

    /* mobile rejigging */
    Harvey.attach(breakpoints.mobile, {
        setup: function(){
            $('footer .social-wrapper').insertBefore('footer li.main:first'); //move social icons for mobile
            $('footer .smallprint ul').insertBefore('span.address'); //move smallprint for mobile
            $('aside').appendTo('.mobile-menu-wrapper'); //move sidebar for mobile
            $('aside .events-ads-wrapper').insertAfter('aside .related'); //events and ads move to bottom of sidebar in mobile
        },
        on: function(){
            $('footer .social-wrapper').insertBefore('footer li.main:first'); //move social icons for mobile
            $('footer .smallprint ul').insertBefore('span.address'); //move smallprint for mobile
            $('aside').appendTo('.mobile-menu-wrapper'); //move sidebar for mobile
            $('aside .events-ads-wrapper').insertAfter('aside .related'); //events and ads move to bottom of sidebar in mobile
        },
        off: function(){
            $('footer .social-wrapper').insertBefore('footer .smallprint'); //move social icons for mobile
            $('footer .smallprint ul').insertAfter('span.address'); //move smallprint for mobile
            $('aside').insertAfter('.page-content'); //move sidebar for mobile
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
                var packery = $('.packery').packery({
                    itemSelector: '.item',
                    stamp: ".stamp"
                });
            });
        },
        off: function(){
            $('.packery').destroy();
        }
    });

    /* IE<9 targetted execution of above desktopSmall Harvey stuff, since media queries aren't understood */
    $('.lt-ie9').each(function(){
        /* Packery */
        $('.packery').imagesLoaded( function() {
            var packery = $('.packery').packery({
                itemSelector: '.item',
                stamp: ".stamp"
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
        }

        // prepare the items already in the page (if non-inifinite-scroll)
        prepareNewItems(items.slice(loadmoreTargetIndex, loadmoreIndex));

        loadmore.click(function(e){
            e.preventDefault();

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
                    rowArray[rowCounter] = new Array();
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
            options.each(function(){
                newOptions = newOptions + '<li data-val="' + ($(this).attr('value') ? $(this).val() : "") + '" class="'+ ($(this).prop('selected') ? "selected":"") +'">' + $(this).html() + '</li>';
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

    /* Google maps for contact page */
    //initializeMaps(); //leaving commented out for now - needs to be specific to contact page

    /* Apply custom styles to selects */
    $('select:not(.filters select)').customSelect({
        customClass: "select"
    });
});