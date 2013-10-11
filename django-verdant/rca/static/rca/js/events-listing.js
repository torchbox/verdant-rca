$(function(){
	$('#programme-listing-filter').submit(function() {
		$('#listing').load("/events/", $(this).serialize());
		return false;
	})
});