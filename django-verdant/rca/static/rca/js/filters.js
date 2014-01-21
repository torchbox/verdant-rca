/* reloads a listing page based on filters selected */
/* requires an 'current_page' var to be set before this is called, on the template, to determine the index page to load */

$(function(){

	function filterProgrammes() {
		$("#filters li.filter > label[for=programme]").each(function() {
			// If programme was automatically deselected, reset the filter
			if (!selected_programme) {
				$(this).removeClass('active');
				$(this).html("Programme"); // TODO: Find a better way to pull this value through
			}

			// Get parent (li.filter)
			var $parent = $(this).parent();

			// Hide all filter options
			$parent.find("li[data-val]").hide();

			// Show filter options in related_programmes
			$.each(related_programmes, function(){
				$parent.find("li[data-val=" + this + "]").show();
			});

			// Show the ALL filter option
			$parent.find("li[data-val='']").show();

			// Find number of programes that are visible
			var visibleProgrammes = $parent.find("li").filter(function(){
				return $(this).css("display") != "none";
			}).length;

			// Adjust number of columns to show 8 options per column
			if(visibleProgrammes <= 8){
				$("#filters div[data-id=programme]").css("width", "101%")
				.closest("li.filter.three-cols").removeClass("three-cols");
			}
			if(visibleProgrammes > 8){
				$("#filters div[data-id=programme]").css("width", "201%")
				.closest("li.filter.three-cols").removeClass("three-cols");
			}
			if(visibleProgrammes > 16){
				$("#filters div[data-id=programme]").css("width", "301%")
				.closest("li.filter").addClass("three-cols");
			}
		});
	}

	function filterSchools(){
		$("#filters li.filter > label[for=school]").each(function() {
			// If school was automatically deselected, reset the filter
			if (!selected_school) {
				$(this).removeClass('active');
				$(this).html("School"); // TODO: Find a better way to pull this value through
			}

			// Get parent (li.filter)
			var $parent = $(this).parent();

			// Hide all filter options
			$parent.find("li[data-val]").hide();

			// Show filter options in related_schools
			$.each(related_schools, function(){
				$parent.find("li[data-val=" + this + "]").show();
			});

			// Show the ALL filter option
			$parent.find("li[data-val='']").show();
		});
	}

	$('#filters .options li').click(function() {
		$('#listing').load(current_page, $('#filters').serialize(), function(){
			filterProgrammes();
			filterSchools();
			alignGallery(); // defined in site.js
		});
		$(this).parent().closest('li').removeClass('expanded');
		return false;
	});
});