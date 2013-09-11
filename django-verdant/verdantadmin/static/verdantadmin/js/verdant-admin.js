function makeRichTextEditable(id) {
    var input = $('#' + id);
    var richText = $('<div class="richtext"></div>').html(input.val());
    richText.insertBefore(input);
    input.hide();
    richText.hallo({
        plugins: {
            'halloformat': {}
        }
    }).bind('hallomodified', function(event, data) {
        input.val(data.content);
    });
}
