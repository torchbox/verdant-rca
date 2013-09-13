/* generic function to show / hide elements
 * the argument element will be assigned or unassigned an 'expanded' class.
 * The rest should be handled by the css */
function showHide(element) {
    $(element).click(function(eventObject){
        $(this).toggleClass('expanded');
    });
}

/* based on function above but allowing the action to be triggered
on a different element to the element that has the expanded class applied */
function showHideWithSeparateClick(element, clickElement){
    $(clickElement).click(function(eventObject){
        $(element).toggleClass('expanded');
    });
}

function showHideParent(element) {
    $(element).click(function(eventObject){
        $(this).parent().toggleClass('expanded');
    });
}

function showHideDialogue() {
    showHideWithSeparateClick('.dialogue', '.share');
    $(document).click(function() {
        $('.dialogue').removeClass('expanded');
    });
    $('.dialogue').click(function(e){
        e.stopPropagation();
    });
    $('.share').click(function(e){
        e.preventDefault();
        e.stopPropagation();
    });
}

$(function(){

    showHideParent('.footer-expand'); /* footer expand / collapse */
    showHide('.today');
    showHide('.related');
    showHideWithSeparateClick('nav', '.showmenu');
    showHideWithSeparateClick('form.search', '.showsearch');
    showHideDialogue();

    /* start any bxslider carousels */
    carousel = $('.carousel').bxSlider({
        pager: function(){return $(this).hasClass('paginated')}
    }); 

    /* tabs */
    $('.tab-nav a, .tab-content .header a').click(function (e) {
        e.preventDefault()
        $(this).tab('show')
        carousel.reloadSlider();
    });   

    /* mobile rejigging */
    Harvey.attach('screen and (max-width:768px)', {
        setup: function(){
            // called when the query becomes valid for the first time
            // WHY?: $('nav').insertAfter('.showMenu'); //move navigation into content for mobile version
            $('footer li.main').removeClass('expanded'); // contract footer menu
            $('footer .social-wrapper').insertBefore('footer li.main:first'); //move social icons for mobile
            $('footer .smallprint ul').insertBefore('span.address'); //move smallprint for mobile
        }, 
        on: function(){
             // called each time the query is activated
            // WHY?: $('nav').insertAfter('.showMenu'); //move navigation into content for mobile version
            $('footer li.main').removeClass('expanded'); //contract footer menu
            $('footer .social-wrapper').insertBefore('footer li.main:first'); //move social icons for mobile
            $('footer .smallprint ul').insertBefore('span.address'); //move smallprint for mobile
        }, 
        off: function(){
            // called each time the query is deactivated
            // WHY?: $('nav').insertBefore('.search-form'); //move navigation back to its proper place for desktop
            $('footer li.main').addClass('expanded'); //expand footer menu
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


    /* X-plus functionality */
    $('.x-plus').each(function(){
        var $this = $(this);
        var number = $this.data('number');
        var loadmore = $('.load-more', $this);
        var loadmoreTarget = $('.load-more-target', $this);
        var items = $(' > ul > li', $this);
        console.log(items);

        // split list at the 'load-more-target' item.
        var loadmoreTargetIndex = items.index(loadmoreTarget);
        var loadmoreIndex = items.index(loadmore);
        var hidden = items.slice(loadmoreTargetIndex, loadmoreIndex).hide();

        loadmore.click(function(){

        });

    });
    
});