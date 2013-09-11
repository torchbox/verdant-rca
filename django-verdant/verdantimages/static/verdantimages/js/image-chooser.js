function createImageChooser(id) {
    var chooserElement = $('#' + id + '-chooser');
    var previewImage = $('#' + id + '-previewimage img');
    var input = $('#' + id);

    chooserElement.click(function() {
        ModalWorkflow({
            'url': '/admin/images/chooser/', /* TODO: don't hard-code this, as it may be changed in urls.py */
            'responses': {
                'imageChosen': function(imageData) {
                    input.val(imageData.id);
                    previewImage.attr({
                        'src': imageData.preview.url,
                        'width': imageData.preview.width,
                        'height': imageData.preview.height,
                        'alt': imageData.title
                    });
                }
            }
        });
    });
}
