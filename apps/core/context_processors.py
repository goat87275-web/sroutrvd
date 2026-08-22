from django.conf import settings

def maps_settings(request):
    return {'MAPS_API_KEY': settings.MAPS_API_KEY}
