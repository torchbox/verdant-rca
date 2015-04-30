"use strict";

var overlay;

var themes = ['architecture', 'communication', 'design', 'fineart', 'humanities', 'material'];

function randTheme(){
    var chosen;

    if(!$.cookie('showrcatheme')){
        chosen = themes[Math.floor(Math.random() * themes.length)];
        $.cookie('showrcatheme', chosen, { expires: 0.04, path: window.showIndexPath || '/' });
    } else {
        chosen = $.cookie('showrcatheme')
    }

    $('body').addClass('theme-schoolof' + chosen);
    return chosen;
}

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
        var vid = $('video', overlay).get()[0];
        vid.play();
        $('video', overlay).coverVid(500, 281);
    }, 400)
}

$(function(){
    // Only enable overlay for non-touch devices
    overlay = $('.no-touch #overlay');

    if(overlay.length){
        var cookieName = '2015';

        randTheme();

        if(window.debug || (!$('body').hasClass('type-login') && !$.cookie(cookieName))){
            setupOverlay();
            displayShowOverlay();
           $.cookie(cookieName, '1', { expires: 0.04, path: '/' });
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