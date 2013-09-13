function(modal) {
    $('a.navigate-pages', modal.body).click(function() {
        modal.loadUrl(this.href);
        return false;
    });

    $('a.choose-page', modal.body).click(function() {
        modal.respond('pageChosen', $(this).data());
        modal.close();

        return false;
    });
}
