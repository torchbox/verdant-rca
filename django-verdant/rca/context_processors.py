from rca.models import Advert

def global_vars(request):
	return {
		'global_adverts': Advert.objects.filter(show_globally=True),
	}
