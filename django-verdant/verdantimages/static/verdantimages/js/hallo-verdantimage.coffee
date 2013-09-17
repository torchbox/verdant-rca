# plugin for hallo.js to allow inserting images from the Verdant image library

(($) ->
    $.widget "IKS.halloverdantimage",
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
                label: 'Images'
                icon: 'icon-picture'
                command: null

            # Append the button to toolbar
            toolbar.append button

            button.on "click", (event) ->
                lastSelection = widget.options.editable.getSelection()
                ModalWorkflow
                    url: '/admin/images/chooser/?select_format=true' # TODO: don't hard-code this, as it may be changed in urls.py
                    responses:
                        imageChosen: (imageData) ->
                            img = document.createElement('img')
                            img.setAttribute('src', imageData.preview.url)
                            img.setAttribute('width', imageData.preview.width)
                            img.setAttribute('height', imageData.preview.height)
                            img.setAttribute('alt', imageData.alt)
                            img.setAttribute('data-id', imageData.id)
                            img.setAttribute('data-format', imageData.format)
                            lastSelection.deleteContents()
                            lastSelection.insertNode(img)
                            widget.options.editable.element.trigger('change')

)(jQuery)
