function(modal) {
    $('.link-types a', modal.body).click(function() {
        modal.loadUrl(this.href);
        return false;
    });

    modal.ajaxifyForm($('.search-bar', modal.body));

    $('a.choose-page', modal.body).click(function() {
        var pageData = $(this).data();
        modal.respond('pageChosen', $(this).data());
        modal.close();

        return false;
    });
}
