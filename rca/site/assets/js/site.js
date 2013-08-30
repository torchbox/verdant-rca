
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


$(document).ready(function(){
	$('.bxslider').bxSlider({
		//auto: true,
  		//autoControls: true
  		pager: false
	}); /* start bxslider */
	showHide('li.main'); /* footer expand / collapse */
	showHide('.today');
	showHideWithSeparateClick('nav', '.showmenu');
	showHideWithSeparateClick('form.search', '.showsearch');
	showHideWithSeparateClick('.dialogue', '.share');

	/* mobile rejigging */
	Harvey.attach('screen and (max-width:599px)', {
		setup: function(){
			$('nav').insertAfter('.showMenu'); //move navigation into content for mobile version
		}, // called when the query becomes valid for the first time
		on: function(){
		}, // called each time the query is activated
		off: function(){
			$('nav').insertBefore('.search-form');
			//move navigation back to its proper place for desktop
		} // called each time the query is deactivated
	});

	//$('.bx-wrapper').addClass('bx-wrapper-fullscreen');
	//$('body').append('<div class="overlay">');  
	//$('.bx-wrapper').insertBefore('.header-wrapper');
});