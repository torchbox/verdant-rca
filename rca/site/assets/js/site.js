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

