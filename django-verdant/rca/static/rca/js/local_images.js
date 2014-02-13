//Only called in debug mode. Replaces broken images on the local build with production images
//on the live site (unless they have been added locally)
$(function(){
    var production_url = "http://www.rca.ac.uk/media/";
    var local_url = media_url;
    $("img").each(function(){
         $(this).on("error", function(){
             this.src = this.src.replace(production_url, local_url);
        });
        this.src = this.src.replace(local_url, production_url);
    });
});