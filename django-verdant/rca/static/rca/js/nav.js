$(function(){

	Harvey.attach(breakpoints.mobile, {
		setup: function(){},
		on: function(){
			
			    // function showHideMobileMenu(){
			    //     $('.js-showmenu').click(function(eventObject){
			    //         $('.js-mobile-nav').toggleClass('expanded');
			    //         $(this).toggleClass('expanded');
			    //     });
		    	// }
		},
		off: function(){
			
		}
	});
	Harvey.attach(breakpoints.desktopSmall, {
		setup: function(){},
		on: function(){
			/* Duplicate anything added to this function, into the ".lt-ie9" section below */

			//enable desktop dropdown nav and kill mobile nav
			desktopNav.apply();
			mobileNav.revoke();
		},
		off: function(){
			//kill desktop dropdown nav and enable mobile nav
			desktopNav.revoke();
			mobileNav.apply();
		}
	});

	/* IE<9 targetted execution of above desktopSmall Harvey stuff, since media queries aren't understood */
	$('.lt-ie9').each(function(){
		desktopNav.apply();
	});

});

var mobileNav = {
	apply: function() {
		$('js-mobile-nav').addClass('dl-menuwrapper').dlmenu({
			animationClasses : {
				classin : 'dl-animate-in-2',
				classout : 'dl-animate-out-2'
			}
		});

		function toggleMobileNav() {
			$('.js-mobile-nav').toggleClass('expanded');
			$('.js-showmenu').toggleClass('expanded');
		}

		// namespace the click to allow distinction between desktop and mobile actions
		$('.js-showmenu').on('click.mobile', toggleMobileNav);
	},

	revoke: function() {
		$('.js-showmenu').off('.mobile'); // clears events in the .mobile namespace
		$('.js-mobile-nav').removeClass('dl-menuwrapper').removeData();
		$('js-mobile-nav *').removeClass('dl-subview dl-subviewopen');
		$('js-mobile-nav .dl-back').remove();
	}
}

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

		$('.js-nav-wrapper nav:not(.dl-menuwrapper)').each(function(){
			var $self = $(this);
			var maxHeight = 0;
			var selected = $('.selected', $self).clone();
			var menu = $('.js-menu');
			var toggle = $('.js-showmenu');

			// find tallest submenu
			$self.find('ul').each(function(){
				maxHeight = ($(this).height() > maxHeight) ? $(this).height() : maxHeight
			})

			$self.data('maxHeight', maxHeight + 70);

			// set menu as ready
			$self.addClass('ready');

			function openMenu(){
				$self.addClass('changing');
				setTimeout(function(){
					$self.removeClass('changing');
				}, 400)

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
			}

			function toggleMenu() {
				if($self.hasClass('open')){
					closeMenu();
				}else{
					openMenu();
				}
			}

			function clearMenu(e) {
				if(!$(e.target).hasClass('js-showmenu')){
					closeMenu();
				}
			}

			// open/close menu based on toggle click
			// namespace the click to allow distinction between desktop and mobile actions
			$(document).on('click.desktop', toggle, toggleMenu);

			// close menu on all clicks outside the toggle
			$(document).on('click.desktop', clearMenu);

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
		//$('.js-showmenu').off('.desktop'); // clears events in the .desktop namespace
		$(document).off('.desktop');
		$('.js-nav-wrapper nav').each(function(){
			$(this).unbind().removeClass('ready').removeClass('changing').attr('style', '');
			$('li, ul', $(this)).unbind().attr('style', '');
			$('.menu', $(this)).attr('style', '');
			$('.submenu', $(this)).attr('style', '');
		})
	}
};
