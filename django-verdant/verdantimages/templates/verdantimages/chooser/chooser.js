function(modal) {
    $('a.image-choice', modal.body).click(function() {
        modal.loadUrl(this.href);
        return false;
    });
}
