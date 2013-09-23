function(modal) {
    $('a.document-choice', modal.body).click(function() {
        modal.loadUrl(this.href);
        return false;
    });
}
