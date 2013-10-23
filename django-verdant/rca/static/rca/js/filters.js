/* reloads a listing page based on filters selected */
/* requires an 'current_page' var to be set before this is called, on the template, to determine the index page to load */
$(function(){
	$('#filters .options li').click(function() {
		$('#listing').load(current_page, $('#filters').serialize());
		$(this).parent().closest('li').removeClass('expanded');
		return false;
	});
});