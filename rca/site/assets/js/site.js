
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


$(document).ready(function(){
	showHide('li.main'); /* footer expand / collapse */
	showHide('.today');
});