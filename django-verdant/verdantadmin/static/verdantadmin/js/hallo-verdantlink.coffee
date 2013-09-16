# plugin for hallo.js to allow inserting links using Verdant's page chooser

(($) ->
    $.widget "IKS.halloverdantlink",
        options:
            uuid: ''
            editable: null

        populateToolbar: (toolbar) ->
            widget = this

            # Create an element for holding the button
            button = $('<span></span>')
            button.hallobutton
                uuid: @options.uuid
                editable: @options.editable
                label: 'Links'
                icon: 'icon-link'
                command: null

            # Append the button to toolbar
            toolbar.append button

            button.on "click", (event) ->
                lastSelection = widget.options.editable.getSelection()
                ModalWorkflow
                    url: '/admin/choose-page/core/page/' # TODO: don't hard-code this, as it may be changed in urls.py
                    responses:
                        pageChosen: (pageData) ->
                            a = document.createElement('a')
                            a.setAttribute('href', pageData.url)
                            a.setAttribute('data-id', pageData.id)

                            if (not lastSelection.collapsed) and lastSelection.canSurroundContents()
                                # use the selected content as the link text
                                lastSelection.surroundContents(a)
                            else
                                # no text is selected, so use the page title as link text
                                a.appendChild(document.createTextNode pageData.title)
                                lastSelection.insertNode(a)

                            widget.options.editable.element.trigger('change')

)(jQuery)
