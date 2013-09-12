function makeRichTextEditable(id) {
    var input = $('#' + id);
    var richText = $('<div class="richtext"></div>').html(input.val());
    richText.insertBefore(input);
    input.hide();
    richText.hallo({
        toolbar: 'halloToolbarFixed',
        plugins: {
            'halloformat': {},
            'halloheadings': {},
            'hallolists': {},
            'halloreundo': {},
            'halloverdantimage': {}
        }
    }).bind('hallomodified', function(event, data) {
        input.val(data.content);
    });
}
