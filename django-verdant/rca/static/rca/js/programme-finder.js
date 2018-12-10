// Programme Finder
$(function() {
    $("input#course_search").autocomplete({
        minLength: 3,
        source: function(request, response) {
            $.getJSON("/programme_search/?q=" + request.term, function(data) {
                response(data);
            });
        },
        select: function( event, ui ) {
            window.location.href = ui.item.search_url || ui.item.url;
        }
    }).data("ui-autocomplete")._renderItem = function( ul, item ) {
        ul.addClass('hero-search__list');
        if (item.thumbnail.url) {
            // Render image when it's available
            return $( "<li class=\"hero-search__result\"></li>" )
                .data( "item.autocomplete", item )
                .append( "<a class=\"hero-search__link\">" + "<img class=\"hero-search__image\" src=\"" + item.thumbnail.url + "\">" + item.title + "</a>" )
                .appendTo( ul );
        } else {
            // When there's no image just render the title
            return $( "<li class=\"hero-search__result\"></li>" )
                .data( "item.autocomplete", item )
                .append( "<a class=\"hero-search__link\">" + item.title + "</a>" )
                .appendTo( ul );
        }
    };
});
