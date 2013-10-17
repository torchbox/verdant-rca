$(function(){
	$('#filters .options li').click(function() {
		$('#listing').load(current_research_page, $('#filters').serialize());
		$(this).parent().closest('li').removeClass('expanded');
		return false;
	});
});