from math import radians, sin, cos, asin, sqrt
from django.db.models import Q
from apps.accounts.models import User
from .models import Category, Service


def verified_provider_filter():
    return Q(role='provider', is_active=True, provider_profile__status='active', provider_profile__verification_status='verified')


def filter_public_providers(params):
    qs = User.objects.filter(verified_provider_filter()).select_related('provider_profile').prefetch_related('services')
    q = params.get('q')
    if q:
        qs = qs.filter(Q(username__icontains=q) | Q(first_name__icontains=q) | Q(last_name__icontains=q) | Q(provider_profile__business_name__icontains=q) | Q(provider_profile__display_name__icontains=q) | Q(provider_profile__specialization__icontains=q) | Q(services__title__icontains=q)).distinct()
    city = params.get('city')
    district = params.get('district')
    service = params.get('service')
    category = params.get('category')
    min_rating = params.get('min_rating')
    min_experience = params.get('min_experience')
    availability = params.get('availability')
    if city: qs = qs.filter(provider_profile__location_city_id=city) if str(city).isdigit() else qs.filter(provider_profile__city__icontains=city)
    if district: qs = qs.filter(provider_profile__location_district_id=district) if str(district).isdigit() else qs.filter(provider_profile__district__icontains=district)
    if service: qs = qs.filter(services__id=service)
    if category: qs = qs.filter(services__category_id=category)
    if min_rating: qs = qs.filter(provider_profile__average_rating__gte=min_rating)
    if min_experience: qs = qs.filter(provider_profile__experience_years__gte=min_experience)
    if availability == 'available': qs = qs.filter(provider_profile__is_available=True)
    lat = params.get('lat'); lng = params.get('lng'); radius = params.get('radius')
    if lat and lng and radius:
        # Small datasets: filter by bounding box in DB, annotate distance in Python only after DB narrowing.
        try:
            latf, lngf, radiusf = float(lat), float(lng), float(radius)
            delta = radiusf / 111.0
            qs = qs.filter(provider_profile__latitude__gte=latf-delta, provider_profile__latitude__lte=latf+delta, provider_profile__longitude__gte=lngf-delta, provider_profile__longitude__lte=lngf+delta)
            providers = list(qs)
            def distance(p):
                plat=float(p.provider_profile.latitude); plng=float(p.provider_profile.longitude)
                dlat=radians(plat-latf); dlng=radians(plng-lngf)
                a=sin(dlat/2)**2 + cos(radians(latf))*cos(radians(plat))*sin(dlng/2)**2
                return 6371*2*asin(sqrt(a))
            providers=[p for p in providers if distance(p) <= radiusf]
            providers.sort(key=distance)
            return providers
        except (TypeError, ValueError):
            pass
    return qs.order_by('-provider_profile__average_rating', '-provider_profile__completed_orders')


def filter_public_services(params):
    qs=Service.objects.filter(status='active', provider__provider_profile__status='active', provider__provider_profile__verification_status='verified').select_related('provider','provider__provider_profile','category')
    q=params.get('q')
    if q:
        qs=qs.filter(Q(title__icontains=q)|Q(description__icontains=q)|Q(provider__username__icontains=q)|Q(category__name__icontains=q))
    city=params.get('city'); district=params.get('district')
    if city: qs=qs.filter(provider__provider_profile__location_city_id=city) if str(city).isdigit() else qs.filter(provider__provider_profile__city__icontains=city)
    if district: qs=qs.filter(provider__provider_profile__location_district_id=district) if str(district).isdigit() else qs.filter(provider__provider_profile__district__icontains=district)
    return qs


def filter_public_categories(params):
    qs=Category.objects.filter(is_active=True)
    q=params.get('q')
    if q: qs=qs.filter(Q(name__icontains=q)|Q(description__icontains=q))
    return qs.order_by('order','name')
