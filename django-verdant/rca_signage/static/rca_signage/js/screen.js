var Screen = function() {
    this.currentPage =  1; // NB: number of page is 1-based so must be n-1 to use for array access purposes
    this.eventsData = [];
    this.eventsElem = '#eventlist';
    this.headingElem = $('#heading');
    this.loadingElem = $('#loading');
    this.pagingElem = $('#paging');
    this.pages = [];

    var $this = this;

    this.loadEvents = function() {
        console.log('loading events');
        
        // Perform ajax request
        $.getJSON("data", function(data) {
            console.log('events loaded');
            $this.eventsData = data;

            console.log($this.eventsData);
            $this.handleEvents();
        });
    };

    this.addToPage = function(elem){
        totalHeight += elem.outerHeight();
        if(typeof $this.pages[pageCounter] == "undefined"){
            $this.pages[pageCounter] = [];
        }
        $this.pages[pageCounter].push(elem.toArray()[0]); /* unclear why this bizarre toArray()[0] method is necessary. Can't find better alternative */
    };

    this.handleEvents = function(){
        console.log('handling events');
        
        // empty events list and create temporary ul used to measure height
        var tmpUl = $($this.eventsElem).empty().append('<ul id="tmp"></ul>');

        console.log(tmpUl)

        if($this.eventsData.is_special){
            console.log('special event detected');
            $this.headingElem.html('Special events')
        } else {
            console.log('no special events detected');
            $this.headingElem.html('Upcoming events')
        }

        for (var e=0; e < $this.eventsData.events.length; e++){
            var li = $('<li></li>');
            if ($this.eventsData.events[e].times && $this.eventsData.events[e].times.length){
               $('<p>' + $this.eventsData.events[e].times + '</p>').appendTo(li);
            }
            $('<h3>' + $this.eventsData.events[e].title + '</h3>').appendTo(li);
            if ($this.eventsData.events[e].location && $this.eventsData.events[e].location.length){
               $('<p>' + $this.eventsData.events[e].location + '</p>').appendTo(li);
            }
            if ($this.eventsData.events[e].specific_directions && $this.eventsData.events[e].specific_directions.length){
               $('<p>' + $this.eventsData.events[e].specific_directions + '</p>').appendTo(li);
            }
            $($this.eventsElem).find('#tmp').append(li);
        }        

        var totalHeight = 0;
        var pageCounter = 0;
        /*
            $($this.eventsElem).find('li').each(function(){
                if(totalHeight + $(this).outerHeight() > $($this.eventsElem).outerHeight()){
                    pageCounter ++;
                    totalHeight = 0;

                    $this.addToPage($(this));
                }else{
                    $this.addToPage($(this));
                }
            });
        */

        $($this.eventsElem).empty();

        for(var i=0; i < $this.pages.length; i++){
            var ul = $('<ul></ul>').appendTo($($this.eventsElem));
            ul.append($this.pages[i]);
        }

        //reset current page
        $this.currentPage = 0;
        $this.changePage();

        $($this.eventsElem).removeClass('loading');
        $this.pagingElem.html($this.currentPage + '/' + $this.pages.length).removeClass('loading');
        $this.loadingElem.hide();

    };   
}

Screen.prototype.loadEvents = function() {
    $this = this;

    console.log('loading events');
    // Perform ajax request
    $.getJSON("data", function(data) {
        console.log('events loaded');
        $this.eventsData = data;
        $this.handleEvents();
    });
};

Screen.prototype.changePage = function(){
    $this = this;

    // if beyond number of available pages, reset to 1
    if($this.currentPage + 1 > $this.pages.length){
        $this.currentPage = 0;
    }
    $this.currentPage++;

    if($this.pages.length >= $this.currentPage){
        $this.pagingElem.html($this.currentPage + '/' + $this.pages.length);
        $($this.eventsElem).find('ul').hide();
        $($this.eventsElem).find('ul:eq(' + ($this.currentPage-1) + ')').show()
    }
};


$(function() {
    var loadInterval = 3; // frequency (seconds) that new events are pulled from DB
    var pageInterval = 1; // frequence (seconds) that events are paginated

    // start screen system
    var screen = new Screen();
    screen.loadEvents();

    // load new events on an interval
    if(loadInterval){
        window.setInterval(function(){
            console.log($(screen.eventsElem).html())
            screen.loadEvents();

        }, loadInterval * 1000);
    }

    // rotate pages of events on an interval
    if(pageInterval){
        window.setInterval(function() {
           screen.changePage();
        }, pageInterval * 1000);
    }
});