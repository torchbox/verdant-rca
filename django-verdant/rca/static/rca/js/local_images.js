//Only called in debug mode. Replaces broken images on the local build with production images
//on the live site (unless they have been added locally)
$(function(){
    var production_url = "http://www.rca.ac.uk/media/";
    var local_url = media_url;
    //setTimeout necessary to allow the images to have time to 404 rather
    //than the request getting cancelled which throws a load of errors to the terminal
    setTimeout(function(){
        $("img").each(function(){
            $(this).one("error", function(){
                this.src = this.src.replace(production_url, local_url);
            });
            this.src = this.src.replace(local_url, production_url);
        });
    },3000);
});