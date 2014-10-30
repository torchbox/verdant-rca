// JAVASCRIPT HELPERS FOR BLACKBAUD FORMS
$(function() {
    // Grouping of fields
    function groupSetOfFields(fieldSelectors) {
        $(fieldSelectors).wrapAll('<div class="grouped-form-items"></div>');
    }

    //Remove the JS added Blackbaud CSS when loaded. 
    var el = 'link[href^="https://bbox.blackbaudhosting.com/webforms"]';

    var blackbaudElementCheckInterval = setInterval(function(){
        //Run once form has loaded
        if ($('#mongo-form').length) {
            clearInterval(blackbaudElementCheckInterval);

            //remove the stylesheet found
            $(el).remove();

            //Shows the form smoothly
            $('#bbox-root #mongo-form').css({opacity: 0, visibility: "visible"}).animate({opacity: 1.0}, 340, function() {
                $(this).addClass("form-visible");
            }); //Smooth intro for the form.
            

            // FORM HELPERS for Donations

            $('#bboxdonation_payment_cboCardType option:eq(0)').text('Please select')

            // If other amount label selected show the other amount input
            $('.BBFormRadioLabelGivingLevelOther').on('click', function() {
                $('#bboxdonation_gift_fldOtherLevelAmount').show(200);
            });

            // Click was on an actual amount so hide the 'other' amount input box
            $('.BBFormRadioLabelGivingLevel:not(.BBFormRadioLabelGivingLevelOther)').on('click', function() {
                $('#bboxdonation_gift_fldOtherLevelAmount').hide(250);
            });  

            $('.BBFormSelectList').customSelect({customClass:'select'}).change(function(){
                $('.hasCustomSelect').removeClass('hasCustomSelect').removeAttr('style');
                $('.select').remove();
                $('.BBFormSelectList').customSelect({customClass:'select'});
            });            

            // FORM IMPROVEMENTS
            // Blackbaud markup isn't great so we're boosting the experience. 

            // Add currenty to the 'other amount box'
            $('#bboxdonation_gift_txtOtherAmountButtons').before('<span class="currency-symbol">&pound;</span>');                  
            
            // Move the name label next to it's input field.
            var firstNameLabel = $('#bboxdonation_billing_lblFullName').clone();
            $('#bboxdonation_billing_lblFirstName, #bboxdonation_billing_lblFullName').remove();
            $('#bboxdonation_billing_txtFirstName').before(firstNameLabel);

            // GROUPS OF FIELDS

            // firstname 
            groupSetOfFields('#bboxdonation_billing_lblFullName, #bboxdonation_billing_txtFirstName');
            
            // lastname
            groupSetOfFields('#bboxdonation_billing_lblLastName, #bboxdonation_billing_txtLastName');

            //Group the above groups 
            groupSetOfFields('#divName .grouped-form-items');

            // CA province
            groupSetOfFields('#bboxdonation_billing_billingAddress_lblCAProvince, #bboxdonation_billing_billingAddress_ddCAProvince, #bboxdonation_billing_billingAddress_ddCAProvince + .select');

            // CA postcode
            groupSetOfFields('#bboxdonation_billing_billingAddress_lblCAPostCode, #bboxdonation_billing_billingAddress_txtCAPostCode');

            // USA state
            groupSetOfFields('#bboxdonation_billing_billingAddress_lblState , #bboxdonation_billing_billingAddress_ddState, #bboxdonation_billing_billingAddress_ddState + .select');
           
            // USA zip
            groupSetOfFields('#bboxdonation_billing_billingAddress_lblZip, #bboxdonation_billing_billingAddress_txtZip');

            // NZ city
            groupSetOfFields('#bboxdonation_billing_billingAddress_lblNZCity, #bboxdonation_billing_billingAddress_ddNZCity, #bboxdonation_billing_billingAddress_ddNZCity + .select');

            // NZ postcode
            groupSetOfFields('#bboxdonation_billing_billingAddress_lblNZPostCode, #bboxdonation_billing_billingAddress_txtNZPostCode');

            // Credit expiration 
            groupSetOfFields('#bboxevent_payment_lblMonth, #bboxevent_payment_cboMonth');           
            groupSetOfFields('#bboxevent_payment_lblYear, #bboxevent_payment_cboYear');           

        }
    }, 1000);
});