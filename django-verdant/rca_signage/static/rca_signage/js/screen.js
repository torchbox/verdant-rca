var conf = {
    currentPage: 1, // NB: number of page is 1-based so must be n-1 to use for array access purposes
    eventsData: [],
    loadInterval: 0, // frequency (seconds) that new events are pulled from DB
    pageInterval: 1, // frequence (seconds) that events are paginated
    eventsElem: $('#eventlist'),
    headingElem: $('#heading'),
    loadingElem: $('#loading'),
    pagingElem: $('#paging'),
    pages: [],

    loadEvents: function() {
        $this = this;

        console.log('loading events');
        // Perform ajax request
        $.getJSON("data", function(data) {
            console.log('events loaded');
            $this.eventsData = data;
            $this.handleEvents();
        });
    },

    handleEvents: function(){
        console.log('handling events');
        $this = this;
        
        $this.eventsElem.append('<ul></ul>');

        if($this.eventsData.is_special){
            console.log('special event detected');
            $this.headingElem.html('Special events')
        } else {
            console.log('no special events detected');
            $this.headingElem.html('Upcoming events')
        }

        for (var e=0; e < $this.eventsData.events.length; e++){
            var li = $('<li></li>').appendTo($this.eventsElem.find('ul'));
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
        }        

        var totalHeight = 0;
        var pageCounter = 0;

        function addToPage(elem){
            totalHeight += elem.outerHeight();
            if(typeof $this.pages[pageCounter] == "undefined"){
                $this.pages[pageCounter] = [];
            }
            $this.pages[pageCounter].push(elem.toArray()[0]); /* unclear why this bizarre toArray()[0] method is necessary. Can't find better alternative */
        }

        this.eventsElem.find('li').each(function(){
            if(totalHeight + $(this).outerHeight() > $this.eventsElem.outerHeight()){
                pageCounter ++;
                totalHeight = 0;

                addToPage($(this));
            }else{
                addToPage($(this));
            }
        });

        $this.eventsElem.empty();

        for(var i=0; i < $this.pages.length; i++){
            var ul = $('<ul></ul>').appendTo($this.eventsElem);
            ul.append($this.pages[i]);
        }

        //reset current page
        $this.currentPage = 0;
        $this.changePage();

        $this.eventsElem.removeClass('loading');
        $this.pagingElem.html($this.currentPage + '/' + $this.pages.length).removeClass('loading');
        $this.loadingElem.hide();

    },

    changePage: function(){
        // if beyond number of available pages, reset to 1
        if(this.currentPage + 1 > this.pages.length){
            this.currentPage = 0;
        }
        this.currentPage++;

        if(this.pages.length >= this.currentPage){
            this.pagingElem.html(this.currentPage + '/' + $this.pages.length);
            this.eventsElem.find('ul').hide();
            this.eventsElem.find('ul:eq(' + (this.currentPage-1) + ')').show()
        }
    }
}


$(function() {
    // load events
    var run = conf;
    run.loadEvents();

    // load new events on an interval
    if(run.loadInterval){
        window.setInterval(function(){
            run.loadEvents();
        }, run.loadInterval * 1000);
    }

    // rotate pages of events on an interval
    if(run.pageInterval){
        window.setInterval(function() {
           run.changePage();
        }, run.pageInterval * 1000);
    }
});