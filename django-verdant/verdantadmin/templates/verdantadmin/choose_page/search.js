function(modal) {
    $('.link-types a', modal.body).click(function() {
        modal.loadUrl(this.href);
        return false;
    });

    {% include 'verdantadmin/choose_page/_search_behaviour.js' %}
    ajaxifySearchResults();
}
