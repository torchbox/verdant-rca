# How to

## Content configuration

Configuration of the fields, content blocks and templates is all done within [site-app]/models.py. This file defines the templates that are available for use within Verdant, also the discreet blocks of content available on that template e.g Title, Related Link, Carousel. Furthermore it defines the fields that comprise any content block e.g A "Carousel item" might include an image, a link and a caption.

### Terminology

*	"Page": Defines the template for a kind of page and defines all the fields to be stored in the database against it. Any templates you create will subclass Page as it provides a few core fields by default: Title and Slug. e.g "def BlogPage(Page):" would create a template suitable for Blog entries, based on the basic Page model. 

*	"AdminHandler": This is created separately and defines the content blocks available to the Verdant user and links them to the fields defined in your instance of Page (see above).

*	"Panel": A Panel is an instance of a singular content block e.g a Title, a Body text field, an Author. These are defined within an AdminHandler and essentially state "Pages of this kind of template all have this content block".

*	"InlinePanel": This is for content blocks that repeat an unknown/unpredicatable number of times. While single, unrepeating fields can be defined as denormalised fields of your Page, the database can't forever add new fields for every instance of a mulitple content block. E.g a "Date published" is likely to be a single item on your page however a "Carousel item" would need to have multiple entries, each potentially comprising many fields. InlinePanel therefore creates a ForeignKey association between your Page and any Model you've created to represent this repeating content block.


# Troubleshooting / Idiosyncrasies

* 	Foreign key fields linked to other first-class Verdant citizens, e.g Images or Documents, declare "related_name='+'" in the ForeignKey definition. This is clumsy but necessary. It creates a bogus link to avoid a reference back to the object in which it is defined.

* 	You can't create a Field at any point in the site, with the same name as an existing Model . e.g if you create a News page/template with a field "Author", you will run into difficulties if you also have a separate template/Page model tcalled "Author." 

	The solution is to manually namespace. Rather than creating a template/Page called "Author", call it "AuthorPage". (This of course means you can't then create a separate template on which you have a field called AuthorPage, but hey ho).

