$(function(){

	/* configure left slideout menu toggle */
	$(".mobile-menu-button").toggleClick(function(){
		$("body").addClass("show-mobile-menu");
	},function(){
		$("body").removeClass("show-mobile-menu");
	});


	// copy the sidebar so that we can show it on the left in the mobile version
	if(!$(".mobile-menu-wrapper > aside").length){
		$(".mobile-menu-wrapper").append($(".page-wrapper > aside").clone(true, true));
	}

	Harvey.attach(breakpoints.mobile, {
		setup: function(){},
		on: function(){
			$('nav').addClass('dl-menuwrapper').dlmenu({
				animationClasses : {
					classin : 'dl-animate-in-2',
					classout : 'dl-animate-out-2'
				}
			});
		},
		off: function(){
			$('nav').removeClass('dl-menuwrapper').removeData();
			$('nav *').removeClass('dl-subview dl-subviewopen');
			$('nav .dl-back').remove();

			// remove width from page content which is needed to keep it constant when showing the mobile menu
			$("body").removeClass("show-mobile-menu");
			$("body, .mobile-content-wrapper").removeAttr("style");

		}
	});
	Harvey.attach(breakpoints.desktopSmall, {
		setup: function(){},
		on: function(){
			/* Duplicate anything added to this function, into the ".lt-ie9" section below */

			//enable desktop dropdown nav
			desktopNav.apply()
		},
		off: function(){
			//kill desktop dropdown nav
			desktopNav.revoke()
		}
	});

	/* IE<9 targetted execution of above desktopSmall Harvey stuff, since media queries aren't understood */
    $('.lt-ie9').each(function(){
        desktopNav.apply()
    })

});

var desktopNav = {
	apply: function(){
		// highlight the path to the current page in the menu based on the url
		// it might not contain all the levels leading to it
		var path = document.location.pathname;
		while(path.split("/").length > 2){
			var $menuItem = $(".menu a[href$='" + path + "']");
			if($menuItem.length){
				$menuItem.parents("li").addClass("selected");
				break;
			}else{
				path = path.split("/").slice(0, -2).join("/") + "/";
			}
		}

		$('.nav-wrapper nav:not(.dl-menuwrapper)').each(function(){
			var $self = $(this);
			var maxHeight = 0;
			var selected = $('.selected', $self).clone();
			var menu = $('.menu', $self);
			var toggle = $('h2', $self);

			// find tallest submenu
			$self.find('ul').each(function(){
				maxHeight = ($(this).height() > maxHeight) ? $(this).height() : maxHeight
			})

			/* create breadcrumb menu from selected items */
			selected.find('ul').remove();
			menu.before($('<ul class="breadcrumb"></ul>').append(selected));

			$self.data('maxHeight', maxHeight + 70);

			// set menu as ready
			$self.addClass('ready');

			function openMenu(){
				$self.addClass('changing');
				setTimeout(function(){
					$self.removeClass('changing');
				}, 400)

				$self.find('.breadcrumb').stop().hide();

				$self.stop().animate({
					height: $self.data('maxHeight')
				},200, function(){
					$self.removeClass('changing').addClass('open');
				})

				menu.stop().fadeIn(200, function(){
					//necessary to avoid some kind of weird race bug where opacity stops getting changed to 1
					menu.css({opacity:1,display:'block'})
					$self.removeClass('changing').addClass('open');
				});
			}

			function closeMenu(){
				$self.addClass('changing').removeClass('hovered');

				// reset or submenu
				setTimeout(function(){
					$('ul', menu).stop().removeAttr('style');
				}, 600)


				menu.stop().hide()

				$self.stop().animate({
					height: 34
				}, 200, function(){
					// $self.find('.selected > ul').stop().show()
					$self.removeClass('changing').removeClass('open');
				});

				$self.find('li:not(.selected) > ul').stop().fadeOut(100, function(){
					$(this).find('.selected > ul').fadeIn(100)
				});

				$self.find('.breadcrumb').stop().fadeIn(200, function(){
					$(this).removeClass('changing');
				})
			}

			// open/close menu based on toggle click
			toggle.click(function(){
				if($self.hasClass('open')){
					closeMenu();
				}else{
					openMenu();
				}
			});

			// close menu on all clicks outside the toggle
			$(document).on('click', function(e){
				if($(e.target).get(0) != toggle.get(0)){
					closeMenu();
				}
			});

			$('li', menu).hoverIntent({
				over: function(e){
					$self.addClass('hovered');

					$('.open', $(this).parent()).removeClass('open');
					$(this).addClass('open').parents('li').addClass('open');

					$(this).siblings().find(' > ul').stop().hide();
					$(this).find(' > ul').stop().fadeIn(200);
				},
				out: function(){},
				timeout: 200
			});
		});
	},

	revoke: function(){
		$('nav').each(function(){
			$(this).unbind().removeClass('ready').removeClass('changing').attr('style', '');
			$('li, ul', $(this)).unbind().attr('style', '');
			$('.breadcrumb', $(this)).remove()
			$('.menu', $(this)).attr('style', '');
			$('.submenu', $(this)).attr('style', '');
		})
	}
};