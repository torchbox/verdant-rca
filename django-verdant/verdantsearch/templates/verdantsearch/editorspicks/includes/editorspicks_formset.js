{% with formset.extra_forms.0 as empty_form %}
    (function() {
        function fixPrefix(str) {return str;}

        var panel = InlinePanel({
            formsetPrefix: fixPrefix("id_{{ formset.prefix }}"),
            emptyChildFormPrefix: fixPrefix("{{ empty_form.prefix }}"),
            canOrder: true,

            onAdd: function(fixPrefix) {
                createPageChooser(fixPrefix('id_{{ formset.prefix }}-__prefix__-page'), 'core.page', null);
            }
        });

        {% for form in formset.initial_forms %}
            createPageChooser(fixPrefix('id_{{ formset.prefix }}-{{ forloop.counter0 }}-page'), 'core.page', null);
            panel.initChildControls('id_{{ formset.prefix }}-{{ forloop.counter0 }}');
        {% endfor %}

        panel.updateMoveButtonDisabledStates();
    })();
{% endwith %}