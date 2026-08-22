REQUIRED_DOCUMENT_CODES = ['IDENTITY', 'CV']
DEFAULT_DOCUMENT_TYPES = [
    ('IDENTITY', 'الهوية', True),
    ('CV', 'CV / السيرة الذاتية', True),
    ('EXPERIENCE_CERTIFICATE', 'شهادة خبرة', False),
    ('PROFESSIONAL_CERTIFICATE', 'شهادة مهنية', False),
    ('ACADEMIC_CERTIFICATE', 'شهادة أكاديمية', False),
    ('COMMERCIAL_REGISTRATION', 'سجل تجاري', False),
    ('OTHER', 'مستندات أخرى', False),
]

def is_provider_verified(user):
    if not user.is_authenticated or not user.is_provider():
        return False
    profile = getattr(user, 'provider_profile', None)
    return bool(profile and profile.status == 'active' and profile.verification_status == 'verified')

def get_provider_onboarding_status(profile):
    from apps.core.models import TermsAcceptance
    from apps.marketplace.models import ProviderService
    from apps.accounts.models import ProviderVerificationRequest
    profile_ok = all([
        profile.bio.strip(),
        profile.specializations.exists(),
        bool(profile.location_city_id),
        bool(profile.location_district_id),
    ])
    experience_ok = bool(profile.experience.strip() and profile.qualification_choices.exists() and profile.experience_years >= 0)
    location_ok = profile.latitude is not None and profile.longitude is not None
    uploaded_required = set(profile.documents.filter(status__in=['pending', 'approved'], document_type__is_required=True).values_list('document_type__code', flat=True))
    required = set(profile.documents.model._meta.get_field('document_type').related_model.objects.filter(is_active=True, is_required=True).values_list('code', flat=True))
    documents_ok = required.issubset(uploaded_required) if required else bool(profile.documents.exists())
    services_ok = ProviderVerificationRequest.objects.filter(provider=profile, requested_services__isnull=False).exists() or ProviderService.objects.filter(provider=profile, catalog_service__isnull=False).exists()
    terms_ok = TermsAcceptance.objects.filter(user=profile.user).exists()
    checklist = {
        'profile': profile_ok,
        'services': services_ok,
        'experience': experience_ok,
        'documents': documents_ok,
        'location': location_ok,
        'terms': terms_ok,
    }
    return checklist, all(checklist.values())
