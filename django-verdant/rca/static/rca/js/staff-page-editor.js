/**
 * This file contains scripts executed in the admin panel on StaffPage
 * editor that enable to have dependency on staff role and staff type.
 */
(function() {
    /**
     * Make sure staff type matches particular role fields.
     */
    $(document).ready(function() {
        // Make sure we are dealing with the editor of StaffPage,
        // otherwise do not execute.
        if (!$('body').hasClass('model-staffpage') && !$('body').hasClass('page-editor')) {
            return;
        }

        // Evaluate form values when it is first loaded
        evaluateStaffPageRoles();

        // Evaluate form when staff type changes.
        getStaffTypeElement().on('change', evaluateStaffPageRoles);

        // Evaluate form after a new inline row is addded.
        $('#id_roles-ADD').on('click', evaluateStaffPageRoles);

        // When form is submitted, empty unnecessary values.
        $('#page-edit-form').submit(submitStaffPageForm);
    });

    /**
     * Get staff type element.
     */
    function getStaffTypeElement() {
        return $('#id_staff_type');
    }

    /**
     * Get staff type currently selected in the form.
     */
    function getSelectedStaffType() {
        return getStaffTypeElement().val();
    }

    /**
     * Get forms number.
     */
    function getFormsNumber() {
        return $('#id_roles-TOTAL_FORMS').val() || 0;
    }

    /**
     * Get <input> DOM element for given field.
     * @param {Number} inlineId Row number of the inline form.
     * @param {String} fieldName Field name
     */
    function getFieldInputElement(inlineId, fieldName) {
        return $('#id_roles-' + inlineId + '-' + fieldName);
    }

    /**
     * Empty fields that are not for our staff type before submitting them
     * back to the server.
     */
    function submitStaffPageForm() {
        var staffType = getSelectedStaffType();

        for (var i = 0; i < getFormsNumber(); i++) {
            if (staffType === 'academic') {
                emptyFields(['location'], i);
            } else if (staffType === 'technical') {
                emptyFields(['school', 'programme', 'area'], i);
            } else if (staffType === 'administrative') {
                emptyFields(['school', 'programme', 'location'], i);
            }
        }
    }

    /**
     * Evaluate staff page role inline forms and change visibility of the fields
     * according to the staff type.
     */
    function evaluateStaffPageRoles() {
        for (var i = 0; i < getFormsNumber(); i++) {
            evaluateStaffPageRole(i);
        }
    }

    /**
     * Empty fields that are not for the chosen staff type.
     *
     * @param {Array} fieldNames Array of strings containing field names.
     * @param {Number} inlineId Row number of inline form.
     */
    function emptyFields(fieldNames, inlineId) {
        for (var i = 0; i < fieldNames.length; i++) {
            var field = getFieldInputElement(inlineId, fieldNames[i]);

            if (field) {
                field.val('');
            }
        }
    }

    /**
     * Evaluate inline form fields for staff roles for particular inline form
     * and toggle their visibility accordingly to the staff type.
     * @param {Number} inlineId
     */
    function evaluateStaffPageRole(inlineId) {
        var staffType = getSelectedStaffType();

        if (staffType === 'technical') {
            hideFields(['area', 'school', 'programme'], inlineId);
            showFields(['location'], inlineId);
        } else if (staffType === 'academic') {
            showFields(['area', 'school', 'programme'], inlineId);
            hideFields(['location'], inlineId);
        } else if (staffType === 'administrative') {
            showFields(['area'], inlineId);
            hideFields(['location', 'school', 'programme'], inlineId);
        } else {
            showFields(['area', 'location', 'school', 'programme'], inlineId);
        }
    }

    /**
     * Hide fields for given form inline.
     * @param {Array} fieldNames Array of strings containing field names to hide.
     * @param {Number} inlineId Inline form row number
     */
    function hideFields(fieldNames, inlineId) {
        toggleVisibilityOfFields(fieldNames, inlineId, 'hide');
    }

    /**
     * Show fields for given form inline.
     * @param {Array} fieldNames Array of strings containing fields names to show.
     * @param {Number} inlineId Row number of inline form.
     */
    function showFields(fieldNames, inlineId) {
        toggleVisibilityOfFields(fieldNames, inlineId, 'show');
    }

    /**
     * Toggle visibility of given fields for inline row.
     * @param {Array} fieldNames Array of strings with field names.
     * @param {Number} inlineId Row number of the form inline.
     * @param {String} showOrHide 'show' or 'hide', keep empty for toggling.
     */
    function toggleVisibilityOfFields(fieldNames, inlineId, showOrHide) {
        for (var i = 0; i < fieldNames.length; i++) {
            var field = getFieldInputElement(inlineId, fieldNames[i]);

            // If field exists, hide the first encountered parent <li> element.
            if (field) {
                var parentElement = field.parent();

                while(!parentElement.is('li')) {
                    parentElement = parentElement.parent();
                }

                if (showOrHide === 'show') {
                    parentElement.show();
                } else if (showOrHide === 'hide') {
                    parentElement.hide();
                } else {
                    parentElement.toggle();
                }
            }
        }
    }
})();
