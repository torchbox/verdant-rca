
/* generic function to show / hide elements
 * the argument element will be assigned or unassigned an 'expanded' class.
 * The rest should be handled by the css */
function expand(element) {

}


$(document).ready(function(){
	$('li.main').click(function(eventObject){
		if($(this).hasClass('expanded')) {
			$(this).removeClass('expanded');
		} else {
			$(this).addClass('expanded');
		}
	});
});

