var Screen = function() {
    var pageInterval = 20; // frequence (seconds) that events pages are paginated
    var loadInterval = pageInterval * 10; // frequency (seconds) that new events are pulled from DB
    var currentPage =  0;
    var eventsData = [];
    var eventsElemSelector = '#eventlist';
    var headingElemSelector = '#heading';
    var pagingElemSelector = '#paging';
    var pagingTimerSelector = '#paging-timer';
    var pages = [];

    function loadEvents() {
        clearInterval(window.pagingTimeout);
        $('body').addClass('loading');

        // Perform ajax request
        var data;
        $.getJSON("data/", function(data) {
            eventsData = data;
            handleEvents();

            if(loadInterval){
                // load new events on an interval
                window.loadTimeout = setTimeout(function(){
                    clearTimeout(window.loadTimeout); 
                    window.screen = null;
                    window.screen = new Screen();
                    window.screen.run();                
                }, loadInterval * 1000);
            }
        });
    };

    function handleEvents(){
        var pageCounter = 0;

        if(eventsData.is_special){
            $(headingElemSelector).html('Special Events');
            $('body').addClass('special');
        } else {
            $(headingElemSelector).html('Upcoming Events');
            $('body').removeClass('special');
        }

        // Check there actually are some events
        if (!eventsData.events.length){
            $(eventsElemSelector).append('<p>There are no upcoming events</p>');
            return false;
        }

        // temporary UL used to find heights of each event item
        var tmpUl = $('<ul id="tmp"></ul>');

        var tmpDate = null;
        for (var e=0; e < eventsData.events.length; e++){
            if(eventsData.events[e].date === tmpDate){
                eventsData.events[e].sameDay = true;
            } else {
                tmpDate = eventsData.events[e].date;
            }

            tmpUl.append(renderEvent(eventsData.events[e])); 
        }       

        // empty events list and create temporary ul used to measure height
        $(eventsElemSelector).empty().append(tmpUl);

        // if special events, do one per page
        if(eventsData.is_special){
            $('li', tmpUl).each(function(){
                var thisLi = $(this);
                
                if(typeof pages[pageCounter] == "undefined"){
                    pages[pageCounter] = [];
                }
                var thisLi = $(this);
                pages[pageCounter].push(thisLi.toArray()[0]); /* unclear why this bizarre toArray()[0] method is necessary. Can't find better alternative */
                pageCounter ++;
            });

        } else {    

            // distribute events into pages as required by their height
            var totalHeight = 0;
            
            $('li', tmpUl).each(function(){
                var thisLi = $(this);
                var thisLiHeight = parseInt(thisLi.outerHeight());

                if(totalHeight + thisLiHeight > $(eventsElemSelector).outerHeight()){
                    // start a new page
                    pageCounter ++;
                    
                    // reset total height
                    totalHeight = thisLiHeight;
                }else{
                    totalHeight += thisLiHeight;
                }

                if(typeof pages[pageCounter] == "undefined"){
                    pages[pageCounter] = [];
                }
                pages[pageCounter].push(thisLi.toArray()[0]); /* unclear why this bizarre toArray()[0] method is necessary. Can't find better alternative */
            });
        }

        // create separate UL for each page
        for(var i=0; i < pages.length; i++){
            var ul = $('<ul></ul>').append(pages[i]);
            ul.appendTo($(eventsElemSelector));
        }

        // set loadInterval to at least the total time for all pages to have rotated once at their current pageInterval rate
        if((pages.length * pageInterval) > loadInterval){
            loadInterval = pages.length * pageInterval;
        }

        tmpUl.remove();
        tmpUl = null;

        // remove loading indicators
        $('body').removeClass('loading');
        $(eventsElemSelector).removeClass('loading');

        // show/activate paging
        if(pages.length > 1){
            $(pagingElemSelector).html(currentPage + '/' + pages.length).removeClass('loading');
            // change to first page current page
            changePage();

            // set further display of pages on an interval
            if(pageInterval){
                window.pagingTimeout = setInterval(function() {
                    changePage();
                }, pageInterval * 1000);
            }

        }else{
             $(pagingElemSelector).hide();
        }       
    }; 

    function renderEvent(event){
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

    function changePage(){
        var pagerClone = $(pagingTimerSelector).clone(); 
        $(pagingTimerSelector).replaceWith(pagerClone);
        pagerClone = null;

        // if beyond number of available pages, reset to 1
        if(currentPage + 1 > pages.length){
            currentPage = 1;
        }else{
            currentPage++;
        }

        // add timer css to paging pie spinner if > 1 page
        if (pages.length > 1){
            $(pagingTimerSelector).find('*').attr('style', '-webkit-animation-duration:'+ pageInterval+'s').addClass('start');
        }

        if(pages.length >= currentPage){
            $(pagingElemSelector).html(currentPage + '/' + pages.length);
            $(eventsElemSelector).find('ul').hide();
            $(eventsElemSelector).find('ul:eq(' + ( currentPage-1 ) + ')').show()
        }
    };

    this.run = function(){
        clearTimeout(window.loadTimeout);
        loadEvents();
    };

}

$(function() {
    // start screen system
    window.screen = new Screen();
    window.screen.run();

    // means of testing non-rotated version
    $(document).click(function(){
        $('body').toggleClass('rotated')
    })
});