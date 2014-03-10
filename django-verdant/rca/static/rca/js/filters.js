/* reloads a listing page based on filters selected */
/* requires an 'current_page' var to be set before this is called, on the template, to determine the index page to load */

$(function() {
    
    
    function updateFilters() {
        $('#listing').load(current_page, $('#filters').serialize(), function() {
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
            updateHashTags();
        });
    }
    
    function updateHashTags() {
        // Add non-empty filters to hashtag
        var serializedFilters = $('select', '#filters').filter(function() {
            return $(this).val()  ; 
        }).serialize();

        if (serializedFilters) {
            window.location.hash = '#/?' + serializedFilters;
        } else {
            // Remove the # symbol, copied from @Andy E's answer @
            // http://stackoverflow.com/questions/1397329/how-to-remove-the-hash-from-window-location-with-javascript-without-page-refresh
            var scrollV, scrollH, loc = window.location;
            if ("pushState" in history)
                history.pushState("", document.title, loc.pathname + loc.search);
            else {
                // Prevent scrolling by storing the page's current scroll offset
                scrollV = document.body.scrollTop;
                scrollH = document.body.scrollLeft;

                loc.hash = "";

                // Restore the scroll offset, should be flicker free
                document.body.scrollTop = scrollV;
                document.body.scrollLeft = scrollH;
            }
        }
    }
        
    updateFilters();
    

    $('#filters .options li').click(function() {
        
        updateFilters();
        
        
        $(this).parent().closest('li').removeClass('expanded');

        return false;
    });
});