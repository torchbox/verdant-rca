/* reloads a listing page based on filters selected */
/* requires an 'current_page' var to be set before this is called, on the template, to determine the index page to load */
$(function(){
	$('#filters .options li').click(function() {
		var prevActive = $("#filters").find("li.filter").find(".active");
		var showAll = !$(this).data("val");
		var showAllFor = $(this).parent().data("id");
		$('#listing').load(current_page, $('#filters').serialize(), function(){
			var $parent = $("#filters").find("li.filter").find("label[for=programme]").parent();
			if($("#filters").find("li.filter").find("label.active[for=school]").length){
				$parent.find("li[data-val]").hide();
				$.each(related_programmes, function(){
					$parent.find("li[data-val=" + this + "]").show();
				});
				if(!related_programmes.length){
					$parent.find("li[data-val!='']").hide();
				}
				$parent.find("li[data-val='']").show();
			}

			if(showAll){
				if(showAllFor == "programme"){
					$parent.find("li[data-val]").show();
				}
				if(showAllFor == "school"){
					$parent.find("li[data-val]").show();
				}
			}

			var visibleProgrammes = $parent.find("li").filter(function(){
				return $(this).css("display") != "none";
			}).length;
			if(visibleProgrammes < 8){
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
		$(this).parent().closest('li').removeClass('expanded');
		return false;
	});
});