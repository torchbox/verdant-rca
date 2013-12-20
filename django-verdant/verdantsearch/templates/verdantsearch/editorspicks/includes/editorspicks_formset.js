{% with formset.extra_forms.0 as empty_form %}
    (function() {
        function fixPrefix(str) {return str;}

        var panel = InlinePanel({
            formsetPrefix: fixPrefix("id_{{ formset.prefix }}"),
            emptyChildFormPrefix: fixPrefix("{{ empty_form.prefix }}"),
            canOrder: true,

            onAdd: function(fixPrefix) {
                createPageChooser(fixPrefix('id_editors_picks-__prefix__-page'), 'core.Page', null);
            }
        });
        panel.updateMoveButtonDisabledStates();
    })();
{% endwith %}