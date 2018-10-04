$(function(){

	Harvey.attach(breakpoints.mobileAndDesktopSmall, {
		setup: function(){
			console.log('setup mobileAndDesktopSmall');
			mobileNav.apply();
		},
		on: function(){
				console.log('on mobileAndDesktopSmall');
		},
		off: function(){
			console.log('off mobileAndDesktopSmall');
		}
	});
	Harvey.attach(breakpoints.desktopRegular, {
		setup: function(){
			console.log('setup desktopRegular');
		},
		on: function(){
			console.log('on desktopRegular');
			/* Duplicate anything added to this function, into the ".lt-ie9" section below */

			//enable desktop dropdown nav and kill mobile nav
			desktopNav.apply();
			mobileNav.revoke();
		},
		off: function(){
			console.log('off desktopRegular');
			//kill desktop dropdown nav and enable mobile nav
			desktopNav.revoke();
			mobileNav.apply();
		}
	});

	/* IE<9 targetted execution of above mobileAndDesktopSmall Harvey stuff, since media queries aren't understood */
	$('.lt-ie9').each(function(){
		desktopNav.apply();
	});

});

var mobileNav = {
	apply: function() {
		console.log('apply mobile nav');
		$('.js-mobile-nav').addClass('dl-menuwrapper').dlmenu({
			animationClasses : {
				classin : 'dl-animate-in-2',
				classout : 'dl-animate-out-2'
			}
		});

		function toggleMobileNav() {
			console.log('toggling mobile nav');
			$('.js-mobile-nav').toggleClass('expanded');
			$('.js-showmenu').toggleClass('expanded');
		}

		// namespace the click to allow distinction between desktop and mobile actions
		$('.js-showmenu').on('click.mobile', toggleMobileNav);
	},

	revoke: function() {
		console.log('revoke mobile nav');
		$('.js-showmenu').off('.mobile'); // clears events in the .mobile namespace
		$('.js-mobile-nav').removeClass('dl-menuwrapper').removeData();
		$('js-mobile-nav *').removeClass('dl-subview dl-subviewopen');
		$('js-mobile-nav .dl-back').remove();
	}
}

var desktopNav = {
	apply: function(){
		console.log('apply desktop nav');
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

		//$('.js-nav').each(setupNav);
		//$('.js-priority-nav').each(setupNav);

		$('.js-nav').each(function() {
			var $self = $(this);
			var maxHeight = 0;
			//var selected = $('.selected', $self).clone();
			var menu = $('.js-menu');
			var toggle = $('.js-showmenu');

			// find tallest submenu
			$self.find('ul').each(function(){
				maxHeight = ($(this).height() > maxHeight) ? $(this).height() : maxHeight
			})

			$self.data('maxHeight', maxHeight + 70);

			// set menu as ready
			$self.addClass('ready');

			function openMenu(maxHeight){
				$self.addClass('changing');
				setTimeout(function(){
					$self.removeClass('changing');
				}, 400)

				$self.stop().animate({
					height: maxHeight
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
					$self.find('.selected > ul').stop().show()
					$self.removeClass('changing').removeClass('open');
				});

				$self.find('li:not(.selected) > ul').stop().fadeOut(100, function(){
					$(this).find('.selected > ul').fadeIn(100)
				});
			}

			function toggleMenu(maxHeight) {
				if($self.hasClass('open')){
					console.log('desktop close');
					closeMenu();
				}else{
					console.log('desktop open');
					openMenu(maxHeight);
				}
			}

			// function clearMenu(e) {
			// 	console.log('calling clear menu');
			// 	if(!$(e.target).hasClass('js-showmenu')){
			// 		closeMenu();
			// 	}
			// }

			// open/close menu based on toggle click
			// namespace the click to allow distinction between desktop and mobile actions
			// also pass the maxHeight from the data stored on $self, because for some reason I can't work
			// out, the maxHeight data isn't accessible from within any of the sub functions (even though other methods such
			// as css() work fine)
			$(document).on('click', toggle, toggleMenu.bind(toggleMenu, $self.data('maxHeight')));
			//$(document).on('mouseover', $('.js-hover-menu'), toggleMenu.bind(toggleMenu, $self.data('maxHeight')));

			// close menu on all clicks outside the toggle
			//$(document).on('click.desktop', clearMenu);

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
		console.log('revoke desktop nav');
		//$('.js-showmenu').off('.desktop'); // clears events in the .desktop namespace
		$(document).off('.desktop');
		$('.js-nav').each(function(){
			$(this).unbind().removeClass('ready').removeClass('changing').attr('style', '');
			$('li, ul', $(this)).unbind().attr('style', '');
			$('.menu', $(this)).attr('style', '');
			$('.submenu', $(this)).attr('style', '');
		})
	}
};
