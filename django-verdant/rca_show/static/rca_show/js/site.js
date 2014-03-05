"use strict";

var overlay;

function setupOverlay(){
    var usedSlots = [];

    function randSlot(limitArray){
        if (typeof limitArray == "undefined"){
            limitArray = [1,2,3,4,5,6,7,8];
        }
        return limitArray[Math.floor(Math.random() * limitArray.length)];
    }

    function giveSlot(element, slot){
        if(usedSlots.indexOf(slot) > -1){
            return false;
        }
        usedSlots.push(slot);
        $(element).addClass('slot-' + slot);
        return true;
    }

    overlay.click(function(){
        $(this).removeClass('in');
        var resetTimeout = setTimeout(function(){
            overlay.hide();
            $('body').removeClass('showoverlay');
        }, 200);
    });

    // give a random slot to each eligible item
    $('.repos', overlay).each(function(){
        var slot;

        if($(this).hasClass('logo')){
            slot = randSlot([1,2,3]);
        }else{
            slot = randSlot();
        }

        while (!giveSlot($(this), slot)){
            slot = randSlot();
        }            
    })
}
function displayShowOverlay(){
    overlay.show();
    $('body').append(overlay);
    var showOverlayTimeout = setTimeout(function(){
        overlay.addClass('in');
        $('body').addClass('showoverlay');
    }, 400)
}

$(function(){
    Harvey.attach(breakpoints.mobile, {
        setup: function(){
          
        },
        on: function(){
            
        },
        off: function(){
          
        }
    });

    Harvey.attach(breakpoints.desktopSmall, {
        setup: function(){

        },
        on: function(){
          
        },
        off: function(){
            
        }
    });

    overlay = $('#showrca2014-overlay');

    if(overlay.length){
        setupOverlay();

        if(!$.cookie('showrca2014')){
            displayShowOverlay();
            $.cookie('showrca2014', '1', { expires: 0.5 });
        }
        
        $('.toggleoverlay').click(function(){
            displayShowOverlay();
        });
    }

    $('.jumplist').each(function(){
        var $this = $(this);
        $('.toggle', $this).click(function(){
            $this.toggleClass('open');
            $('.jumplist').not($this).removeClass('open');
        })
    });
});