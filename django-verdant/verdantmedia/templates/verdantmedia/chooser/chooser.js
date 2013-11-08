function(modal) {
    $('form.media-form', modal.body).submit(function() {
        var url = $('#id_url').val();

        modal.respond('mediaChosen', url);
        modal.close();

        return false;
    });
}
