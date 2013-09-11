function createImageChooser(id) {
    var chooserElement = $('#' + id + '-chooser');
    var previewImage = $('#' + id + '-previewimage');

    chooserElement.click(function() {
        ModalWorkflow({
            'url': '/admin/images/chooser/' /* TODO: don't hard-code this, as it may be changed in urls.py */
        });
    });
}
