{% for panel in admin.panels %}
    {{ panel.render_js|safe }}
{% endfor %}

{% if admin.can_delete %}
    $(fixPrefix('#{{ admin.form.DELETE.id_for_label }}-button')).click(function() {
        /* set 'deleted' form field to true */
        $(fixPrefix('#{{ admin.form.DELETE.id_for_label }}')).val('1');
        $(fixPrefix('#admin_{{ admin.prefix }}')).fadeOut();
    });
{% endif %}
