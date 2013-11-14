jQuery(function(){

    var $dateRange = $('#dateRange');

    var downloadLink = $(".download").attr("href") + "?";

    $dateRange.daterangepicker({
        posX: $dateRange.offset().left,
        posY: $dateRange.offset().top + $('#dateRange').height() + 18,
        earliestDate: new Date(2013, 7, 9),
        latestDate: new Date(),
        dateFormat: "dd/mm/yy",
        onChange: function(){
            var range = $dateRange.val();
            var bits = range.split(" - ");
            var from = bits[0];
            var to = bits[1];
            var params;

            bits = from.split("/");
            from = new Date(bits[2], parseInt(bits[1], 10) - 1, bits[0]);
            if(to){
                // date range
                bits = to.split("/");
                to = new Date(bits[2], parseInt(bits[1], 10) - 1, bits[0]);
                params = "date_from=" + from.toString('yyyy-MM-dd') + "&date_to=" + to.toString('yyyy-MM-dd');
            }else{
                // single day
                params = "date_from=" + from.toString('yyyy-MM-dd') + "&date_to=" + from.toString('yyyy-MM-dd');
            }

            $(".download").attr("href", downloadLink + params);
       }
    });

    $(".ui-daterangepickercontain").css($dateRange .position()).css("top", "+=" + $dateRange.outerHeight());

});