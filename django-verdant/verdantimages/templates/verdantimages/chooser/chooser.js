function(modal) {
    function ajaxifyLinks (context) {
        $('a.image-choice', context).click(function() {
            modal.loadUrl(this.href);
            return false;
        });

        $('a.pagination_link', context).click(function() {
            var page = this.getAttribute("data-page");
            setPage(page);
            return false;
        });
    }

    var searchUrl = $('form.image-search', modal.body).attr('action');
    function search() {
        $.ajax({
            url: searchUrl,
            data: {q: $('#id_q').val()},
            success: function(data, status) {
                $('#image-results').html(data);
                ajaxifyLinks($('#image-results'));
            }
        });
        return false;
    }
    function setPage(page) {
        $.ajax({
            url: searchUrl,
            data: {q: $('#id_q').val(), p: page},
            success: function(data, status) {
                $('#image-results').html(data);
                ajaxifyLinks($('#image-results'));
            }
        });
        return false;
    }

    ajaxifyLinks(modal.body);

    $('form.image-upload', modal.body).submit(function() {
        var formdata = new FormData(this);

        $.ajax({
            url: this.action,
            data: formdata,
            processData: false,
            contentType: false,
            type: 'POST',
            dataType: 'text',
            success: function(response){
                modal.loadResponseText(response);
            }
        });

        return false;
    });

    $('form.image-search', modal.body).submit(search);

    $('#id_q').on('input', function() {
        clearTimeout($.data(this, 'timer'));
        var wait = setTimeout(search, 50);
        $(this).data('timer', wait);
    });
    $('a.suggested-tag').click(function() {
        $('#id_q').val($(this).text());
        search();
        return false;
    });

    {% url 'verdantadmin_tag_autocomplete' as autocomplete_url %}
    
    /* Add tag entry interface (with autocompletion) to the tag field of the image upload form */
    $('#id_tags', modal.body).tagit({
        autocomplete: {source: "{{ autocomplete_url|addslashes }}"}
    });
}
