$(function() {
    var currentPage = 0;
    var pages = []

    function setPage(newPage) {
        // If there are no pages, do nothing
        if (pages.length == 0) {
            return;
        }

        // Wrap page id
        if (newPage >= pages.length)
            newPage = 0;

        // Switch to next page
        currentPage = newPage;
        $("div#content").html(pages[currentPage]);
    }

    function updatePages() {
        // Perform ajax request
        $.getJSON("data", function(newPages) {
            // Get new pages
            pages = newPages;

            // Go back to first page
            setPage(0);
        });
    }
    updatePages();

    // Update pages every minute
    window.setInterval(updatePages, 60000);

    // Rotate pages every 10 seconds
    window.setInterval(function() {
        // Go to next page
        setPage(currentPage + 1)
    }, 10000);
});