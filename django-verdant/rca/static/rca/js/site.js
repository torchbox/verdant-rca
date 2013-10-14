var breakpoints = {
    mobile: "screen and (max-width:768px)",
    desktopSmall: "screen and (min-width:768px)",
    desktopRegular: "screen and (min-width:1024px)",
    desktopLarge: "screen and (min-width:1280px)"
}

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
        $(this).prev().slideToggle();
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
        $(showElement).slideToggle();
    });
}

/* hide the search submit button then show
on typing text */
function showSearchSubmit() {
    $('form.search input[type="submit"]').hide();
    $('form.search input[type="text"]').focus(function() {
       $('form.search input[type="submit"]').show(); 
    });
    $('form.search input[type="text"]').focusout(function() {
       $('form.search input[type="submit"]').hide(); 
    });
}

/*google maps for contact page */
function initializeMaps() {
    var mapCanvas = document.getElementById('map_canvas_kensington');
    var mapOptions = {
        center: new google.maps.LatLng(51.501144, -0.179285),
        zoom: 16,
        mapTypeId: google.maps.MapTypeId.ROADMAP
    }
    var map = new google.maps.Map(mapCanvas, mapOptions);

    var mapCanvas2 = document.getElementById('map_canvas_battersea');
    var mapOptions2 = {
        center: new google.maps.LatLng(51.479167, -0.170076),
        zoom: 16,
        mapTypeId: google.maps.MapTypeId.ROADMAP
    }
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
    })

    var carousel = $this.bxSlider({
        adaptiveHeight: true,
        pager: function(){return $(this).hasClass('paginated')},
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
    })
}

$(function(){
    showSearchSubmit();
    showHideFooter();
    showHideSlide('.today h2', '.today', '.today ul');
    showHideSlide('.related h2', '.related', '.related .wrapper');
    showHide('.showmenu', 'nav');
    showHide('.showsearch', 'form.search');
    showHideDialogue();
    showHideSlide('.profile .continue', '.profile .remainder', '.profile .remainder');

    /* change text on show more button to 'hide' once it has been clicked */
    $('.profile .showmore').click(function(eventObject){
        if($(this).html() == 'hide'){
            $(this).html('show more');
        } else {
            $(this).html('hide');
        }
    });

    /* start any bxslider carousels not found within a tab  */
    $('.carousel:not(.tab-pane .carousel)').each(function(){
        applyCarousel($(this));
    })

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

    $('.tab-nav a, .tab-content .header a').click(function (e) {
        e.preventDefault()
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
    });

    /* mobile rejigging */
    Harvey.attach(breakpoints.mobile, {
        setup: function(){
            $('footer .social-wrapper').insertBefore('footer li.main:first'); //move social icons for mobile
            $('footer .smallprint ul').insertBefore('span.address'); //move smallprint for mobile
        }, 
        on: function(){
            $('footer .social-wrapper').insertBefore('footer li.main:first'); //move social icons for mobile
            $('footer .smallprint ul').insertBefore('span.address'); //move smallprint for mobile
        }, 
        off: function(){
            $('footer .social-wrapper').insertBefore('footer .smallprint'); //move social icons for mobile
            $('footer .smallprint ul').insertAfter('span.address'); //move smallprint for mobile
        }
    });

    // Things definitely only for desktop
    Harvey.attach(breakpoints.desktopSmall, {
        setup: function(){}, 
        on: function(){
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

    /* x-plus functionality */

    $('.x-plus').each(function(){
        var $this = $(this);
        var paginationContainer = $($this.data('pagination'));
        var loadmore = $('.load-more', $this);
        var loadmoreTarget = $('.load-more-target', $this);
        var itemContainer = $('.item-container', $this);
        var ul = $('> ul', itemContainer);
        var items = $('> li', ul);
        var step = 100

        // split list at the 'load-more-target' item.
        var loadmoreTargetIndex = items.index(loadmoreTarget);
        var loadmoreIndex = items.index(loadmore);
        var hidden = items.slice(loadmoreTargetIndex, loadmoreIndex).addClass('hidden fade-in-before');

        loadmore.click(function(e){
            e.preventDefault();
            
            if($this.data('pagination') && paginationContainer.length()){
                $('<div></div>').load($('.next a', paginationContainer).attr('href') + " .x-plus ul", function(){
                    loadmore.before($(this).find("li:not(.load-more)"));
                    expandToFit(false);
                });
            }else{
                expandToFit(true);
            }

            return false;
        });

        var expandToFit = function(animateHeight){
            if(!$this.hasClass('expanded')){
                $this.addClass('expanded');

                if(animateHeight){
                    itemContainer.css('height', itemContainer.height());
                    hidden.removeClass('hidden');
                    itemContainer.animate({height:ul.height()}, 300);
                }

                var time = 0;
                hidden.each(function(index){
                    var $this = $(this);
                    setTimeout( function(){ 
                        $this.addClass('fade-in-after');
                    }, time);
                    time += step;
                });
            }else{
                $this.removeClass('expanded');
                itemContainer.removeAttr('style');
                hidden.removeClass('fade-in-after').addClass('hidden');
            }
        }

    });
    
    /* Alters a UL of gallery items, so that each row's worth of iems are within their own UL, to avoid alignment issues */
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
        
        // Change items parent container to a div, to maintain validity
        if(items.parent().prop('tagName') == 'UL'){
            items.parent().replaceWith(function(){
                return $("<div />").append($(this).contents());
            });
        }

        for(i = 0; i < rowArray.length; i++){
            $(rowArray[i]).wrapAll('<ul class="newrow"></ul>');
        }
    }) 
    
    /* Search filters */
    $('.filters .label').click(function(){
        $(this).parent().toggleClass('expanded');
        $(this).parent().siblings().removeClass('expanded');
    });

    /* Google maps for contact page */
    //initializeMaps(); //leaving commented out for now - needs to be specific to contact page
});