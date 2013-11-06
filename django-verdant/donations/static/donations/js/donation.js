jQuery(function($) {

    $.fn.serializeObject = function(){
        var o = {};
        var a = this.serializeArray();
        $.each(a, function() {
            if (o[this.name] !== undefined) {
                if (!o[this.name].push) {
                    o[this.name] = [o[this.name]];
                }
                o[this.name].push(this.value || '');
            } else {
                o[this.name] = this.value || '';
            }
        });
        return o;
    };

    function fieldError(field, msg){
      $(field).closest("li")
        .addClass("error")
        .append($("<li/>").addClass("error-message").text(msg));
    }

    function scrollUp(){
      $(document.body).animate({
        scrollTop: $(".messages").show().offset().top - $(".nav-wrapper").height() - 5
      }, 500);
    }

    function stripeResponseHandler(status, response) {
      var $form = $('#payment-form');

      if (response.error) {
        // Show the errors on the form
        $(".errorlist").append($("<li/>").addClass("error-message").text(response.error.message));
        scrollUp();
        $form.removeClass("loading").find('button').prop('disabled', false);
      } else {
        // token contains id, last4, and card type
        var token = response.id;
        // Set the token so it gets submitted to the server
        $form.find('[name="stripe_token"]').val(token);

        // let's not submit credit card details to our server because we don't need them
        $form.find('[data-stripe="number"], [data-stripe="cvc"], [data-stripe="exp-month"], [data-stripe="exp-year"]').val("");

        // and re-submit without javascript
        // TODO: currently this doesn't trigger the jquery submit event but it might in the future
        $form.get(0).submit();
      }
    }

  $('[data-stripe="number"]').payment('formatCardNumber');
  $('[data-stripe="cvc"]').payment('formatCardCVC');
  $('[name="amount"]').keypress(function(eve) {
    if ((eve.which != 46 || $(this).val().indexOf('.') != -1) && (eve.which < 48 || eve.which > 57)  ) {
        eve.preventDefault();
    }
  }).keyup(function(eve) {
    // this part is when left part of number is deleted and leaves a . in the leftmost position.
    // For example, 33.25, then 33 is deleted
    if($(this).val().indexOf('.') == 0) {
        $(this).val($(this).val().substring(1));
    }
  });


  $('#payment-form').submit(function(e) {
    var $form = $(this);

    var scroll = window.scrollY;
    $(".error-message", $form).map(function(){
        scroll -= $(this).outerHeight();
        scroll -= 2;
    });
    $(".error-message", $form).remove();
    $(".error", $form).removeClass("error");
    $(window).scrollTop(scroll);

    var error = false;

    var amount = $('[name="amount"]').val(),
        ccNum = $('[data-stripe="number"]').val(),
        cvcNum = $('[data-stripe="cvc"]').val(),
        expMonth = $('[data-stripe="exp-month"]').val(),
        expYear = $('[data-stripe="exp-year"]').val();

    $('[name="amount"]').val(amount.replace(/\.$/, ""));

    if (!Stripe.validateCVC(cvcNum)) {
        error = true;
        fieldError('[data-stripe="cvc"]', cvcNum ? 'The CVC number appears to be invalid.' : 'This field is required.');
    }
    if (!Stripe.validateExpiry(expMonth, expYear)) {
        error = true;
        fieldError('[data-stripe="exp-month"], [data-stripe="exp-year"]', 'The expiration date appears to be invalid.');
    }
    if (!Stripe.validateCardNumber(ccNum)) {
        error = true;
        fieldError('[data-stripe="number"]', ccNum ? 'The credit card number appears to be invalid.' : 'This field is required.');
    }
    if (!/\d+(\.\d+)?/.test(amount)) {
        error = true;
        fieldError('[name="amount"]', amount ? 'The amount specified appears to be invalid.'  : 'This field is required.');
    }
    if(error){
        scrollUp();
        return false;
    }

    $(".error-message", $form).remove();
    $(".error", $form).removeClass("error");


    // Disable the submit button to prevent repeated clicks
    $form.addClass("loading").find('button').prop('disabled', true);
    var name = "";
    var title = $form.find("[name=title]").val();
    var first_name = $form.find("[name=first_name]").val();
    var last_name = $form.find("[name=last_name]").val();
    if(title){
        name += title + " ";
    }
    if(first_name){
        name += first_name+ " ";
    }
    if(last_name){
        name += last_name;
    }
    // we have to serialise the form and make sure the correct attributes are set
    var formData = $form.serializeObject();
    var params = $.extend(formData, {
        exp_month: $form.find('[data-stripe="exp-month"]').val(),
        exp_year: $form.find('[data-stripe="exp-year"]').val(),
        name: name
    });

    Stripe.createToken(params, stripeResponseHandler);
    // Stripe.createToken($form[0], stripeResponseHandler);

    // Prevent the form from submitting with the default action
    return false;
  });
});