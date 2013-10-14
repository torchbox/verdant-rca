from rca.models import Advert, SCHOOL_CHOICES, PROGRAMME_CHOICES, EVENT_LOCATION_CHOICES, AREA_CHOICES, EVENT_AUDIENCE_CHOICES

def global_vars(request):
	return {
		'global_adverts': Advert.objects.filter(show_globally=True),
		'global_schools': SCHOOL_CHOICES,
		'global_programmes': PROGRAMME_CHOICES,
		'global_locations': EVENT_LOCATION_CHOICES,
		'global_areas': AREA_CHOICES,
		'global_audiences': EVENT_AUDIENCE_CHOICES,
	}
