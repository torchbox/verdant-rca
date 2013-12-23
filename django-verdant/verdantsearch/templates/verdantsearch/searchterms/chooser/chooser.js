function(modal) {
    function ajaxifyLinks (context) {
        $('.listing a', context).click(function() {
            modal.loadUrl(this.href);
            return false;
        });

        $('.pagination a', context).click(function() {
            var page = this.getAttribute("data-page");
            setPage(page);
            return false;
        });
    }

    var searchUrl = $('form.searchterms-search', modal.body).attr('action');
    function search() {
        $.ajax({
            url: searchUrl,
            data: {q: $('#id_q').val()},
            success: function(data, status) {
                $('#searchterms-results').html(data);
                ajaxifyLinks($('#searchterms-results'));
            }
        });
        return false;
    }
    function setPage(page) {

        if($('#id_q').val().length){
            dataObj = {q: $('#id_q').val(), p: page};
        }else{
            dataObj = {p: page};
        }

        $.ajax({
            url: searchUrl,
            data: dataObj,
            success: function(data, status) {
                $('#searchterms-results').html(data);
                ajaxifyLinks($('#searchterms-results'));
            }
        });
        return false;
    }

    ajaxifyLinks(modal.body);

    $('form.searchterms-search', modal.body).submit(search);

    $('a.choose-searchterms', modal.body).click(function() {
        modal.respond('searchtermsChosen', $(this).data());
        modal.close();

        return false;
    });

    $('#id_q').on('input', function() {
        clearTimeout($.data(this, 'timer'));
        var wait = setTimeout(search, 200);
        $(this).data('timer', wait);
    });
}
