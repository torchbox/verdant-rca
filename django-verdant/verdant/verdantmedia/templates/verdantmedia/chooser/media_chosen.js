function(modal) {
    modal.respond('mediaChosen', '{{ media_html|safe }}');
    modal.close();
}