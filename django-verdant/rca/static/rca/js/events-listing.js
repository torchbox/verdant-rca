$(function(){
	$('#filters .options li').click(function() {
		$('#listing').load(events_index, $('#filters').serialize());
		$(this).parent().closest('li').removeClass('expanded');
		return false;
	});
});