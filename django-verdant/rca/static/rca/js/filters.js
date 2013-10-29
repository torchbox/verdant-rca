/* reloads a listing page based on filters selected */
/* requires an 'current_page' var to be set before this is called, on the template, to determine the index page to load */
$(function(){
	$('#filters .options li').click(function() {
		var prevActive = $("#filters").find("li.filter").find(".active");
		var showAll = !$(this).data("val");
		var showAllFor = $(this).parent().data("id");
		$('#listing').load(current_page, $('#filters').serialize(), function(){
			if($("#filters").find("li.filter").find("label.active[for=school]").length){
				$("#filters").find("li.filter").find("label[for=programme]").parent().find("li[data-val]").show();
				$.each(related_programmes, function(){
					$("#filters").find("li.filter").find("label[for=programme]").parent()
						.find("li[data-val!=" + this + "]").hide();
				});
				if(!related_programmes.length){
					$("#filters").find("li.filter").find("label[for=programme]").parent().find("li[data-val!='']").hide();
				}
				$("#filters").find("li.filter").find("label[for=programme]").parent().find("li[data-val='']").show();
			}

			if(showAllFor == "programme") if(showAll){
				$("#filters").find("li.filter").find("label[for=programme]").parent().find("li[data-val]").show();
			}

			var visibleProgrammes = $("#filters").find("li.filter").find("label[for=programme]").parent().find("li").filter(function(){
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