var Screen = function() {
    this.loadInterval = 10; // frequency (seconds) that new events are pulled from DB
    this.pageInterval = 2; // frequence (seconds) that events pages are paginated
    this.currentPage =  0;
    this.eventsData = [];
    this.eventsElemSelector = '#eventlist';
    this.headingElem = $('#heading');
    this.pagingElem = $('#paging');
    this.dateHeadingElem = $('#date');
    this.pages = [];

    var $this = this;

    this.loadEvents = function(onComplete) {

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
        // if beyond number of available pages, reset to 1
        if($this.currentPage + 1 > $this.pages.length){
            $this.currentPage = 1;
        }else{
            $this.currentPage++;
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
    var loadInterval;
    var screen = new Screen();
    screen.loadEvents(function(){
        loadInterval = screen.loadInterval;
    
        // load new events on an interval
        window.setInterval(function(){          
            screen = new Screen();
            screen.loadEvents(function(){
                loadInterval = screen.loadInterval;
            });            

        }, loadInterval * 1000);

    });

    // rotate pages of events on an interval
    if(screen.pageInterval){
        window.setInterval(function() {
           screen.changePage();
        }, screen.pageInterval * 1000);
    }
});