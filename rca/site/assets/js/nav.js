
$(function(){

	Harvey.attach('screen and (min-width:600px)', {
		setup: function(){

		}, // called when the query becomes valid for the first time
		on: function(){
			applyNav()
		}, // called each time the query is activated
		off: function(){
			revokeNav()
		} // called each time the query is deactivated
	});
	Harvey.attach('screen and (max-width:599px)', {
		setup: function(){

		}, // called when the query becomes valid for the first time
		on: function(){
			$('nav li').each(function(){
				if($(this).children('ul.submenu').length){
					console.log($(this).find('a').html() + ' has children')
					console.log($(this).children('ul.submenu'))
					
					$(this).append('<div class="expand">+</div>')
				}
			})

			$('nav').addClass('dl-menuwrapper').dlmenu({
				animationClasses : { classin : 'dl-animate-in-2', classout : 'dl-animate-out-2' }
			});
		}, // called each time the query is activated
		off: function(){
			$('nav').removeClass('dl-menuwrapper');
		} // called each time the query is deactivated
	});
});

function revokeNav(){
	$('nav').each(function(){
		$(this).unbind().removeClass('ready').removeClass('changing').attr('style', '');
		$('li, ul', $(this)).unbind().attr('style', '');
		$('.breadcrumb', $(this)).remove()
		$('.menu', $(this)).attr('style', '');
		$('.submenu', $(this)).attr('style', '');
	})
}

function applyNav(){

	$('nav:not(.dl-menuwrapper)').each(function(){
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
					height: $self.data('maxHeight')
				},200, function(){
					$self.removeClass('changing');
				})

				$self.find('.menu').stop().fadeIn(300, function(){
					//necessary to avoid some kind of weird race bug where opacity stops getting changed to 1
					$self.find('.menu').css({opacity:1,display:'block'})
					$self.removeClass('changing');
				});
			}, 
			out: function(){
				$self.addClass('changing');
			
				$self.find('.menu').stop().hide()

				$self.stop().animate({
					height: 20
				}, 200, function(){
					$self.find('.selected > ul').stop().show()
					$self.removeClass('changing');
				});

				$self.find('li:not(.selected) > ul').stop().fadeOut(200, function(){
					$(this).find('.selected > ul').fadeIn(200)
				});

				$self.find('.breadcrumb').stop().fadeIn(function(){
					$this.removeClass('changing');
				})
			},
			timeout:200
		})	

		$('li', $self).hoverIntent({
			over: function(){
				$(this).siblings().find(' > ul').stop().hide()
				$(this).find(' > ul').fadeIn('slow');
			},
			out: function(){
				if(!$('nav').hasClass('changing')){
					$(this).find('> ul').stop().hide();
				}
			},
			timeout: 300
		});
	});
}