
/* generic function to show / hide elements
 * the argument element will be assigned or unassigned an 'expanded' class.
 * The rest should be handled by the css. No sliding. */
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

/* show hide dialogue - has it's own funciton because of hide behaviour */
function showHideDialogue() {
    $('.share').click(function() {
         $('.dialogue').addClass('expanded');
         $('.dialogue').slideDown();
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

$(function(){
    showSearchSubmit();
    showHideFooter();
    showHideSlide('.today h2', '.today', '.today ul');
    showHideSlide('.related h2', '.related', '.related .wrapper');
    showHide('.showmenu', 'nav');
    showHide('.showsearch', 'form.search');
    showHideDialogue();

    /* start any bxslider carousels not found within a tab  */
    carousel = $('.carousel:not(.tab-pane .carousel)').bxSlider({
        pager: function(){return $(this).hasClass('paginated')}
    }); 

    /* tabs */
    $('.tab-nav a, .tab-content .header a').click(function (e) {
        e.preventDefault()
        $(this).tab('show');
        console.log('reloading slider');

        /* ensure carousels within tabs only execute once, on first viewing */
        if(!$(this).data('carousel')){
            var tabCarousel = $('.carousel', $($(this).attr('href'))).bxSlider({
                pager: function(){return $(this).hasClass('paginated')}
            });
            $(this).data('carousel', true)
        }
    });   

    /* mobile rejigging */
    Harvey.attach('screen and (max-width:768px)', {
        setup: function(){
            // called when the query becomes valid for the first time
            // WHY?: $('nav').insertAfter('.showMenu'); //move navigation into content for mobile version
            $('footer .social-wrapper').insertBefore('footer li.main:first'); //move social icons for mobile
            $('footer .smallprint ul').insertBefore('span.address'); //move smallprint for mobile
        }, 
        on: function(){
             // called each time the query is activated
            // WHY?: $('nav').insertAfter('.showMenu'); //move navigation into content for mobile version
            $('footer .social-wrapper').insertBefore('footer li.main:first'); //move social icons for mobile
            $('footer .smallprint ul').insertBefore('span.address'); //move smallprint for mobile
        }, 
        off: function(){
            // called each time the query is deactivated
            // WHY?: $('nav').insertBefore('.search-form'); //move navigation back to its proper place for desktop
            $('footer .social-wrapper').insertBefore('footer .smallprint'); //move social icons for mobile
            $('footer .smallprint ul').insertAfter('span.address'); //move smallprint for mobile
        }
    });

    // Things definitely only for desktop
    Harvey.attach('screen and (min-width:769px)', {
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
        var loadmore = $('.load-more', $this);
        var loadmoreTarget = $('.load-more-target', $this);
        var itemContainer = $('.item-container', $this);
        var ul = $('> ul', itemContainer);
        var items = $('> li', ul);
        var time = 0
        var step = 100

        // split list at the 'load-more-target' item.
        var loadmoreTargetIndex = items.index(loadmoreTarget);
        var loadmoreIndex = items.index(loadmore);
        var hidden = items.slice(loadmoreTargetIndex, loadmoreIndex).addClass('hidden fade-in-before');

        loadmore.click(function(){
            itemContainer.css('height', itemContainer.height());

            hidden.removeClass('hidden');

            $this.addClass('expanded');

            itemContainer.animate({height:ul.height()}, 300, function(){
                hidden.each(function(index){
                    var $this = $(this);
                    setTimeout( function(){ 
                        $this.addClass('fade-in-after');
                    }, time);
                    time += step;
                });
            });

            return false;
        });
    });
});