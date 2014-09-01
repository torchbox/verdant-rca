// JAVASCRIPT HELPERS FOR BLACKBAUD DONATION FORM
$(function() {
    // Grouping of fields
    function groupSetOfFields(fieldSelectors) {
        console.log('here');
        $(fieldSelectors).wrapAll('<div class="grouped-form-items"></div>');
    }

    //Remove the JS added Blackbaud CSS when loaded. 
    var el = 'link[href^="https://bbox.blackbaudhosting.com/webforms"]';

    var blackbaudElementCheckInterval = setInterval(function(){
        //Run once form has loaded
        if ($(el).length) {
            clearInterval(blackbaudElementCheckInterval);

            //remove the stylesheet found
            $(el).remove();

            $('#bbox-root #mongo-form').css({opacity: 0, visibility: "visible"}).animate({opacity: 1.0}, 200); //Smooth intro for the form.
            
            // FORM HELPERS for Donations

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


            //Group firstname label with input
            groupSetOfFields('#bboxdonation_billing_lblFullName, #bboxdonation_billing_txtFirstName');
            //Group lastname label with input 
            groupSetOfFields('#bboxdonation_billing_lblLastName, #bboxdonation_billing_txtLastName');
            //Group the above groups 
            groupSetOfFields('#divName .grouped-form-items');
            //Group Provience and Postcode 
            groupSetOfFields('#bboxdonation_billing_billingAddress_lblCAProvince, #bboxdonation_billing_billingAddress_ddCAProvince, #bboxdonation_billing_billingAddress_ddCAProvince + .select');
            groupSetOfFields('#bboxdonation_billing_billingAddress_lblState , #bboxdonation_billing_billingAddress_ddState, #bboxdonation_billing_billingAddress_ddState + .select');

            groupSetOfFields('#bboxdonation_billing_billingAddress_lblCAPostCode, #bboxdonation_billing_billingAddress_txtCAPostCode');
            
            groupSetOfFields('#bboxdonation_billing_billingAddress_lblZip, #bboxdonation_billing_billingAddress_txtZip');

            groupSetOfFields('#bboxdonation_billing_billingAddress_lblNZCity, #bboxdonation_billing_billingAddress_ddNZCity, #bboxdonation_billing_billingAddress_ddNZCity + .select');

            groupSetOfFields('#bboxdonation_billing_billingAddress_lblNZPostCode, #bboxdonation_billing_billingAddress_txtNZPostCode');

        }
    }, 1000);
});