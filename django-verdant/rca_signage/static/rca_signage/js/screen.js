var Screen = function() {
    this.pageInterval = 20; // frequence (seconds) that events pages are paginated
    this.loadInterval = this.pageInterval * 10; // frequency (seconds) that new events are pulled from DB
    this.currentPage =  0;
    this.eventsData = [];
    this.eventsElemSelector = '#eventlist';
    this.headingElem = $('#heading');
    this.pagingElem = $('#paging');
    this.pagingTimerElem = $('#paging-timer');
    this.dateHeadingElem = $('#date');
    this.pages = [];

    var $this = this;

    this.run = function(){
        var loadTimeout, tmpLoadInterval;
        clearTimeout(loadTimeout);

        $this.loadEvents(function(){
            // load new events on an interval
            loadTimeout = setTimeout(function(){   
                screen = new Screen();
                screen.run(); 
            }, $this.loadInterval * 1000);
        });  
    };

    this.loadEvents = function(onComplete) {
        clearInterval(window.pagingTimeout);
        $('body').addClass('loading');

        // Perform ajax request
        $.getJSON("data", function(data) {
            $this.eventsData = data;
            $this.handleEvents(onComplete);
        });
    };

    this.handleEvents = function(onComplete){

        var pageCounter = 0;

        if($this.eventsData.is_special){
            $this.headingElem.html('Special events');
            $('body').addClass('special');
        } else {
            $this.headingElem.html('Upcoming events');
            $('body').removeClass('special');
        }

        // Check there actually are some events
        if (!$this.eventsData.events.length){
            $($this.eventsElemSelector).append('<p>There are no upcoming events</p>');
            return false;
        }

        // temporary UL used to find heights of each event item
        var tmpUl = $('<ul id="tmp"></ul>');

        var tmpDate = null;
        for (var e=0; e < $this.eventsData.events.length; e++){
            if($this.eventsData.events[e].date === tmpDate){
                $this.eventsData.events[e].sameDay = true;
            } else {
                tmpDate = $this.eventsData.events[e].date;
            }

            tmpUl.append($this.renderEvent($this.eventsData.events[e])); 
        }       

        // empty events list and create temporary ul used to measure height
        $($this.eventsElemSelector).empty().append(tmpUl);

        // if special events, do one per page
        if($this.eventsData.is_special){

            $('li', tmpUl).each(function(){
                var thisLi = $(this);
                
                if(typeof $this.pages[pageCounter] == "undefined"){
                    $this.pages[pageCounter] = [];
                }
                var thisLi = $(this);
                $this.pages[pageCounter].push(thisLi.toArray()[0]); /* unclear why this bizarre toArray()[0] method is necessary. Can't find better alternative */
                pageCounter ++;
            });

        } else {    

            // distribute events into pages as required by their height
            var totalHeight = 0;
            
            $('li', tmpUl).each(function(){
                var thisLi = $(this);
                var thisLiHeight = parseInt(thisLi.outerHeight());

                if(totalHeight + thisLiHeight > $($this.eventsElemSelector).outerHeight()){
                    // start a new page
                    pageCounter ++;
                    
                    // reset total height
                    totalHeight = thisLiHeight;
                }else{
                    totalHeight += thisLiHeight;
                }

                if(typeof $this.pages[pageCounter] == "undefined"){
                    $this.pages[pageCounter] = [];
                }
                $this.pages[pageCounter].push(thisLi.toArray()[0]); /* unclear why this bizarre toArray()[0] method is necessary. Can't find better alternative */
            });
        }

        // create separate UL for each page
        for(var i=0; i < $this.pages.length; i++){
            var ul = $('<ul></ul>').append($this.pages[i]);
            ul.appendTo($($this.eventsElemSelector));
        }

        // set loadInterval to at least the total time for all pages to have rotated once at their current pageInterval rate
        if(($this.pages.length * $this.pageInterval) > $this.loadInterval){
            $this.loadInterval = $this.pages.length * $this.pageInterval;
        }

        tmpUl.remove();

        // remove loading indicators
        $($this.eventsElemSelector).removeClass('loading');
        $this.pagingElem.html($this.currentPage + '/' + $this.pages.length).removeClass('loading');
        $('body').removeClass('loading');

        // change to first page current page
        $this.changePage();

           // set further rotation of pages on an interval
        if($this.pageInterval){
            window.pagingTimeout = setInterval(function() {
                $this.changePage();
            }, $this.pageInterval * 1000);
        }

        if(typeof onComplete == "function"){
            onComplete();
        }
    }; 

    this.renderEvent = function(event){
        var li = $('<li></li>');
        if (event.sameDay){
            li.addClass('same');
        }
        if (event.date && event.date.length){
           $('<p class="date">' + event.date + '</p>').appendTo(li);
        }
        if (event.times && event.times.length){
           $('<p>' + event.times + '</p>').appendTo(li);
        }
        $('<h3>' + event.title + '</h3>').appendTo(li);
        if (event.location && event.location.length){
           $('<p>' + event.location + '</p>').appendTo(li);
        }
        if (event.specific_directions && event.specific_directions.length){
           $('<p class="directions">' + event.specific_directions + '</p>').appendTo(li);
        }

        return li;
    };

    this.changePage = function(){
        var pagerHtml = $this.pagingTimerElem.html(); 
        $this.pagingTimerElem.empty().append(pagerHtml);

        // if beyond number of available pages, reset to 1
        if($this.currentPage + 1 > $this.pages.length){
            $this.currentPage = 1;
        }else{
            $this.currentPage++;
        }

        // add timer css to paging pie spinner if > 1 page
        if ($this.pages.length > 1){
            $this.pagingTimerElem.find('*').attr('style', '-webkit-animation-duration:'+ $this.pageInterval+'s').addClass('start');
        }

        if($this.pages.length >= $this.currentPage){
            $this.pagingElem.html($this.currentPage + '/' + $this.pages.length);
            $($this.eventsElemSelector).find('ul').hide();
            $($this.eventsElemSelector).find('ul:eq(' + ( $this.currentPage-1 ) + ')').show()
        }
    };
}

$(function() {
    // start screen system
    var screen = new Screen();
    screen.run();

    // means of testing non-rotated version
    $(document).click(function(){
        $('body').toggleClass('rotated')
    })
});