$(function(){
	$('#filters .options li').click(function() {
		$('#listing').load(news_index, $('#filters').serialize());
		$(this).parent().closest('li').removeClass('expanded');
		return false;
	});
});