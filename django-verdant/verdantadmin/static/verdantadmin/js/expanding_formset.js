function buildExpandingFormset(prefix, opts) {
    if (!opts) {
        opts = {};
    }

    var addButton = $('#' + prefix + '-ADD');
    var formContainer = $('#' + prefix + '-FORMS');
    var totalFormsInput = $('#' + prefix + '-TOTAL_FORMS');
    var formCount = parseInt(totalFormsInput.val(), 10);

    var isOrderable = formContainer.hasClass('orderable');

    var emptyFormTemplate = document.getElementById(prefix + '-EMPTY_FORM_TEMPLATE').innerText;

    addButton.click(function() {
        var newFormHtml = emptyFormTemplate.replace(/__prefix__/g, formCount);
        formContainer.append(newFormHtml);
        if (isOrderable) {
            $('#' + prefix + '-' + formCount + '-ORDER').val(formCount);
        }

        if (opts.onAdd) {
            opts.onAdd(formCount);
        }

        formCount++;
        totalFormsInput.val(formCount);
    });
}
