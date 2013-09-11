/* generic function to show / hide elements
 * the argument element will be assigned or unassigned an 'expanded' class.
 * The rest should be handled by the css */
function showHide(element) {
    $(element).click(function(eventObject){
        if($(this).hasClass('expanded')) {
            $(this).removeClass('expanded');
        } else {
            $(this).addClass('expanded');
        }
    });
}

/* based on function above but allowing the action to be triggered
on a different element to the element that has the expanded class applied */
function showHideWithSeparateClick(element, clickElement){
    $(clickElement).click(function(eventObject){
        if($(element).hasClass('expanded')) {
            $(element).removeClass('expanded');
        } else {
            $(element).addClass('expanded');
        }
    });
}

function showHideParent(element) {
    $(element).click(function(eventObject){
        if($(this).parent().hasClass('expanded')) {
            $(this).parent().removeClass('expanded');
        } else {
            $(this).parent().addClass('expanded');
        }
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
    carousel = $('.bxslider').bxSlider({
        //auto: true,
        //autoControls: true
        pager: false
    }); /* start bxslider */

    showHideParent('.footer-expand'); /* footer expand / collapse */
    showHide('.today');
    showHide('.related');
    showHideWithSeparateClick('nav', '.showmenu');
    showHideWithSeparateClick('form.search', '.showsearch');
    showHideDialogue();

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

    /* tabs */
    $('.tab-nav a, .tab-content .header a').click(function (e) {
        e.preventDefault()
        $(this).tab('show')
        carousel.reloadSlider();
    })
});