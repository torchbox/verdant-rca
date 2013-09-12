$(function(){

	Harvey.attach('screen and (max-width:1023px)', {
		setup: function(){}, // called when the query becomes valid for the first time
		on: function(){
			$('nav').addClass('dl-menuwrapper').dlmenu({
				animationClasses : { 
					classin : 'dl-animate-in-2', 
					classout : 'dl-animate-out-2' 
				}
			});
		}, // called each time the query is activated
		off: function(){
			$('nav').removeClass('dl-menuwrapper').removeData();
			$('nav *').removeClass('dl-subview dl-subviewopen');
			$('nav .dl-back').remove();

		} // called each time the query is deactivated
	});
	Harvey.attach('screen and (min-width:1024px)', {
		setup: function(){}, // called when the query becomes valid for the first time
		on: function(){
			desktopNav.apply()
		}, // called each time the query is activated
		off: function(){
			desktopNav.revoke()
		} // called each time the query is deactivated
	});

});

var desktopNav = {
	apply: function(){
		$('.nav-wrapper nav:not(.dl-menuwrapper)').each(function(){
			// find tallest submenu
			var maxHeight = 0;
			$(this).find('ul').each(function(){
				maxHeight = ($(this).height() > maxHeight) ? $(this).height() : maxHeight
			})

			$(this).data('maxHeight', maxHeight);

			var selected = $(this).find('.selected').clone();
			selected.find('ul').remove();
			$(this).append($('<ul class="breadcrumb"></ul>').append(selected));
			$(this).addClass('ready')

			var $self = $(this);

			$self.hoverIntent({
				over: function(){
					$self.addClass('changing');
					setTimeout(function(){
						$self.removeClass('changing');
					}, 400)

					$self.find('.breadcrumb').stop().hide();

					$self.stop().animate({
						height: $self.data('maxHeight') + 16
					},200, function(){
						$self.removeClass('changing');
					})

					$self.find('.menu').stop().fadeIn(200, function(){
						//necessary to avoid some kind of weird race bug where opacity stops getting changed to 1
						$self.find('.menu').css({opacity:1,display:'block'})
						$self.removeClass('changing');
					});
				}, 
				out: function(){
					$self.addClass('changing');
				
					$self.find('.menu').stop().hide()

					$self.stop().animate({
						height: 34
					}, 200, function(){
						$self.find('.selected > ul').stop().show()
						$self.removeClass('changing');
					});

					$self.find('li:not(.selected) > ul').stop().fadeOut(100, function(){
						$(this).find('.selected > ul').fadeIn(100)
					});

					$self.find('.breadcrumb').stop().fadeIn(200, function(){
						$(this).removeClass('changing');
					})
				},
				timeout:400
			})	

			$('li', $self).hoverIntent({
				over: function(){
					$(this).siblings().find(' > ul').stop().hide()
					$(this).find(' > ul').fadeIn(200);
				},
				out: function(){
					if(!$('nav').hasClass('changing')){
						$(this).find('> ul').stop().hide();
					}
				},
				timeout: 300
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