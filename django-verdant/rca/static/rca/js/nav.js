$(function(){
	Harvey.attach(breakpoints.mobileAndDesktopSmall, {
		setup: function(){
		},
		on: function(){
			mobileNav.apply();
		},
		off: function(){
			mobileNav.revoke();
		}
	});
	Harvey.attach(breakpoints.desktopRegular, {
		setup: function(){
		},
		on: function(){
			desktopNav.apply();
		},
		off: function(){
			desktopNav.revoke();
		}
	});

	/* IE<9 targetted execution of above desktopRegular Harvey stuff, since media queries aren't understood */
	$('.lt-ie9').each(function(){
		desktopNav.apply();
	});

});

var mobileNav = {
	apply: function() {
		$('.js-mobile-nav').addClass('dl-menuwrapper').dlmenu({
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
		$('.js-showmenu').removeClass('expanded');
		$('.js-mobile-nav').removeClass('dl-menuwrapper').removeData();
		$('js-mobile-nav *').removeClass('dl-subview dl-subviewopen');
		$('js-mobile-nav .dl-back').remove();
	}
}

var desktopNav = {
	apply: function(){

		var toggle = $('.js-showmenu');
		var $mainNav = $('.js-nav');

		$mainNav.each(setupNav);
		$('.js-priority-nav').each(setupNav);

		function openPriorityMenu($nav, $trigger) {
			$trigger.addClass('open');
			openMenu($nav);
		}

		function openMenu($nav){
			var $menu = $nav.find('.js-menu');

			$nav.addClass('changing');
			
			setTimeout(function(){
				$nav.removeClass('changing');
			}, 400)

			$nav.stop().animate({
				height: $nav.data('maxHeight')
			},200, function(){
				$nav.removeClass('changing').addClass('open');
			})

			$menu.stop().fadeIn(200, function(){
				//necessary to avoid some kind of weird race bug where opacity stops getting changed to 1
				$menu.css({opacity:1,display:'block'})
				$nav.removeClass('changing').addClass('open');
			});
		}

		function closeMenu($nav){
			var $menu = $nav.find('.js-menu');

			$nav.addClass('changing').removeClass('hovered');

			// reset or submenu
			setTimeout(function(){
				$('ul', menu).stop().removeAttr('style');
			}, 600)

			$menu.stop().hide()

			$nav.stop().animate({
				height: 0
			}, 200, function(){
				$nav.find('.selected > ul').stop().show()
				$nav.removeClass('changing').removeClass('open');
			});

			$nav.find('li:not(.selected) > ul').stop().fadeOut(100, function(){
				$(this).find('.selected > ul').fadeIn(100)
			});
		}

		function toggleMenu(event) {
			var $nav = event.data.nav;
			if($nav.hasClass('open')){
				closeMenu($nav);
			}else{
				openMenu($nav);
			}
		}

		// figures out ul heights and adds the hover effect to the child menu items
		// which reveal further levels of the menu
		// Also binds the events to reveal / hide the menus
		function setupNav() {
			var $self = $(this);
			var maxHeight = 0;
			var $menu = $(this).find('.js-menu');	

			// find tallest submenu
			$self.find('ul').each(function(){
				maxHeight = ($(this).height() > maxHeight) ? $(this).height() : maxHeight
			})

			$self.data('maxHeight', maxHeight + 70);

			// set menu as ready
			$self.addClass('ready');

			$('li', $menu).hoverIntent({
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
		};

		// open/close menu based on toggle click
		// namespace the click to allow distinction between desktop and mobile actions
		// passes the nav to be opened
		toggle.on('click.desktop',  {nav: $mainNav}, toggleMenu);

		// hover to show priority nav submenus
		// not namesapced as the priority nav is completely hidden at mobile
		$('.js-priority').each(function(){
			var $hover = $(this);
			var $subNav = $(this).find('.js-priority-nav');

			$hover.hoverIntent({
				over: function(e){
					openPriorityMenu($subNav, $hover);
				},
				out: function() {
					closeMenu($subNav);
				},
				timeout: 200
			});
		});
	},

	revoke: function(){
		$('.js-showmenu').off('.desktop'); // clears events in the .desktop namespace
		//$(document).off('.desktop');
		$('.js-nav').each(function(){
			$(this).removeClass('ready').removeClass('changing').attr('style', '');
			$('li, ul', $(this)).unbind().attr('style', '');
			$('.menu', $(this)).attr('style', '');
			$('.submenu', $(this)).attr('style', '');
		});
		$('.js-priority').unbind();
	}
};
