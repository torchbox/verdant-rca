$(function() {
	var currentSlide = 0;
	var slides = [];

	function setSlide(newSlide) {
		// If there are no slides, do nothing
		if (slides.length == 0) {
			return;
		}

		// Wrap slide id
		if (newSlide >= slides.length)
			newSlide = 0;

		// Switch to next slide
		currentSlide = newSlide;
		$("div#content").html(slides[currentSlide]);
	}

	function updateSlides() {
		// Perform ajax request
		$.getJSON("slides", function(newSlides) {
			// Get new slides
			slides = newSlides;

			// Go back to first slide
			setSlide(0);
		});
	}
	updateSlides();

	// Update slides every minute
	window.setInterval(updateSlides, 60000);

	// Rotate slides every 10 seconds
	window.setInterval(function() {
		// Go to next slide
		setSlide(currentSlide + 1)
	}, 10000);
});