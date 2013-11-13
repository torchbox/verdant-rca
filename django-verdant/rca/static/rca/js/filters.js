/* reloads a listing page based on filters selected */
/* requires an 'current_page' var to be set before this is called, on the template, to determine the index page to load */

$(function(){

	function applyFilters(school_or_year, showAll, showAllFor){
		var $parent = $("#filters").find("li.filter").find("label[for=programme]").parent();
		if($("#filters").find("li.filter").find("label.active[for=" + school_or_year + "]").length){
			$parent.find("li[data-val]").hide();
			$.each(related_programmes, function(){
				$parent.find("li[data-val=" + this + "]").show();
			});
			if(!related_programmes.length){
				$parent.find("li[data-val!='']").hide();
			}
			$parent.find("li[data-val='']").show();
		}

		if(showAll) if((showAllFor == "programme") || (showAllFor == school_or_year)){
			$parent.find("li[data-val]").show();
		}

		// adjust dropdown width / columns for programmes
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
		if(school_or_year == "degree_year"){
			filterSchools();
		}
	}

	function filterSchools(){
		var year = $("#degree_year").val();
		if(year){
			var schools = Object.keys(SCHOOL_PROGRAMME_MAP[year]);
		}
		$("#filters li.filter [data-id=school] li[data-val]").each(function(){
			var $this = $(this);
			if($this.data("val")){
				$this.hide();
			}
			if(year && schools.indexOf($this.data("val")) != -1){
				$this.show();
			}
			if(!year){
				$this.show();
			}
		});
	}

	$('#filters .options li').click(function() {
		var showAll = !$(this).data("val");
		var showAllFor = $(this).parent().data("id");
		$('#listing').load(current_page, $('#filters').serialize(), function(){
			$.each(["school", "degree_year"], function(){
				applyFilters(this, showAll, showAllFor);
			});
		});
		$(this).parent().closest('li').removeClass('expanded');
		return false;
	});

	// if there's a year selector than select the current one on page load
	var $yearLabel = $("#filters").find("li.filter").find("label[for=degree_year]");
	if($yearLabel.length){
		var year = "" + new Date().getFullYear();
		$yearLabel
			.text(year)
			.addClass("active")
			.next("select").val(year)
			.parent().find("li[data-val=" + year + "]").addClass("selected")
			.siblings().removeClass("selected");
		applyFilters("degree_year");
	}
});