{% for child in self.children %}
    {{ child.render_js }}
    initInlineChildDeleteButton(fixPrefix("inline_child_{{ child.form.prefix }}"), fixPrefix("{{ child.form.DELETE.id_for_label }}"));
{% endfor %}

buildExpandingFormset(fixPrefix("id_{{ self.formset.prefix }}"), {
    onAdd: function(prefix) {
        function fixPrefix(str) {
            return str.replace(/__prefix__/g, prefix);
        }

        {{ self.empty_child.render_js }}
        initInlineChildDeleteButton(fixPrefix("inline_child_{{ self.empty_child.form.prefix }}"), fixPrefix("{{ self.empty_child.form.DELETE.id_for_label }}"));
    }
});
