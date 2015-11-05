/* reloads a listing page based on filters selected */
/* requires an 'current_page' var to be set before this is called, on the template, to determine the index page to load */

$(function() {


    function updateFilters() {
        $('#listing').load(current_page, $('#filters').serialize(), function() {
            // Make sure we have window.filter is specified. By default it will refer to the the element with id="filters" on the page.
            if(window.debug)
            if(filters.nodeType === 1){
                var warning = 'RCA: window.filter is not specified, instead it refers to the element with id="filters".' +
                    'Depending on the page type, you might need to call run_filters() from python and pass the resulting filterspecs to the template.';
                console.warn(warning);
            }

            // Run filters
            $(filters).each(function(idx, filter) {
                $('#filters li.filter > label[for=' + filter['name'] + ']').each(function() {
                    // Get parent (li.filter)
                    var $parent = $(this).parent();

                    // If filter was automatically deselected, reset the filter
                    if (!filter['current_value']) {
                        // Deactivate filter
                        $(this).removeClass('active');

                        // Reset filter label
                        $(this).html($(this).data('originalLabel'));

                        // Clear select box value
                        $parent.find('select').val(null);

                        // Set ALL filter option as the selected option
                        $parent.find('li[data-val].selected').removeClass('selected');
                        $parent.find('li[data-val=""]').addClass('selected');
                    }

                    // Hide all filter options
                    $parent.find('li[data-val]').hide();

                    // Show filter options in related_schools
                    $.each(filter['options'], function() {
                        $parent.find('li[data-val="' + this + '"]').show();
                    });

                    // Show the ALL filter option
                    $parent.find('li[data-val=""]').show();

                    // If the filter has 3 columns, sort into columns
                    if ($parent.hasClass('three-cols') || $parent.hasClass('three-cols-disabled')) {
                        // Get number of options that are visible
                        var visibleOptions = $parent.find('li').filter(function(){
                                return $(this).css('display') != 'none';
                        }).length;

                        // Adjust number of columns to show 8 options per column
                        if (visibleOptions <= 8) {
                            $('#filters div[data-id=' + filter['name'] + ']').css('width', '101%');
                            $parent.removeClass('three-cols').addClass('three-cols-disabled');
                        }
                        if (visibleOptions > 8) {
                            $('#filters div[data-id=' + filter['name'] + ']').css('width', '201%');
                            $parent.removeClass('three-cols').addClass('three-cols-disabled');
                        }
                        if (visibleOptions > 16) {
                            $('#filters div[data-id=' + filter['name'] + ']').css('width', '301%');
                            $parent.removeClass('three-cols-disabled').addClass('three-cols');
                        }
                    }
                });
            });

            alignGallery(); // Defined in site.js
            updateUrl();
        });
    }


	function updateUrl() {
        if(!history.replaceState){
            return;
        }

        var serializedFilters = $('select', '#filters').filter(function() {
            return $(this).val();
        }).serialize();

        if (serializedFilters) {
            history.replaceState("", document.title, location.pathname + '?' + serializedFilters);
        }
	}

	updateFilters();


    $('#filters .options li').click(function() {

        updateFilters();

        $(this).parent().closest('li').removeClass('expanded');

        return false;
    });
});
