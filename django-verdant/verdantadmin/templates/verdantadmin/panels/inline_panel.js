{% for admin in admins %}
    {{ admin.render_setup_js }}
{% endfor %}

buildExpandingFormset(fixPrefix("id_{{ formset.prefix }}"), {
    onAdd: function(prefix) {
        function fixPrefix(str) {
            return str.replace(/__prefix__/g, prefix);
        }

        {{ empty_form_admin.render_setup_js }}
    }
});
