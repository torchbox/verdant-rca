/* reloads a listing page based on filters selected */
/* requires an 'current_page' var to be set before this is called, on the template, to determine the index page to load */

$(function() {
    $('#filters .options li').click(function() {
        $('#listing').load(current_page, $('#filters').serialize(), function() {
            // Run filters
            $(filters).each(function(idx, filter) {
                $('#filters li.filter > label[for=' + filter['name'] + ']').each(function() {
                    // If filter was automatically deselected, reset the filter
                    if (!filter['current_value']) {
                        $(this).removeClass('active');
                        $(this).html(filter['name']); // TODO: Find a better way to pull this value through
                    }

                    // Get parent (li.filter)
                    var $parent = $(this).parent();

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
        });

        $(this).parent().closest('li').removeClass('expanded');

        return false;
    });
});