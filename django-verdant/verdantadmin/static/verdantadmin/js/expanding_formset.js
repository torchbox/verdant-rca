function buildExpandingFormset(prefix) {
    var addButton = $('#' + prefix + '-ADD');
    var formContainer = $('#' + prefix + '-FORMS');
    var totalFormsInput = $('#' + prefix + '-TOTAL_FORMS');
    var formCount = parseInt(totalFormsInput.val(), 10);

    var emptyFormTemplate = document.getElementById(prefix + '-EMPTY_FORM_TEMPLATE').innerText;

    addButton.click(function() {
        var newFormHtml = emptyFormTemplate.replace(/__prefix__/g, formCount);
        formContainer.append(newFormHtml);
        formCount++;
        totalFormsInput.val(formCount);
    });
}
