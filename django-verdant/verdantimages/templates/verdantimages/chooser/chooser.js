function(modal) {
    $('a.image-choice', modal.body).click(function() {
        modal.loadUrl(this.href);
        return false;
    });

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

    $('#id_q').keyup(function() {
        clearTimeout($.data(this, 'timer'));
        var wait = setTimeout(search, 10);
        $(this).data('timer', wait);
    });

    function search () {
        $.ajax({
            url: "{%url 'verdantimages_chooser' %}",
            data: {q: "" + $('#id_q').val() + ""},
            success: function(data, status) {
                $('#image-results').html(data);
            }
        });
        return false;
    };

    {% url 'verdantadmin_tag_autocomplete' as autocomplete_url %}
    $('#id_tags', modal.body).tagit({
        autocomplete: {source: "{{ autocomplete_url|addslashes }}"}
    });
}
