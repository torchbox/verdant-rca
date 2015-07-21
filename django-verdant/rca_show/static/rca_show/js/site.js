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

    /* x-plus functionality */

    $('.x-plus').each(function(){
        var $this = $(this);
        var paginationContainer = $this.data('pagination');
        var loadmore = $('.load-more', $this);
        var loadmoreTarget = $('.load-more-target', $this);
        var itemContainer = $('.item-container', $this);
        var ul = $('> ul', itemContainer);
        var items = $('> li', ul);
        var step = 100;
        var hiddenClasses = 'hidden fade-in-before';
        var contractedHeight = items.first().height();

        // split list at the 'load-more-target' item.
        var loadmoreTargetIndex = items.index(loadmoreTarget);
        var loadmoreIndex = items.index(loadmore);
        var newItems = items.slice(loadmoreTargetIndex, loadmoreIndex);

        var prepareNewItems = function(items){
            items.addClass(hiddenClasses);
        };

        var showNewItems = function(){
            itemContainer.css('height', itemContainer.height());
            newItems.removeClass('hidden');
            itemContainer.animate({height:ul.height()}, expansionAnimationSpeed, function(){
                itemContainer.removeAttr('style');
            });

            // Fade in each item one by one
            var time = 0;
            newItems.each(function(index){
                var $item = $(this);
                setTimeout( function(){
                    $item.addClass('fade-in-after');
                }, time);
                time += step;
            });
        };

        var hideNewItems = function(){
            $this.removeClass('expanded');
            itemContainer.animate({height:contractedHeight}, expansionAnimationSpeed, function(){
                itemContainer.removeAttr('style');
                newItems.addClass('hidden');
            });

            // Fade out each item one by one
            var time = 0;
            newItems.reverse().each(function(index){
                var $item = $(this);
                setTimeout( function(){
                    $item.removeClass('fade-in-after').addClass('fade-in-before');
                }, time);
                time += step;
            });
        };

        // prepare the items already in the page (if non-inifinite-scroll)
        prepareNewItems(items.slice(loadmoreTargetIndex, loadmoreIndex));

        // This click event can originate from the filtered results on an index page or any other paginated content.
        // If it is form a filter then we need to use event delegation but on other pages with multiple paginated
        // items this would result in a single event handler bound multiple times to the same container element.
        // So we have to use different containers to bind the event to: #listing for filters, and $this for everything else.
        var $bindTo = $this.closest("#listing").length ? $this.closest("#listing") : $this;

        $($bindTo).on("click", ".load-more", function(e){
            e.preventDefault();
            var loadmore = $(this);

            if(paginationContainer && $(paginationContainer).length){
                var nextLink = $('.next a', $(paginationContainer));
                var nextLinkUrl = nextLink.attr('href');

                // get next set of results
                var nextPage = $('<html></html>').load(nextLinkUrl, function(){
                    newItems = $('.x-plus.item-container > ul > li:not(.load-more)', nextPage);
                    prepareNewItems(newItems);
                    loadmore.before(newItems);
                    if(loadmore.hasClass('gallery-load-more')){
                        alignGallery();
                    }

                    // get next pagination link
                    if($(paginationContainer + ' .next a', nextPage).length){
                        nextLink.attr('href', $(paginationContainer + ' .next a', nextPage).attr('href'));
                    }else{
                        loadmore.remove();
                    }
                    showNewItems();

                });
            }else if(!$this.hasClass('expanded')){
                showNewItems();
                $this.addClass('expanded');
            }else{
                hideNewItems();
            }

            return false;
        });
    });
});
