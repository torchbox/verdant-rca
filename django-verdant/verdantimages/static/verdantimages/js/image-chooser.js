function createImageChooser(id) {
    var chooserElement = $('#' + id + '-chooser');
    var previewImage = $('#' + id + '-previewimage');

    chooserElement.click(function() {
        ModalWorkflow();
    })
}
