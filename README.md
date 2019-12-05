# Getting Started

## Vagrant

* Install [Vagrant](https://wiki.torchbox.com/view/Vagrant)
* ```git clone git@github.com:torchbox/verdant-rca.git```
* ```cd verdant-rca```
* ```vagrant up```
* ```vagrant ssh```
* ```djrun```
* Edit your code locally, browse at [localhost:8000](http://localhost:8000/)

## Docker

There is a docker-compose file included in djang-verdant/docker-compose. Run with `docker-compose up`
the site will be available on 0.0.0.0:8509.

# Deployments

Deployments are handled by [CircleCi](https://circleci.com/gh/torchbox/workflows/verdant-rca).

### Staging

Merging to the `staging` branch will trigger an automatic deployment to the stage site.

### Production

Merging to the `master` branch will trigger a deployment to production, however Circle will await a manual approval before releasing the build to production.

# Gotchas

You may encounter a "Invalid input of type: 'CacheKey'" error when running a new box locally. This is due to a bug in django-redis (see https://github.com/niwinz/django-redis/issues/342) and can be worked around by adding:

`redis==2.10.6` to `django-verdant/requirements.txt` and then running `pip install -r requirements.txt`


# Implementation notes

* MyRCA / student profiles: https://projects.torchbox.com/projects/rca-django-cms-project/notebook/Implementation%20notes%20for%20%22My%20RCA%22%20feature.md
* Course registration: https://projects.torchbox.com/projects/rca-django-cms-project/notebook/Implementation%20notes%20for%20Course%20registration%20(%23788).md


# My RCA

Students (synced via LDAP) can access My RCA area via `/my-rca` to log in. To test, create a test user account with a student role.

## Set up My RCA on new builds (clean db)

If you are starting a new build (ie without using live db) you will need to set pages for the 'Student pages' and 'RCA Now pages' at `/admin/settings/student_profiles/studentprofilessettings/1/` before you can use the My RCA area.

Also you will need to add the following user groups (with same ID)

- Students => 3
- MA Students => 4
- MPhil Students => 5
- PhD Students => 6


# Front end notes on the main RCA build


## Original set up and build

It was orignally built to a design provided by an external agency, and some of the terminology e.g. 'modules' and the names of the text styles are based on their original terminology.

There is no tooling, and the site uses django compressor.


### CSS

This build uses Less.

It was built before the practice of splitting CSS into components became common, and when we still split different media queries for elements into different files.

There is a main file called `core.less` with stylings for different breakpoints in `desktop-small.less`, `desktop-regular.less` and `desktop-lare.less`. This originally contained styles for things like headings, text, site layout and navigation. Navigation styling is now in a separate component file (see below).

Styling for individual page elements are contained in a file called `modules.less`, with styling for different breakpoints in `modules-desktop-small.less` etc.

As of the homepage redesign 2018, we have created a `components` folder for any new styling in the site (using bem). If updating existing styling, you can either work with the original files or refactor the code into components.

There is also a `streamfield-blocks` folder for streamfield blocks - mostly homepage components.

There are a number of text styles in `core.less`, some of which have overrides for different breakpoints. They are based on the original text styles provided by the design agency. They can be confusing to use, especially as they use ems so are affected by the size of the parent element. For new work it is advisable to just follow the design, and set the text size, font style etc for individual elements.

### Sprites

The code from the original build uses a png sprite technique. There are 3 different sprite sheets, and each has a standard version and a retina version. There are mixins available (for each sprite sheet) to load a sprite for an element. The arguments you pass to the mixin are the width and height of the image, and its position in the sprite sheet for both standard and retina. Uploading the sprite sheet to a service like spritecow.com is the easiest way to work out these dimensions. Sprites are generally loaded as a backround image to an `:after` element.

As of the homepage redesign 2018, there is now an svg sprite (`templates/includes/sprites.html`) loaded in via base.html, so any new icons can be added here in the more standard fashion.

### Template structure

RCA was the first wagtail build and all page definitions were added to one model file. The template structure is equally flat, with all page templates sitting directly in the `templates` folder. There is an `includes` file for includes, and a subfolder within that for html relating to 'modules' (see the CSS section above).

Note that all templates for template tags sit in a separate `tags` subfolder.

There's the usual `blocks` folder for streamfield block templates.

### Carousels
The original carousel used was bxslider, and on some templates there is still functionality to add a hero carousel (with both videos and images) using bxslider. The bxslider javascript is loaded via base.html. RCA are not using this functionality much and it may get removed at a later date.

When the homepage 2018 redesign happened, there was a need to use another carousel, slick, in order to use the centre mode functionality.

### Navigation

See `statics/js/nav.js`.

The new navigation (as of the 2018 redesign) uses a combination of a prioity nav pattern with a mega menu. In order to achieve this, the markup for the priority navigation elements is repeated, including all of the submenus. This is quite a bit of extra code per page load, and should probably be subject to further performance testing, but budget did not allow.

The mobile menu uses a library called dl-menu, which has been used since the beginning. This provides the javascript for the mobile mega menu with a back button as you drill down.

The desktop menu uses the same markup, but completely different functionality. There is custom javascript to reveal elements as you hover over them in the mega menu. In order to achieve this, when the desktop menu is initialised it calculates the maximum possible height of all the submenus. This means that care needs to be taken when adjusting CSS for the menu - any changes that might affect the height of the menus before it is revealed (e.g. display, width etc) should be avoided.

Harvey is used (as it is throughout the site) in order to switch between the desktop and mobile versions of the menu as the screen resizes.
